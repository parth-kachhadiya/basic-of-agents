"""
llm.py - Week 1, Day 1

Part 1: llm()        -> wrapper that logs every LLM call to calls.jsonl
Part 2: get_weather  -> a fake tool the model can ask us to run
Part 3: main()       -> one full tool-call round trip

Run:  uv run python llm.py
"""
import json
import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.environ["OPENROUTER_API_KEY"],
)

LOG_FILE = "logs/calls.jsonl"

# USD per 1 million tokens: (input price, output price)
# Check the real price on the model's OpenRouter page and update this.
PRICES = {
    "openai/gpt-4o-mini": (0.15, 0.60),
}

MODEL = "openai/gpt-4o-mini"


# ---------------------------------------------------------------
# PART 1: the logging wrapper (reused for all 12 weeks)
# ---------------------------------------------------------------
def llm(messages, model=MODEL, tools=None, max_tokens=1000):
    """Call the model, log model/tokens/latency/cost to calls.jsonl, return the response."""
    kwargs = {"model": model, "messages": messages, "max_tokens": max_tokens}
    if tools:
        kwargs["tools"] = tools

    start = time.perf_counter()
    resp = client.chat.completions.create(**kwargs)
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
    os.makedirs(os.path.dirname(LOG_FILE), exist_ok=True)
    with open(LOG_FILE, "a") as f:
        f.write(json.dumps(record) + "\n")

    return resp


# ---------------------------------------------------------------
# PART 2: the tool
# ---------------------------------------------------------------
def get_weather(city: str) -> dict:
    """Fake weather function. The model never runs this, our code does."""
    return {"city": city, "temp_c": 31, "condition": "sunny"}


# This is the description the model sees. It does NOT see the Python function.
TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_weather",
            "description": "Get the current weather for a city.",
            "parameters": {
                "type": "object",
                "properties": {
                    "city": {"type": "string", "description": "City name, e.g. Surat"}
                },
                "required": ["city"],
            },
        },
    }
]

# Maps the tool name the model asks for -> the real Python function
TOOL_FUNCTIONS = {"get_weather": get_weather}


# ---------------------------------------------------------------
# PART 3: one full tool-call round trip
# ---------------------------------------------------------------
def main():
    messages = [{"role": "user", "content": "What's the weather in Surat?"}]

    # Call 1: the model decides whether it needs a tool
    r1 = llm(messages, tools=TOOLS)
    print("=== RAW RESPONSE 1 (label every field in LEARNINGS.md) ===")
    print(r1.model_dump_json(indent=2))

    msg = r1.choices[0].message

    if not msg.tool_calls:
        print("\nModel answered directly, no tool used:")
        print(msg.content)
        return

    # Put the model's tool request into the history
    messages.append(
        {
            "role": "assistant",
            "content": msg.content,
            "tool_calls": [
                {
                    "id": tc.id,
                    "type": "function",
                    "function": {
                        "name": tc.function.name,
                        "arguments": tc.function.arguments,
                    },
                }
                for tc in msg.tool_calls
            ],
        }
    )

    # Run each requested tool and send the result back
    for tc in msg.tool_calls:
        args = json.loads(tc.function.arguments)  # arguments arrive as a JSON *string*
        print(f"\nModel wants: {tc.function.name}({args})")

        result = TOOL_FUNCTIONS[tc.function.name](**args)

        messages.append(
            {
                "role": "tool",
                "tool_call_id": tc.id,  # must match the id of the request
                "content": json.dumps(result),
            }
        )

    # Call 2: the model reads the tool result and writes the final answer
    r2 = llm(messages, tools=TOOLS)
    print("\n=== FINAL ANSWER ===")
    print(r2.choices[0].message.content)
