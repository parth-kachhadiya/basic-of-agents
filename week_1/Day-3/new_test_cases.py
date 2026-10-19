"""
new_cases.py - Week 1, Day 3 (extra)

3 FRESH cases that your prompt was not tuned on. They reuse extract() and
check() from your existing files, so you do not edit anything.

Run:  uv run python new_cases.py
"""
from structured import ExtractionError, extract
from test_extractor import check

NEW_CASES = [
    {
        # An invoice-number label that is NOT in your prompt rule
        "name": "unseen label: 'Doc no.'",
        "text": ("Doc no. D-2207 | Mehta Electricals | 14/11/2026\n"
                 "3 LED bulbs @ Rs. 120, 1 extension board @ Rs. 450\n"
                 "No tax. Total Rs. 810"),
        "expect": {"vendor": "Mehta Electricals", "number": "D-2207", "date": "2026-11-14",
                   "currency": "INR", "total": 810, "n_items": 1 + 1},
    },
    {
        # Two codes and two dates in the text: only ONE is the invoice
        "name": "trap: PO number vs invoice number",
        "text": ("Purchase order PO-8841 was placed on 02/11/2026. Rao Packaging has now billed us "
                 "under invoice RP-0519 dated 19/11/2026: 200 boxes at Rs. 15 each, "
                 "GST 12%: Rs. 360. Total: Rs. 3,360."),
        "expect": {"vendor": "Rao Packaging", "number": "RP-0519", "date": "2026-11-19",
                   "currency": "INR", "total": 3360, "n_items": 1},
    },
    {
        # A code-like thing that is NOT an invoice number. The answer must be null.
        "name": "trap: phone number is not an invoice number",
        "text": ("Quick bill from Joshi Dairy: 10 litres milk at Rs. 60 each, paid on 21/11/2026. "
                 "Call me on 98765 43210 if anything is wrong. No tax. Total Rs. 600."),
        "expect": {"vendor": "Joshi Dairy", "number": None, "date": "2026-11-21",
                   "currency": "INR", "total": 600, "n_items": 1},
    },
]


if __name__ == "__main__":
    correct = 0
    for i, case in enumerate(NEW_CASES, 1):
        print(f"\n{i}. {case['name']}")
        try:
            invoice, retries = extract(case["text"])
        except ExtractionError as e:
            print(f"   FAIL (never validated): {e}")
            continue

        print(f"   model said: number={invoice.invoice_number!r}, date={invoice.invoice_date}, "
              f"total={invoice.total}, retries={retries}")
        problems = check(invoice, case["expect"])
        if problems:
            print("   WRONG")
            for p in problems:
                print(f"      - {p}")
        else:
            correct += 1
            print("   OK")

    print(f"\nFresh cases correct: {correct}/{len(NEW_CASES)}")