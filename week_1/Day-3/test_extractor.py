"""
test_extractor.py - Week 1, Day 3
 
10 messy inputs with the expected answer for each. Counts how many come out right.
Run:  uv run python test_extractor.py
"""

from structured import ExtractionError, extract



CASES = [
    {
        "name": "clean, one line",
        "text": ("Invoice #INV-1001 from Sharma Textiles dated 12 Oct 2026. "
                 "10 x Cotton shirt @ 450 INR, 5 x Denim jeans @ 900 INR. "
                 "GST 18%: 1620 INR. Total: 10620 INR."),
        "expect": {"vendor": "Sharma Textiles", "number": "INV-1001", "date": "2026-10-12",
                   "currency": "INR", "total": 10620, "n_items": 2},
    },
    {
        "name": "casual email, Indian number format",
        "text": ("Hi team,\n\nPlease find the bill from Patel Hardware (ref no PH/2026/334) for 20 Oct 2026. "
                 "We bought 4 cement bags at Rs. 380 each and 2 paint buckets at Rs. 1,250 each. "
                 "No tax was charged. Total Rs. 4,020.\n\nThanks,\nRaj"),
        "expect": {"vendor": "Patel Hardware", "number": "PH/2026/334", "date": "2026-10-20",
                   "currency": "INR", "total": 4020, "n_items": 2},
    },
    {
        "name": "USD, numeric day-first date",
        "text": ("INVOICE\nVendor: Blue Cloud Hosting Inc.\nInvoice No: BC-77\nDate: 05/11/2026\n"
                 "1 x Server (monthly) $120.00\n3 x Extra storage 100GB $15.00\n"
                 "Tax: $13.50\nAmount due: $178.50"),
        "expect": {"vendor": "Blue Cloud Hosting", "number": "BC-77", "date": "2026-11-05",
                   "currency": "USD", "total": 178.5, "n_items": 2},
    },
    {
        "name": "lakh format, ordinal date",
        "text": ("Tax invoice no. 2026-0415 issued by Kothari Jewellers on 3rd November 2026. "
                 "1 x Gold chain 22k = Rs 1,20,000. GST @3% = Rs 3,600. Grand total Rs 1,23,600."),
        "expect": {"vendor": "Kothari Jewellers", "number": "2026-0415", "date": "2026-11-03",
                   "currency": "INR", "total": 123600, "n_items": 1},
    },
    {
        "name": "quantities written as words",
        "text": ("Bill from Chai Point Cafe, invoice CP-908, 15-10-2026. Two cappuccino at \u20b9150 each, "
                 "three sandwiches at \u20b9200 each. Tax 5%: 45. Total: 945."),
        "expect": {"vendor": "Chai Point Cafe", "number": "CP-908", "date": "2026-10-15",
                   "currency": "INR", "total": 945, "n_items": 2},
    },
    {
        "name": "EUR with VAT, ISO date",
        "text": ("Rechnung / Invoice\nStudio Berlin GmbH\nInvoice number: SB-2026-88\nDate: 2026-10-30\n"
                 "5 hours consulting x \u20ac80 = \u20ac400\nVAT 19%: \u20ac76\nTotal: \u20ac476"),
        "expect": {"vendor": "Studio Berlin", "number": "SB-2026-88", "date": "2026-10-30",
                   "currency": "EUR", "total": 476, "n_items": 1},
    },
    {
        "name": "NO invoice number (must be null)",
        "text": ("Hey, quick note: Gupta Stationers charged me 640 INR on 18/10/2026 for 8 notebooks "
                 "at 80 each. No tax. No bill number was given."),
        "expect": {"vendor": "Gupta Stationers", "number": None, "date": "2026-10-18",
                   "currency": "INR", "total": 640, "n_items": 1},
    },
    {
        "name": "three items with decimals",
        "text": ("Invoice: AGR-5521 | Agro Fresh Traders | Date: 22 Oct 2026\n"
                 "- Tomatoes 12 kg @ \u20b932.50 = \u20b9390\n- Onions 25 kg @ \u20b928 = \u20b9700\n"
                 "- Potatoes 40 kg @ \u20b922.75 = \u20b9910\nTax: \u20b90\nTotal: \u20b92000"),
        "expect": {"vendor": "Agro Fresh Traders", "number": "AGR-5521", "date": "2026-10-22",
                   "currency": "INR", "total": 2000, "n_items": 3},
    },
    {
        "name": "forwarded email with noise",
        "text": ("---------- Forwarded message ----------\nFrom: accounts@zenith-logistics.in\n"
                 "Subject: Invoice ZL/10/2026/019\n\nDear customer, your freight invoice dated 25-Oct-2026 "
                 "is attached. Charges: Freight 1 shipment 18,500 INR; Handling fee 1 unit 1,500 INR. "
                 "GST (18%) INR 3,600. Net payable: INR 23,600.\nRegards, Zenith Logistics Pvt Ltd"),
        "expect": {"vendor": "Zenith Logistics", "number": "ZL/10/2026/019", "date": "2026-10-25",
                   "currency": "INR", "total": 23600, "n_items": 2},
    },
    {
        "name": "lowercase, compressed",
        "text": "inv no 4412 - moonlight studios - 01/12/2026 - logo design x1 $450, 2 revisions x $75 each. tax $0. total $600",
        "expect": {"vendor": "Moonlight Studios", "number": "4412", "date": "2026-12-01",
                   "currency": "USD", "total": 600, "n_items": 2},
    },
]



def _norm(number):
    return number.lstrip("#").strip().casefold() if number else None
 
 
def check(invoice, exp) -> list[str]:
    """Return a list of mismatches. Empty list = correct."""
    problems = []
    if exp["vendor"].casefold() not in invoice.vendor.casefold():
        problems.append(f"vendor: got {invoice.vendor!r}")
    if _norm(invoice.invoice_number) != _norm(exp["number"]):
        problems.append(f"number: got {invoice.invoice_number!r}, expected {exp['number']!r}")
    if str(invoice.invoice_date) != exp["date"]:
        problems.append(f"date: got {invoice.invoice_date}, expected {exp['date']}")
    if invoice.currency != exp["currency"]:
        problems.append(f"currency: got {invoice.currency}, expected {exp['currency']}")
    if abs(invoice.total - exp["total"]) > 0.01:
        problems.append(f"total: got {invoice.total}, expected {exp['total']}")
    if len(invoice.items) != exp["n_items"]:
        problems.append(f"items: got {len(invoice.items)}, expected {exp['n_items']}")
    return problems



if __name__ == "__main__":
    correct = retried = failed = 0
 
    for i, case in enumerate(CASES, 1):
        try:
            invoice, retries = extract(case["text"])
        except ExtractionError as e:
            failed += 1
            print(f"{i:>2}. FAIL (never validated)  {case['name']}\n      {e}")
            continue
 
        retried += 1 if retries else 0
        problems = check(invoice, case["expect"])
        if problems:
            print(f"{i:>2}. WRONG  {case['name']}  (retries: {retries})")
            for p in problems:
                print(f"      - {p}")
        else:
            correct += 1
            print(f"{i:>2}. OK     {case['name']}  (retries: {retries})")
 
    print("\n" + "=" * 50)
    print(f"Correct:                  {correct}/{len(CASES)}")
    print(f"Needed a retry:           {retried}")
    print(f"Failed validation twice:  {failed}")
