"""
streaming.py - Week 1, Day 3

> `Day - 3` has 3 jobs..**

1. Make the model return data in `fixed shape` and check it with `Pydantic`. if the check fails, retry once and send the error back.
2. Build an `extractor` (Messy text to a clean object) and score it on 10 inputs.
3. `Stream` the answer on token by token, and see how tool call arrive in a stream. 

stream_chat(): like llm(), but the answer arrives token by token.
Two demos:
  text   -> watch plain text stream into the terminal
  tools  -> watch tool-call fragments arrive and get assembled

Run:  python streaming.py          (both demos)
      python streaming.py text
      python streaming.py tools
"""
import json
import os
import sys
import time

from llm import LOG_FILE, MODEL, PRICES, client
from tools import TOOLS


def _log_call(model, usage, latency, ttft, finish_reason):
    """Same log format as llm(), plus ttft_s (time to first token)."""
    in_tok = usage.prompt_tokens if usage else 0
    out_tok = usage.completion_tokens if usage else 0
    price_in, price_out = PRICES.get(model, (0, 0))
    cost = (in_tok * price_in + out_tok * price_out) / 1_000_000

    record = {
        "model": model,
        "input_tokens": in_tok,
        "output_tokens": out_tok,
        "latency_s": round(latency, 2),
        "cost_usd": f"{cost:.6f}",
        "finish_reason": finish_reason,
        "ttft_s": round(ttft, 2) if ttft is not None else None,
    }
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")


def stream_chat(messages, tools=None, model=MODEL, max_tokens=1000, show_raw=False):
    """
    Stream one model call. Prints text as it arrives.
    Returns {"content": str, "tool_calls": [...], "finish_reason": str}.
    tool_calls has the same shape agent.py puts in the assistant message.
    """
    kwargs = {
        "model": model,
        "messages": messages,
        "max_tokens": max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},  # ask for token counts in the last chunk
    }
    if tools:
        kwargs["tools"] = tools

    start = time.perf_counter()
    ttft = None            # time to first token
    text_parts = []
    calls = {}             # tool-call index -> {"id", "name", "arguments"}
    finish_reason = None
    usage = None
    n_chunks = 0

    for chunk in client.chat.completions.create(**kwargs):
        n_chunks += 1

        if getattr(chunk, "usage", None):   # only the very last chunk carries usage
            usage = chunk.usage
        if not chunk.choices:               # that last chunk has no choices
            continue

        choice = chunk.choices[0]
        delta = choice.delta
        if choice.finish_reason:
            finish_reason = choice.finish_reason

        # --- plain text pieces ---
        if delta.content:
            if ttft is None:
                ttft = time.perf_counter() - start
            text_parts.append(delta.content)
            print(delta.content, end="", flush=True)

        # --- tool-call pieces: they arrive in FRAGMENTS, joined by index ---
        for tc in delta.tool_calls or []:
            if ttft is None:
                ttft = time.perf_counter() - start
            slot = calls.setdefault(tc.index, {"id": None, "name": "", "arguments": ""})
            if tc.id:
                slot["id"] = tc.id
            if tc.function and tc.function.name and not slot["name"]:
                slot["name"] = tc.function.name
            if tc.function and tc.function.arguments:
                slot["arguments"] += tc.function.arguments

            if show_raw:
                fn = tc.function
                print(f"  chunk {n_chunks:>3} | index {tc.index} | id={tc.id} | "
                      f"name={fn.name if fn else None} | args+={(fn.arguments if fn else None)!r}")

    latency = time.perf_counter() - start
    if text_parts:
        print()  # finish the line after streamed text

    _log_call(model, usage, latency, ttft, finish_reason)
    out_tok = usage.completion_tokens if usage else "?"
    print(f"[stream] first token {ttft if ttft is None else round(ttft, 2)}s | "
          f"total {latency:.2f}s | chunks {n_chunks} | output tokens {out_tok}")

    return {
        "content": "".join(text_parts),
        "tool_calls": [
            {"id": c["id"], "type": "function",
             "function": {"name": c["name"], "arguments": c["arguments"]}}
            for _, c in sorted(calls.items())
        ],
        "finish_reason": finish_reason,
    }


def demo_text():
    print("\n=== DEMO 1: streaming text ===\n")
    stream_chat([{"role": "user",
                  "content": "In 3 short sentences, explain why streaming makes chatbots feel faster."}])


def demo_tools():
    print("\n=== DEMO 2: streaming tool calls (watch the fragments) ===\n")
    schemas = [t["schema"] for t in TOOLS.values()]
    result = stream_chat(
        [{"role": "user", "content": "What's the weather in Surat and in Mumbai?"}],
        tools=schemas,
        show_raw=True,
    )

    print("\n--- assembled tool calls ---")
    for tc in result["tool_calls"]:
        args = json.loads(tc["function"]["arguments"])  # only safe AFTER the stream ends
        print(f"{tc['function']['name']}({args})   id={tc['id']}")
    print("finish_reason:", result["finish_reason"])


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    if which in ("text", "both"):
        demo_text()
    if which in ("tools", "both"):
        demo_tools()