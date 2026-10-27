import json
from llm import llm
from tools_v1 import TOOLS_V1
from tools_v2 import TOOLS_V2



CORRECT_V2 = {
    "get_order": {"get_order"},
    "list_orders": {"search_orders"},
    "cancel": {"cancel_order"},
    "change_address": {"update_shipping_address"},
    "needs_lookup": {"search_orders"},
}

CORRECT_V1 = {
    "get_order": {"get_data"},              # needs full fields; search gives IDs only
    "list_orders": {"get_data", "search"},  # either finds orders by name/email
    "cancel": {"update"},
    "change_address": {"update"},
}

def first_tool(prompt, tools):
    r = llm([{'role' : 'user', 'content' : prompt}], tools = tools)
    calls = r.choices[0].message.tool_calls
    return calls[0].function.name if calls else None


def run(tools, correct):
    rows = [json.loads(line) for line in open("prompts.jsonl")]
    hits, misses = 0, []

    for row in rows:
        got = first_tool(row['prompt'], tools)
        if got in correct[row['intent']]:
            hits += 1
        else:
            misses.append((row['prompt'], row['intent'], got))

    print(f"{hits}/{len(rows)} = {hits/len(rows):.0%}")

    for m in misses:
        print(m)
    
    return hits / len(rows)


if __name__ == "__main__":
    print("--- v1 ---")
    run(TOOLS_V1, CORRECT_V1)
    print("--- v2 ---")
    run(TOOLS_V2, CORRECT_V2)