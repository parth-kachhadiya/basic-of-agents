"""
travel_planner.py - Week 1, Day 6 mini-project: the Travel Planner without LangChain

Your Day 2 agent loop + 5 tools + a travel prompt that tells the agent to RE-PLAN
when a tool fails. After each plan it prints calls, tokens, cost and time.

Run (from the Day-6 folder):
  uv run python travel_planner.py                  default: Goa, 14 Nov, sold-out flights -> re-plan
  uv run python travel_planner.py tight            small budget -> only the cheapest hotel fits
  uv run python travel_planner.py impossible       budget too small -> the agent must say so honestly
  uv run python travel_planner.py manali           no airport -> the agent explains what is not covered
  uv run python travel_planner.py default flaky    the first hotel search fails with a 503 -> retry
  uv run python travel_planner.py "your own request"
"""
import json
import sys
import time

from agent import run_agent
from llm import LOG_FILE
from tools.travel_tools import TRAVEL_TOOLS, set_flaky

TRAVEL_PROMPT = """You are a travel planner for a traveller who starts from Surat, India.

Rules:
- Get real options from the tools. Never invent flights, hotels, prices or weather.
- All money is in Indian rupees (Rs.).
- Do every calculation with the calculator tool, not in your head.
- The budget must cover: flights both ways + hotel + Rs. 1,500 per day for food and activities
  (number of days = number of nights + 1).
- If a tool returns an error, READ it. Change the plan (another date, another hotel budget, another
  option), try again, and tell the user at the end what you changed and why.
- If the budget cannot work, say so clearly and show the cheapest plan you found instead of pretending.
- If part of the trip is not covered by your tools (for example, a train or road journey), say clearly
  what is missing. Do not make it up.
- Final answer: a short day-by-day plan and a cost table. At most 250 words."""

PRESETS = {
    "default": "Plan a 3-night trip from Surat to Goa starting 14 Nov 2026. Total budget Rs. 40,000. "
               "I like beaches and good food.",
    "tight": "Plan a 3-night trip from Surat to Goa starting 14 Nov 2026. Total budget Rs. 22,000. "
             "I like beaches and good food.",
    "impossible": "Plan a 3-night trip from Surat to Goa starting 14 Nov 2026. Total budget Rs. 9,000.",
    "manali": "Plan a 2-night trip from Surat to Manali starting 20 Nov 2026. Total budget Rs. 35,000. "
              "I like nature and cafes.",
}


def _log_lines() -> list[str]:
    try:
        with open(LOG_FILE, encoding="utf-8") as f:
            return f.readlines()
    except FileNotFoundError:
        return []


def plan_trip(request: str) -> str:
    before = len(_log_lines())
    start = time.perf_counter()

    answer = run_agent(request, TRAVEL_TOOLS, max_steps=14, system_prompt=TRAVEL_PROMPT)

    seconds = time.perf_counter() - start
    new = [json.loads(l) for l in _log_lines()[before:] if l.strip()]
    cost = sum(float(r["cost_usd"]) for r in new)
    print("\n" + "=" * 60)
    print("FINAL PLAN\n" + "=" * 60)
    print(answer)
    print("\n" + "-" * 60)
    print(f"LLM calls {len(new)} | tokens {sum(r['input_tokens'] for r in new)} in + "
          f"{sum(r['output_tokens'] for r in new)} out | cost ${cost:.6f} | time {seconds:.1f}s")
    return answer


if __name__ == "__main__":
    args = sys.argv[1:]
    flaky = "flaky" in args
    args = [a for a in args if a != "flaky"]
    set_flaky(flaky)

    if not args:
        request = PRESETS["default"]
    elif args[0] in PRESETS:
        request = PRESETS[args[0]]
    else:
        request = " ".join(args)

    print(f"REQUEST: {request}" + ("   [flaky hotel service ON]" if flaky else ""))
    plan_trip(request)