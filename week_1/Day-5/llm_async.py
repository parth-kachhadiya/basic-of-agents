"""
llm_async.py - Week 1, Day 4

allm(): the async twin of llm(). Many calls can wait for the model at the same
time. It writes the same log lines to logs/calls.jsonl, so cost_report.py
keeps working.
"""
import json
import os
import time

from openai import AsyncOpenAI

from llm import LOG_FILE, MODEL, PRICES  # importing llm also loads your .env file

aclient = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)


async def allm(messages, model=MODEL, max_tokens=300, temperature=None):
    kwargs = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if temperature is not None:  # voting needs some randomness, otherwise 3 votes are the same vote
        kwargs["temperature"] = temperature

    start = time.perf_counter()
    resp = await aclient.chat.completions.create(**kwargs)
    latency = time.perf_counter() - start

    usage = resp.usage
    price_in, price_out = PRICES.get(model, (0, 0))
    cost = (usage.prompt_tokens * price_in + usage.completion_tokens * price_out) / 1_000_000

    record = {
        "model": model,
        "input_tokens": usage.prompt_tokens,
        "output_tokens": usage.completion_tokens,
        "latency_s": round(latency, 2),
        "cost_usd": f"{cost:.6f}",
        "finish_reason": resp.choices[0].finish_reason,
    }
    # This runs in the single event-loop thread, so two log lines can never be mixed together.
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")

    return resp