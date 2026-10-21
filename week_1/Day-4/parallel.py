"""
parallel.py - Week 1, Day 4, Pattern 3: parallelisation

Headache 3: “It’s slow, and sometimes it can’t make up its mind”
• This one has two parts.
    Part A: Sectioning (slow)
    - The problem: you have a long document, and you ask the AI to summarise 6 paragraphs one by one. Most of each call is just waiting for the network, so you wait six times.
    - The fix: think of 6 friends. You can ask one friend to summarise all 6 paragraphs, or you can give one paragraph to each friend at the same moment. The second way is far faster.
    - Your own result shows it: 8.52 seconds one by one, and 2.06 seconds in parallel. That’s 4.1x faster. The cost was the same, because it was still 6 calls. Parallelism buys you time, not money.
    - The “semaphore” in the code is a rule that says “no more than 5 at once”, so you don’t flood the server.

    Part B: Voting (unsure)
    - The problem: some yes/no questions are borderline. “Is this ad misleading?” can get a different answer each time you ask.
    - The fix: don’t ask one person, ask 3 and take the majority. The AI needs a little randomness here, because three identical answers would just be one vote copied three times.
    - 3 out of 3 agree means a unanimous verdict, and you can trust it.
    - A 2 against 1 split vote means the case is borderline, so a human should look at it.

SECTIONING: split a long document into parts, process all parts at the same
            time, then merge. We time it against doing the parts one by one.
VOTING:     ask the SAME question 3 times at once and take the majority.

Run:  uv run python parallel.py                        (both demos)
      uv run python parallel.py sectioning             (built-in sample document)
      uv run python parallel.py sectioning my_doc.txt  (your own text file)
      uv run python parallel.py voting

Run it as a script. In Jupyter, asyncio.run() fails; use `await sectioning(...)` instead.
"""
import asyncio
import sys
import time
from collections import Counter

from llm_async import allm

SAMPLE_DOC = """Surat Silks accepts returns within fourteen days of delivery. Items must be unworn, unwashed and carry the original tags. To start a return, open your order page and choose Return Item. We send a prepaid courier label by email, and the refund reaches your original payment method within seven working days of inspection.

Orders are packed within two working days. Standard delivery takes three to six days inside Gujarat and five to nine days for the rest of India. Express delivery is available in major cities for an extra fee shown at checkout. Every parcel has a tracking link that is sent by SMS and email once it leaves our warehouse.

We accept UPI, debit and credit cards, net banking and cash on delivery for orders under ten thousand rupees. Card payments are processed by a certified payment partner and we never store your card number. If a payment fails but money is deducted, the amount is automatically returned within five working days.

Handloom silk sarees come with a six month guarantee against weaving defects. The guarantee does not cover damage from washing at home, perfume stains or normal wear. We recommend dry cleaning only, storing sarees in a soft cotton cloth, and refolding them every few months to prevent permanent creases along the folds.

We collect your name, address, phone number and order history to deliver your purchases and to send updates you have asked for. We never sell your data. You can ask us to delete your account at any time by writing to support, and we will remove personal details within thirty days, except records the law requires us to keep.

Our support team answers calls and chats from ten in the morning to seven in the evening, Monday to Saturday. Emails sent outside these hours are answered the next working day. During festival weeks we add extra staff, but replies can still take up to a day. For urgent delivery problems, please use the chat option."""


def _first_word(resp) -> str:
    parts = (resp.choices[0].message.content or "").strip().split()
    return parts[0].strip(".,!:;'\"").upper() if parts else ""


# ---------------------------------------------------------------
# SECTIONING
# ---------------------------------------------------------------
def split_into_chunks(text: str, max_words: int = 70) -> list[str]:
    """Group whole paragraphs into chunks of at most max_words words (a paragraph is never cut)."""
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks, current, count = [], [], 0
    for p in paragraphs:
        n = len(p.split())
        if current and count + n > max_words:
            chunks.append("\n\n".join(current))
            current, count = [], 0
        current.append(p)
        count += n
    if current:
        chunks.append("\n\n".join(current))
    return chunks


async def summarize(chunk: str, sem: asyncio.Semaphore) -> str:
    async with sem:  # the semaphore allows only a few calls at once (protects against rate limits)
        resp = await allm(
            [{"role": "user", "content": f"Summarize this in ONE short sentence:\n\n{chunk}"}],
            max_tokens=80,
        )
    return (resp.choices[0].message.content or "").strip()


async def sectioning(document: str):
    chunks = split_into_chunks(document)
    sem = asyncio.Semaphore(5)
    print(f"Document split into {len(chunks)} chunks.\n")

    t0 = time.perf_counter()
    one_by_one = [await summarize(c, sem) for c in chunks]  # wait for each call before starting the next
    t_seq = time.perf_counter() - t0

    t0 = time.perf_counter()
    at_once = await asyncio.gather(*(summarize(c, sem) for c in chunks))  # start them all together
    t_par = time.perf_counter() - t0

    print("MERGED SUMMARY (from the parallel run, in the original order):")
    for i, s in enumerate(at_once, 1):
        print(f"  {i}. {s}")

    print(f"\nOne by one : {t_seq:.2f}s  ({len(one_by_one)} calls)")
    print(f"In parallel: {t_par:.2f}s  ({len(at_once)} calls)")
    print(f"Speed-up   : {t_seq / t_par:.1f}x   (cost is the same: the same number of calls ran twice)")


# ---------------------------------------------------------------
# VOTING
# ---------------------------------------------------------------
QUESTION = ("You are a strict marketing reviewer. Does the text below make a claim that could mislead "
            "customers (absolute guarantees, health claims, or superlatives that cannot be proven)? "
            "Answer with exactly one word: YES or NO.\n\nText: {text}")

TEXTS = [
    "Guaranteed to cure back pain forever! 100% pure silk, the best in all of India.",
    "Our new cotton kurtas come in five colours and sizes S to XXL.",
    "Our sarees are among the softest you will ever wear.",
    "Made with premium silk and loved by thousands of customers.",
]


async def one_vote(text: str) -> str:
    resp = await allm([{"role": "user", "content": QUESTION.format(text=text)}],
                      max_tokens=5, temperature=0.8)  # some randomness, or all 3 votes would be identical
    word = _first_word(resp)
    return word if word in ("YES", "NO") else "INVALID"


async def vote(text: str, n: int = 3):
    votes = await asyncio.gather(*(one_vote(text) for _ in range(n)))
    counts = Counter(v for v in votes if v != "INVALID")
    if not counts:
        return votes, "UNSURE", "no valid votes"

    ranked = counts.most_common()
    if len(ranked) > 1 and ranked[0][1] == ranked[1][1]:
        return votes, "UNSURE", "tie"

    verdict = ranked[0][0]
    agreement = "unanimous" if len(counts) == 1 and sum(counts.values()) == n else "SPLIT VOTE"
    return votes, verdict, agreement


async def voting():
    for text in TEXTS:
        votes, verdict, agreement = await vote(text)
        print(f"\nTEXT    : {text}")
        print(f"VOTES   : {votes}")
        print(f"VERDICT : misleading? {verdict}   ({agreement})")


# ---------------------------------------------------------------
async def main(which: str, document: str):
    if which in ("sectioning", "both"):
        print("=== SECTIONING ===\n")
        await sectioning(document)

    if which in ("voting", "both"):
        print("\n=== VOTING ===")
        await voting()


if __name__ == "__main__":
    which = sys.argv[1] if len(sys.argv) > 1 else "both"
    doc = SAMPLE_DOC
    if which in ("sectioning", "both") and len(sys.argv) > 2:
        with open(sys.argv[2], encoding="utf-8") as f:
            doc = f.read()

    # ONE asyncio.run for the whole program. The async client keeps its network
    # connections tied to the event loop that first used them; a second
    # asyncio.run() would start a new loop and hit "Event loop is closed".
    asyncio.run(main(which, doc))