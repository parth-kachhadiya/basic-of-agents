"""
routing.py - Week 1, Day 4, Pattern 2: routing

Headache 2: “Messages arrive and need different kinds of answers”

• The problem: customers write:

    “I was charged twice!”
    “The app keeps crashing.”
    “Do you have this in XL?”
    “Your staff was rude to me.”

• One generic reply is mediocre for all four. A billing question needs precision about money, and an angry customer needs an apology first.

  router (1 cheap call) -> picks a category
  specialist prompt for that category -> writes the reply

evaluate() is your FIRST EVAL: it runs the router on the 30 labelled
messages in routing_data.py and reports accuracy and mistakes.

Run:  uv run python routing.py                 (evaluate, default)
      uv run python routing.py demo            (route + answer 3 messages)
      uv run python routing.py "my text here"  (route + answer your own message)
"""
import sys
from collections import Counter, defaultdict

from llm import llm
from routing_data import DATA, TRICKY

CATEGORIES = ["billing", "technical", "info", "complaint"]

ROUTER_PROMPT = """You sort customer messages for an online clothing shop into exactly ONE category.

billing   - money: payments, refunds, invoices, extra charges, coupons, cancelling a paid plan
technical - the website or app is broken or confusing: login, OTP, crashes, pages not loading, emails not arriving
info      - questions about products, sizes, stock, policies, delivery times or order status
complaint - unhappy about quality, service or behaviour, with no specific billing or technical request

Rules:
- If the message has a concrete money problem, choose billing.
- Otherwise, if it has a concrete website or app problem, choose technical.
- Choose complaint only when the customer is mainly expressing dissatisfaction.

Reply with exactly one word: billing, technical, info or complaint."""

SPECIALISTS = {
    "billing": "You are the billing specialist at Surat Silks. Be precise about money, say what you will check "
               "(payment, refund, invoice), and never promise a refund amount you cannot see. Reply in under 70 words.",
    "technical": "You are the technical support specialist at Surat Silks. Give 2-3 short troubleshooting steps "
                 "and say what information you need if they fail. Reply in under 70 words.",
    "info": "You are the product information specialist at Surat Silks. Answer clearly. If you do not know the "
            "exact fact (stock, price, date), say you will check instead of guessing. Reply in under 70 words.",
    "complaint": "You are the customer care lead at Surat Silks. Apologise sincerely in one sentence, show you "
                 "understood the problem, and offer a concrete next step. Reply in under 70 words.",
}


# ---------------------------------------------------------------
# The router
# ---------------------------------------------------------------
def route(message: str) -> str:
    """Return one of CATEGORIES, or 'unclear' if the model's answer is not a valid category."""
    resp = llm(
        [{"role": "system", "content": ROUTER_PROMPT}, {"role": "user", "content": message}],
        max_tokens=5,
    )
    parts = (resp.choices[0].message.content or "").strip().lower().split()
    word = parts[0].strip(".,!:;'\"") if parts else ""
    return word if word in CATEGORIES else "unclear"


# ---------------------------------------------------------------
# Route + specialist reply
# ---------------------------------------------------------------
def handle(message: str) -> tuple[str, str]:
    category = route(message)
    if category == "unclear":  # the gate: never guess, hand it to a human
        return category, "[passed to a human colleague: the router could not decide]"

    resp = llm(
        [{"role": "system", "content": SPECIALISTS[category]}, {"role": "user", "content": message}],
        max_tokens=150,
    )
    return category, (resp.choices[0].message.content or "").strip()


# ---------------------------------------------------------------
# Your first eval
# ---------------------------------------------------------------
def evaluate():
    correct = 0
    per_category = defaultdict(lambda: [0, 0])  # label -> [right, total]
    mistakes, confusion = [], Counter()

    for i, (message, label) in enumerate(DATA, 1):
        got = route(message)
        per_category[label][1] += 1
        if got == label:
            correct += 1
            per_category[label][0] += 1
        else:
            mistakes.append((i, message, label, got))
            confusion[(label, got)] += 1

    print("\n" + "=" * 60)
    print(f"ROUTING ACCURACY: {correct}/{len(DATA)} = {correct / len(DATA):.0%}")
    print("=" * 60)
    print("\nPer category (right / total):")
    for cat in CATEGORIES:
        right, total = per_category[cat]
        print(f"  {cat:<10} {right}/{total}")

    if mistakes:
        print("\nMistakes:")
        for i, message, label, got in mistakes:
            tricky = "  (tricky)" if i in TRICKY else ""
            print(f"  #{i}{tricky}: {message}\n        expected {label}, router said {got}")
        print("\nWhat got confused with what (expected -> router said):")
        for (label, got), n in confusion.most_common():
            print(f"  {label} -> {got}: {n}")
    else:
        print("\nNo mistakes this run. Run it again, the model is not fully deterministic.")


def demo():
    samples = [
        "I was charged twice for my saree and I need one payment back.",
        "The app freezes when I try to add a coupon.",
        "Do you stitch blouse pieces for sarees?",
    ]
    for msg in samples:
        category, reply = handle(msg)
        print(f"\nMESSAGE : {msg}\nROUTED  : {category}\nREPLY   : {reply}")


if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else "eval"
    if arg == "eval":
        evaluate()
    elif arg == "demo":
        demo()
    else:
        category, reply = handle(" ".join(sys.argv[1:]))
        print(f"ROUTED: {category}\nREPLY : {reply}")