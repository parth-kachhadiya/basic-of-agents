"""
orchestrator.py - Week 1, Day 5, Pattern 4: orchestrator-workers

  1. PLANNER  (1 call)  reads the request and DECIDES 3-5 subtasks at runtime
  2. GATE     plain Python checks the plan; one retry if it is broken
  3. WORKERS  (3-5 calls, all at once) each does ONE subtask
  4. MERGER   (1 call)  combines the finished parts into one document

The difference from Day 4 sectioning: there, YOUR CODE split the document.
Here, the MODEL decides how to split the job.

Run:  uv run python orchestrator.py
      uv run python orchestrator.py "your own request here"
"""
import asyncio
import json
import sys
import time

from llm_async import allm

DEFAULT_REQUEST = ("Prepare a launch kit for the Surat Silks Diwali sale: 20% off all Banarasi sarees "
                   "from 28 Oct to 3 Nov 2026, free delivery above Rs. 5,000.")

PLANNER_PROMPT = (
    "You are the planner for a small online saree shop called Surat Silks. A manager gives you a request. "
    "Split it into 3 to 5 subtasks that different specialists can do independently, at the same time. "
    "You decide the subtasks yourself, based on the request.\n\n"
    "Return ONE JSON object only, no markdown, in exactly this shape:\n"
    '{"subtasks": [{"name": "short name", "brief": "instructions for the specialist"}]}\n\n'
    "Every brief must say: (1) exactly what to write, (2) the maximum length in words, "
    "(3) one thing the specialist must NOT do. A specialist sees only its own brief and the original "
    "request, so never refer to other subtasks."
)

WORKER_PROMPT = (
    "You are a specialist working on ONE part of a bigger job for the online saree shop Surat Silks. "
    "Do only the subtask you are given. Use only the facts in the overall request: never invent prices, "
    "dates, discounts or product names. Obey the length limit in your instructions."
)


def _text(resp) -> str:
    return (resp.choices[0].message.content or "").strip()


def strip_fences(raw: str) -> str:
    """Models sometimes wrap JSON in ```json ... ``` even when told not to."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").strip()
        if raw.lower().startswith("json"):
            raw = raw[4:]
    return raw.strip()


# ---------------------------------------------------------------
# The gate for the plan (plain Python)
# ---------------------------------------------------------------
def parse_plan(raw: str):
    """Return (subtasks, problems). Empty problems = the plan may go to the workers."""
    try:
        data = json.loads(strip_fences(raw))
    except json.JSONDecodeError as e:
        return None, [f"the reply was not valid JSON ({e})"]

    subs = data.get("subtasks") if isinstance(data, dict) else None
    if not isinstance(subs, list):
        return None, ['the top-level key "subtasks" (a list) is missing']

    problems, clean = [], []
    if not 3 <= len(subs) <= 5:
        problems.append(f"need 3 to 5 subtasks but got {len(subs)}")
    for i, s in enumerate(subs, 1):
        if isinstance(s, dict) and str(s.get("name", "")).strip() and str(s.get("brief", "")).strip():
            clean.append({"name": str(s["name"]).strip(), "brief": str(s["brief"]).strip()})
        else:
            problems.append(f"subtask {i} needs a non-empty 'name' and 'brief'")
    return clean, problems


# ---------------------------------------------------------------
# Step 1 + 2: the planner and its gate
# ---------------------------------------------------------------
async def make_plan(request: str, max_retries: int = 1) -> list[dict]:
    messages = [{"role": "system", "content": PLANNER_PROMPT},
                {"role": "user", "content": request}]

    for attempt in range(max_retries + 1):
        raw = _text(await allm(messages, max_tokens=700))
        subtasks, problems = parse_plan(raw)
        print(f"[plan] attempt {attempt}: {'PASS' if not problems else 'FAIL: ' + '; '.join(problems)}")
        if not problems:
            return subtasks

        messages.append({"role": "assistant", "content": raw})
        messages.append({"role": "user",
                         "content": "Your plan was rejected: " + "; ".join(problems) +
                                    ". Return the corrected JSON only."})

    raise RuntimeError(f"The planner could not produce a valid plan: {'; '.join(problems)}")


# ---------------------------------------------------------------
# Step 3: one worker
# ---------------------------------------------------------------
async def run_worker(sub: dict, request: str, sem: asyncio.Semaphore) -> str:
    async with sem:  # at most 5 workers talk to the model at the same moment
        resp = await allm(
            [{"role": "system", "content": WORKER_PROMPT},
             {"role": "user", "content": f"Overall request: {request}\n\n"
                                         f"Your subtask: {sub['name']}\nInstructions: {sub['brief']}"}],
            max_tokens=400,
        )
    return _text(resp)


# ---------------------------------------------------------------
# Step 4: the merger
# ---------------------------------------------------------------
async def merge(request: str, finished: list[tuple[str, str]]) -> str:
    sections = "\n\n".join(f"## {name}\n{text}" for name, text in finished)
    resp = await allm(
        [{"role": "user", "content":
            f"Overall request: {request}\n\nBelow are parts written by different specialists. "
            "Combine them into ONE launch kit with a one-line intro. Keep every fact exactly as given, "
            "add no new facts, and remove repetition.\n\n" + sections}],
        max_tokens=900,
    )
    return _text(resp)


# ---------------------------------------------------------------
# The whole run
# ---------------------------------------------------------------
async def orchestrate(request: str) -> str:
    print(f"REQUEST: {request}\n")
    subtasks = await make_plan(request)

    print("\nThe planner decided on these subtasks:")
    for i, s in enumerate(subtasks, 1):
        print(f"  {i}. {s['name']}\n     brief: {s['brief']}")

    sem = asyncio.Semaphore(5)
    t0 = time.perf_counter()
    # return_exceptions=True: if one worker crashes, the others still finish
    results = await asyncio.gather(*(run_worker(s, request, sem) for s in subtasks),
                                   return_exceptions=True)
    print(f"\nAll {len(subtasks)} workers finished in {time.perf_counter() - t0:.1f}s (in parallel)")

    finished = []
    for sub, result in zip(subtasks, results):
        if isinstance(result, Exception):
            print(f"\n[worker FAILED] {sub['name']}: {type(result).__name__}: {result}")
        else:
            finished.append((sub["name"], result))
            print(f"\n--- {sub['name']} ({len(result.split())} words) ---\n{result}")

    if not finished:
        raise RuntimeError("Every worker failed, so there is nothing to merge.")

    kit = await merge(request, finished)
    if len(finished) < len(subtasks):
        kit += f"\n\n[NOTE: {len(subtasks) - len(finished)} part(s) are missing because a worker failed.]"

    print("\n" + "=" * 60 + "\nFINAL LAUNCH KIT\n" + "=" * 60 + "\n" + kit)
    return kit


if __name__ == "__main__":
    request = " ".join(sys.argv[1:]) or DEFAULT_REQUEST
    # ONE asyncio.run for the whole program (the lesson from the Day 4 bug)
    asyncio.run(orchestrate(request))