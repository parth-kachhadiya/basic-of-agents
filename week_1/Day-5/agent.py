"""
agent.py - Week 1, Day 5

run_agent(task, tools, max_steps): the agent loop.
Run:  uv run python agent.py
"""
import json
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeout

from llm import llm
from tools import TOOLS

SYSTEM_PROMPT = (
    "You are a helpful assistant. Use tools when you need real data or exact math. "
    "If a tool returns an error, read it and try to fix the problem or explain it to the user."
)

MAX_TOOL_OUTPUT = 4000  # characters; stops a huge tool result from flooding the context


# ---------------------------------------------------------------
# Run ONE tool call safely. It never raises: every problem becomes
# an error string that goes back to the model so it can recover.
# ---------------------------------------------------------------
def run_one_tool(tc, tools) -> str:
    name = tc.function.name

    # Failure 1: the model asked for a tool that does not exist
    if name not in tools:
        return f"Error: unknown tool '{name}'. Available tools: {list(tools)}"

    # Failure 2: the arguments are not valid JSON
    try:
        args = json.loads(tc.function.arguments or "{}")
    except json.JSONDecodeError as e:
        return f"Error: arguments for '{name}' were not valid JSON ({e})"

    try:
        result = tools[name]["fn"](**args)
    except TypeError as e:  # Failure 3: wrong or missing argument names
        return f"Error: bad arguments for '{name}': {e}"
    except Exception as e:  # Failure 4: the tool itself crashed
        return f"Error: tool '{name}' failed: {type(e).__name__}: {e}"

    text = json.dumps(result, ensure_ascii=False, default=str)
    return text[:MAX_TOOL_OUTPUT]


# ---------------------------------------------------------------
# The agent loop
# ---------------------------------------------------------------
def run_agent(task: str, tools: dict, max_steps: int = 8, tool_timeout: int = 20) -> str:
    schemas = [t["schema"] for t in tools.values()]
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": task},
    ]

    pool = ThreadPoolExecutor(max_workers=8)
    try:
        for step in range(1, max_steps + 1):
            print(f"\n--- step {step} ---")
            resp = llm(messages, tools=schemas)
            msg = resp.choices[0].message

            # No tool requested -> the model is finished
            if not msg.tool_calls:
                return msg.content

            # Save the model's tool request in the history
            messages.append({
                "role": "assistant",
                "content": msg.content,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {"name": tc.function.name, "arguments": tc.function.arguments},
                    }
                    for tc in msg.tool_calls
                ],
            })

            # Start ALL requested tools at the same time (parallel)
            futures = []
            for tc in msg.tool_calls:
                print(f"model wants: {tc.function.name}({tc.function.arguments})")
                futures.append((tc, pool.submit(run_one_tool, tc, tools)))

            # Collect results; a slow tool becomes a timeout error, not a freeze
            for tc, fut in futures:
                try:
                    result = fut.result(timeout=tool_timeout)
                except FutureTimeout:
                    result = f"Error: tool '{tc.function.name}' timed out after {tool_timeout}s"
                print(f"  -> {result[:150]}")
                messages.append({"role": "tool", "tool_call_id": tc.id, "content": result})

        # Hard stop: the loop ran out of steps
        return f"Stopped: reached max_steps={max_steps} without a final answer."
    finally:
        pool.shutdown(wait=False)


if __name__ == "__main__":
    tasks = [
        # 1 tool
        "What is 1234 * 5678?",
        # 2 weather calls in parallel, then calculator
        "Compare the current weather in Surat and Mumbai, and tell me the temperature difference.",
        # error recovery: this city does not exist
        "What's the weather in Xyzzyville?",
        # search_files tool (needs files inside ./notes)
        "Search my notes for 'Surat' and tell me what you find.",
        # search_files + weather together
        "Search my notes for 'Surat', then tell me the current weather there.",
    ]
    for t in tasks:
        print("\n" + "=" * 60)
        print("TASK:", t)
        answer = run_agent(t, TOOLS)
        print("\nFINAL ANSWER:", answer)