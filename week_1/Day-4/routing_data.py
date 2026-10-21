"""
routing_data.py - Week 1, Day 4

30 customer messages for Surat Silks, each with the CORRECT category.
These labels are MY DRAFT. Your job is the "hand-label" step of the plan:

  1. Read every message and decide the category YOURSELF.
  2. Change any label you disagree with.
  3. Do this BEFORE you run routing.py, so the model's answers do not influence you.

The categories (the router prompt uses the same definitions):
  billing    - money: payments, refunds, invoices, extra charges, coupons, cancelling a paid plan
  technical  - the website/app is broken or confusing: login, OTP, crashes, pages not loading, emails not arriving
  info       - questions about products, sizes, stock, policies, delivery times or order status
  complaint  - unhappy about quality, service or behaviour, with no specific billing or technical request

Tie-break rule: a concrete money problem wins -> billing; else a concrete website/app problem -> technical.
"""

DATA = [
    # (message, correct_category)
    ("I was charged twice for order #4411, please refund one payment.", "billing"),                    # 1
    ("Can you send me the GST invoice for my last purchase?", "billing"),                              # 2
    ("My refund of Rs. 1,200 hasn't reached my bank account yet.", "billing"),                        # 3
    ("Why was an extra Rs. 99 added at checkout?", "billing"),                                        # 4
    ("Can I pay by UPI instead of card for my pending order?", "billing"),                            # 5
    ("The coupon SAVE10 didn't apply, but the discount showed on the page.", "billing"),              # 6 (tricky)
    ("Please update the billing address on invoice INV-2290.", "billing"),                             # 7
    ("I want to cancel my subscription so I won't be charged next month.", "billing"),                # 8

    ("I can't log in. The page says 'invalid OTP' even with the right code.", "technical"),            # 9
    ("The app crashes every time I open my cart.", "technical"),                                      # 10
    ("The checkout page keeps loading and never finishes.", "technical"),                             # 11
    ("I didn't get the password reset email.", "technical"),                                          # 12
    ("The size chart on your website won't open.", "technical"),                                      # 13
    ("The order tracking link gives a 404 error.", "technical"),                                      # 14
    ("How do I switch the app to dark mode?", "technical"),                                           # 15
    ("Product photos don't load on my tablet.", "technical"),                                         # 16

    ("Do you have this kurta in size XL?", "info"),                                                   # 17
    ("How long does delivery to Mumbai usually take?", "info"),                                       # 18
    ("Is the silk saree pure Banarasi or a blend?", "info"),                                          # 19
    ("What is your return policy for sale items?", "info"),                                           # 20
    ("When will the blue jacket be back in stock?", "info"),                                          # 21
    ("Where is my order #5532? It was supposed to arrive yesterday.", "info"),                        # 22 (tricky)
    ("Do you ship to the UK, and what are the charges?", "info"),                                     # 23 (tricky)
    ("What material is the cotton tote bag made of?", "info"),                                        # 24

    ("The dress I received was torn and the colour is different from the photo. Very disappointed.", "complaint"),  # 25
    ("Third time my delivery is late. This is terrible service.", "complaint"),                       # 26
    ("Your staff was rude to me on the phone yesterday.", "complaint"),                               # 27
    ("I ordered a medium but got a small, and nobody replied to my emails for a week.", "complaint"), # 28
    ("Worst shopping experience ever. I'm never buying from you again.", "complaint"),                # 29
    ("Charged twice AND the app crashed on me. I'm furious, fix this now!", "billing"),               # 30 (tricky)
]

TRICKY = {6, 22, 23, 30}  # messages where two categories are arguable; the tie-break rule decides