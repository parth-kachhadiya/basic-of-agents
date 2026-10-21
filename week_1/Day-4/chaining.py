"""
chaining.py - Week 1, Day 4, Pattern 1: prompt chaining with a gate

Headache 1: “I want the announcement written well, every time”
• The problem: you ask the AI “write an announcement for our Diwali collection” in one go. 
  Sometimes it’s great. Sometimes it rambles, or has no structure, or is far too long.

  step 1: LLM writes an outline
  step 2: GATE = plain Python checks the outline (no LLM involved)
          fail -> one retry that tells the model exactly what broke
          fail again -> STOP, no draft is written
  step 3: LLM writes the draft from the approved outline

Run:  uv run python chaining.py            (normal)
      uv run python chaining.py strict     (gate demands 7-8 points, so you see it fail and retry)
"""
import re
import sys

from llm import llm


class GateError(Exception):
    """The outline still broke the rules after the retry."""


def _text(resp) -> str:
    return (resp.choices[0].message.content or "").strip()


# ---------------------------------------------------------------
# The gate: plain Python, no model
# ---------------------------------------------------------------
def parse_points(raw: str) -> list[str]:
    """Pull bullet lines ('- x', '* x', '1. x') out of the model's text."""
    points = []
    for line in raw.splitlines():
        m = re.match(r"^\s*(?:[-*\u2022]|\d+[.)])\s+(.*\S)\s*$", line)
        if m:
            points.append(m.group(1))
    return points


def gate(points, min_points, max_points, max_words) -> list[str]:
    """Return a list of problems. Empty list = the outline may go to step 3."""
    problems = []
    if not (min_points <= len(points) <= max_points):
        problems.append(f"expected {min_points}-{max_points} bullet points but got {len(points)}")
    for i, p in enumerate(points, 1):
        n = len(p.split())
        if n > max_words:
            problems.append(f"point {i} has {n} words (maximum {max_words})")
    if len({p.lower() for p in points}) < len(points):
        problems.append("two points are identical")
    return problems


# ---------------------------------------------------------------
# Step 1 + 2: outline, then gate (with one retry)
# ---------------------------------------------------------------
def build_outline(topic, min_points, max_points, max_words, max_retries=1) -> list[str]:
    messages = [{
        "role": "user",
        "content": (f"Topic: {topic}\n\n"
                    "Write an outline for a short shop announcement.\n"
                    f"Rules: 3 to 5 bullet points, each at most {max_words} words, "
                    "each line starting with '- '. Output only the bullets."),
    }]

    for attempt in range(max_retries + 1):
        raw = _text(llm(messages, max_tokens=300))
        points = parse_points(raw)
        problems = gate(points, min_points, max_points, max_words)

        print(f"[gate] attempt {attempt}: {len(points)} points -> "
              f"{'PASS' if not problems else 'FAIL: ' + '; '.join(problems)}")
        if not problems:
            return points

        # Same idea as Day 3: show the model its own answer and exactly what was wrong
        messages.append({"role": "assistant", "content": raw})
        messages.append({"role": "user",
                         "content": "Your outline broke these rules: " + "; ".join(problems) +
                                    ". Rewrite it so every rule is met. Output only the bullets."})

    raise GateError(f"Outline still broke the rules after {max_retries} retry: {'; '.join(problems)}")


# ---------------------------------------------------------------
# The whole chain
# ---------------------------------------------------------------
def write_announcement(topic, min_points=3, max_points=5, max_words=12) -> str:
    print(f"TOPIC: {topic}\n")
    print("[step 1+2] outline and gate")
    points = build_outline(topic, min_points, max_points, max_words)
    for p in points:
        print(f"   - {p}")

    print("\n[step 3] draft")
    outline_text = "\n".join(f"- {p}" for p in points)
    draft = _text(llm([{
        "role": "user",
        "content": ("Write a friendly shop announcement of at most 80 words. "
                    f"Cover every point of this outline, in order:\n{outline_text}\n\nTopic: {topic}"),
    }], max_tokens=250))
    print(draft)
    print(f"\n({len(draft.split())} words)")
    return draft


if __name__ == "__main__":
    topic = "new Banarasi saree collection at Surat Silks, launching this Diwali"
    mode = sys.argv[1] if len(sys.argv) > 1 else "normal"
    try:
        if mode == "strict":
            write_announcement(topic, min_points=7, max_points=8)
        else:
            write_announcement(topic)
    except GateError as e:
        print(f"\n[stop] the gate refused the outline, so no draft was written.\n       {e}")