"""
evaluator_optimizer.py - Week 1, Day 5, Pattern 5: evaluator-optimizer

  WRITER   writes a product description
  REVIEWER plain-Python checks first (free), then an AI judge with a rubric
  If the review fails, the writer gets its own draft + the feedback and tries again.
  The loop stops at PASS or after max_rounds (never "while True").

Run:  uv run python evaluator_optimizer.py          (limit 70 words, usually passes fast)
      uv run python evaluator_optimizer.py hard     (limit 35 words, you will see the loop work)
"""
import sys

from llm import llm

FACTS = ("Handloom Banarasi silk saree. Deep maroon with a gold zari border. Price Rs. 12,500. "
         "Dry clean only. Ideal for weddings and Diwali.")

RUBRIC = """You review a product description for an online saree shop. Judge it against ALL these rules:
1. It uses ONLY the facts given (no invented details).
2. It mentions the fabric, the colour and the price.
3. It includes the care instruction.
4. It makes no claims that cannot be proven (words like best, guaranteed, 100% pure, perfect).
5. It ends with a short call to action.

Reply in this exact format:
First line: PASS or FAIL (one word only).
Then, only if FAIL, up to 3 short lines saying exactly what to fix. Do not rewrite the description."""


def _text(resp) -> str:
    return (resp.choices[0].message.content or "").strip()


# ---------------------------------------------------------------
# The writer
# ---------------------------------------------------------------
def generate(max_words: int, previous: str | None = None, feedback: str | None = None) -> str:
    if previous is None:
        prompt = (f"Write a product description for the shop website. Use ONLY these facts:\n{FACTS}\n"
                  f"Maximum {max_words} words. Output only the description.")
        messages = [{"role": "user", "content": prompt}]
    else:
        messages = [
            {"role": "user", "content": f"Write a product description using ONLY these facts:\n{FACTS}\n"
                                        f"Maximum {max_words} words. Output only the description."},
            {"role": "assistant", "content": previous},
            {"role": "user", "content": f"A reviewer rejected that draft: {feedback}\n"
                                        f"Rewrite it and fix every problem. Same rules: only the given facts, "
                                        f"maximum {max_words} words. Output only the description."},
        ]
    return _text(llm(messages, max_tokens=200))


# ---------------------------------------------------------------
# The reviewer: code first, then the AI judge
# ---------------------------------------------------------------
def evaluate(draft: str, max_words: int) -> tuple[bool, str]:
    # Check 1: plain Python. Models are bad at counting words, code is exact, and it costs nothing.
    words = len(draft.split())
    if words > max_words:
        return False, f"too long: {words} words (maximum {max_words}). Cut it down."

    # Check 2: judgement that needs language understanding goes to the AI judge
    resp = llm(
        [{"role": "system", "content": RUBRIC},
         {"role": "user", "content": f"Facts the writer was given:\n{FACTS}\n\nDraft:\n{draft}"}],
        max_tokens=200,
    )
    lines = _text(resp).splitlines()
    verdict = lines[0].strip().strip("*.:").upper() if lines else ""
    feedback = " ".join(l.strip() for l in lines[1:] if l.strip())

    if verdict == "PASS":
        return True, feedback or "all rules met"
    if verdict == "FAIL":
        return False, feedback or "(the judge gave no details)"
    return False, f"the judge's answer was unreadable: {lines[:1]}"  # never treat garbage as a PASS


# ---------------------------------------------------------------
# The loop
# ---------------------------------------------------------------
def optimize(max_words: int, max_rounds: int = 3):
    draft, feedback = None, None
    for round_no in range(1, max_rounds + 1):
        draft = generate(max_words, draft, feedback)
        passed, feedback = evaluate(draft, max_words)

        print(f"\n--- round {round_no} ---")
        print(f"DRAFT ({len(draft.split())} words): {draft}")
        print(f"REVIEW: {'PASS' if passed else 'FAIL'} | {feedback}")

        if passed:
            return draft, round_no, True
    return draft, max_rounds, False


if __name__ == "__main__":
    max_words = 35 if len(sys.argv) > 1 and sys.argv[1] == "hard" else 70
    print(f"FACTS: {FACTS}\nWord limit: {max_words}")

    draft, rounds, passed = optimize(max_words)

    print("\n" + "=" * 60)
    if passed:
        print(f"PASSED after {rounds} round(s):\n{draft}")
    else:
        print(f"NOT PASSED after {rounds} rounds. The last draft needs a human look:\n{draft}")