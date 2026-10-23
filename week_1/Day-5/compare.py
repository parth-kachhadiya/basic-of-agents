"""
compare.py - Week 1, Day 5: a fixed WORKFLOW vs your Day 2 AGENT on the SAME task

Task: "Add up my monthly expenses and tell me what percentage is rent."
Both approaches are run N times. Quality, LLM calls, tokens, cost and latency
are measured from logs/calls.jsonl (new lines added during each run).

  WORKFLOW: your code decides the steps (search -> AI extracts -> code does the math -> AI writes)
  AGENT   : the model decides the steps (your run_agent loop from Day 2)

Run:  uv run python compare.py        (3 runs of each)
      uv run python compare.py 5      (5 runs of each)
"""
import contextlib
import io
import json
import re
import statistics
import sys
import time
from pathlib import Path

from agent import run_agent
from llm import LOG_FILE, llm
from tools import TOOLS, search_files

TASK = ("Look in my notes for my monthly expenses, add them all up, and tell me the total "
        "and what percentage of the total is rent.")

NOTES_FILE = Path("notes/expenses.txt")
DEFAULT_NOTES = ("Expense: Rent = 12000\nExpense: Food = 6500\n"
                 "Expense: Travel = 3200\nExpense: Utilities = 1800\n")

EXTRACT_PROMPT = ('Extract every expense from the lines below. Reply with JSON only, in this shape: '
                  '{"expenses": [{"name": "Rent", "amount": 12000}]}. Amounts are plain numbers.\n\nLines:\n')


def _text(resp) -> str:
    return (resp.choices[0].message.content or "").strip()


def strip_fences(raw: str) -> str:
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").strip()
        if raw.lower().startswith("json"):
            raw = raw[4:]
    return raw.strip()


# ---------------------------------------------------------------
# The truth, computed from the file, so we can mark answers right or wrong
# ---------------------------------------------------------------
def ground_truth() -> tuple[float, float]:
    items = {}
    for line in NOTES_FILE.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*Expense:\s*(.+?)\s*=\s*([\d,\.]+)", line)
        if m:
            items[m.group(1).strip().lower()] = float(m.group(2).replace(",", ""))
    total = sum(items.values())
    return total, items.get("rent", 0) / total * 100


def is_correct(answer: str, total: float, pct: float) -> bool:
    """Plain-Python check: does the answer contain the right total AND the right percentage?"""
    numbers = []
    for token in re.findall(r"\d[\d,]*\.?\d*", answer):
        try:
            numbers.append(float(token.replace(",", "").rstrip(".")))
        except ValueError:
            pass
    return any(abs(n - total) < 1 for n in numbers) and any(abs(n - pct) <= 0.15 for n in numbers)


# ---------------------------------------------------------------
# Approach 1: the fixed workflow (YOUR code decides every step)
# ---------------------------------------------------------------
def run_workflow() -> str:
    # step 1: plain code searches the notes
    matches = search_files("Expense")["matches"]
    lines = "\n".join(m["text"] for m in matches)

    # step 2: the AI turns messy lines into data
    data = json.loads(strip_fences(_text(llm([{"role": "user", "content": EXTRACT_PROMPT + lines}],
                                             max_tokens=300))))
    expenses = data["expenses"]

    # step 3: plain code does the math (exact, free)
    total = sum(e["amount"] for e in expenses)
    rent = sum(e["amount"] for e in expenses if e["name"].strip().lower() == "rent")
    pct = rent / total * 100

    # step 4: the AI writes the answer from numbers that are already correct
    return _text(llm([{"role": "user", "content":
                       f"Write a two-sentence answer for the user. Total monthly expenses: {total:.0f}. "
                       f"Rent is {pct:.2f}% of the total."}], max_tokens=120))


# ---------------------------------------------------------------
# Approach 2: the agent (the MODEL decides the steps)
# ---------------------------------------------------------------
def run_agent_version() -> str:
    with contextlib.redirect_stdout(io.StringIO()):  # hide the step-by-step prints, we only want numbers
        return run_agent(TASK, TOOLS)


# ---------------------------------------------------------------
# The scorekeeper: read only the log lines added during one run
# ---------------------------------------------------------------
def _log_lines() -> list[str]:
    try:
        with open(LOG_FILE, encoding="utf-8") as f:
            return f.readlines()
    except FileNotFoundError:
        return []


def measure(fn, total, pct) -> dict:
    before = len(_log_lines())
    start = time.perf_counter()
    try:
        answer, error = fn(), None
    except Exception as e:  # a crashed run counts as a failed run, it must not stop the comparison
        answer, error = "", f"{type(e).__name__}: {e}"
    seconds = time.perf_counter() - start

    new = [json.loads(l) for l in _log_lines()[before:] if l.strip()]
    return {
        "correct": error is None and is_correct(answer, total, pct),
        "calls": len(new),
        "tokens_in": sum(r["input_tokens"] for r in new),
        "tokens_out": sum(r["output_tokens"] for r in new),
        "cost": sum(float(r["cost_usd"]) for r in new),
        "seconds": seconds,
        "answer": answer,
        "error": error,
    }


def summarize(name: str, runs: list[dict]):
    # A crashed run has 0 calls and 0 cost; averaging it in would make that approach look cheaper
    # than it is. So averages use only the runs that finished, and crashes are counted separately.
    done = [r for r in runs if not r["error"]]
    crashed = len(runs) - len(done)
    if not done:
        print(f"{name:<10} every run crashed ({crashed}/{len(runs)})")
        return
    print(f"{name:<10} correct {sum(r['correct'] for r in runs)}/{len(runs)} | crashed {crashed} | "
          f"LLM calls {statistics.mean(r['calls'] for r in done):.1f} | "
          f"tokens in {statistics.mean(r['tokens_in'] for r in done):.0f} | "
          f"tokens out {statistics.mean(r['tokens_out'] for r in done):.0f} | "
          f"cost ${statistics.mean(r['cost'] for r in done):.6f} | "
          f"time {statistics.mean(r['seconds'] for r in done):.1f}s")


if __name__ == "__main__":
    n_runs = int(sys.argv[1]) if len(sys.argv) > 1 else 3

    NOTES_FILE.parent.mkdir(exist_ok=True)
    if not NOTES_FILE.exists():
        NOTES_FILE.write_text(DEFAULT_NOTES, encoding="utf-8")
    total, pct = ground_truth()
    print(f"TASK: {TASK}\nTRUTH (from the file): total {total:.0f}, rent {pct:.2f}%\n")

    results = {"workflow": [], "agent": []}
    for i in range(1, n_runs + 1):
        for name, fn in (("workflow", run_workflow), ("agent", run_agent_version)):
            r = measure(fn, total, pct)
            results[name].append(r)
            status = "correct" if r["correct"] else ("CRASHED" if r["error"] else "WRONG")
            print(f"run {i} {name:<9}: {status:<7} | calls {r['calls']} | "
                  f"tokens {r['tokens_in']}+{r['tokens_out']} | ${r['cost']:.6f} | {r['seconds']:.1f}s")
            if r["error"]:
                print(f"            error: {r['error']}")

    print("\n" + "=" * 100 + "\nAVERAGES\n" + "=" * 100)
    summarize("workflow", results["workflow"])
    summarize("agent", results["agent"])

    print("\nFirst answer from each:")
    print(f"  workflow: {results['workflow'][0]['answer']}")
    print(f"  agent   : {results['agent'][0]['answer']}")