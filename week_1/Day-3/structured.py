"""
structured.py - Week 1, Day 3
 
Turn messy text into a validated Python object (an Invoice).
Flow: ask for JSON -> validate with Pydantic -> if it fails, retry ONCE
and send the exact error back to the model.
 
Install first:  uv add pydantic
Run a demo:     uv run python structured.py
"""

from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, ValidationError, model_validator
from llm import llm


# ---------------------------------------------------------------
# 1. The shape we want (the "schema")
# ---------------------------------------------------------------

class LineItem(BaseModel):
    description : str
    quantity    : float = Field(gt = 0)
    unit_price  : float = Field(ge = 0)

class Invoice(BaseModel):
    vendor : str
    invoice_number : Optional[str] = None
    invoice_date   : date
    currency       : Literal["INR", "USD", "EUR"]
    items          : list[LineItem] = Field(min_length = 1)
    tax            : float = Field(default = 0, ge = 0)
    total          : float = Field(ge = 0)

    @model_validator(mode = "after")
    def total_must_add_up(self):
        calculated = sum(i.quantity * i.unit_price for i in self.items) + self.tax
        if abs(calculated - self.total) > 0.01:
            raise ValueError(
                f"ERROR : Total is {self.total}, but item + tax add up to {calculated}"
            )

        return self

class ExtractionError(Exception):
    """
        Raised when model's output is still invalid even after retry.
    """


# ---------------------------------------------------------------
# 2. The prompt
# ---------------------------------------------------------------

def build_system_prompt() -> str:
    schema = Invoice.model_json_schema()
    return (
        "You extract invoice data from messy text.\n"
        "Reply with ONE JSON object only. No explanation, no markdown fences.\n"
        f"It must match this JSON schema:\n{schema}\n\n"
        "Rules:\n"
        "- Dates must be YYYY-MM-DD. Dates written as numbers in the text are day-first (DD/MM/YYYY).\n"
        "- Numbers must be plain numbers: no commas, no currency symbols. Example: 1,20,000 -> 120000.\n"
        "- If a value is not in the text (for example the invoice number), use null. Never invent values.\n"
        "- tax is the total tax amount (0 if none). total is the final amount payable.\n"
        "- currency: map symbols to codes (Rs or the rupee sign -> INR, $ -> USD, euro sign -> EUR)."
        "- An invoice number may be labelled 'invoice no', 'bill no', 'ref' or 'ref no'. Use it if present; use null only if there is no such code."
    )


# ---------------------------------------------------------------
# 3. Helpers
# ---------------------------------------------------------------

def _strip_fences(raw: str) -> str:
    """Models sometimes wrap JSON in ```json ... ``` even when told not to."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.strip("`").strip()
        if raw.lower().startswith("json"):
            raw = raw[4:]
    return raw.strip()
 
 
def _describe(error: ValidationError) -> str:
    """Short, readable version of a Pydantic error to send back to the model."""
    parts = []
    for e in error.errors():
        where = ".".join(str(p) for p in e["loc"]) or "(whole object)"
        parts.append(f"{where}: {e['msg']}")
    return "; ".join(parts)
 
 
# ---------------------------------------------------------------
# 4. The extractor
# ---------------------------------------------------------------

def extract(text: str, max_retries: int = 1) -> tuple[Invoice, int]:
    """Return (invoice, retries_used). Raise ExtractionError if it never validates."""
    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": text},
    ]
 
    last_problem = ""
    for attempt in range(max_retries + 1):
        raw = llm(messages, max_tokens=800).choices[0].message.content or ""
        try:
            # Checks the JSON syntax AND the schema AND our total_must_add_up rule
            invoice = Invoice.model_validate_json(_strip_fences(raw))
            return invoice, attempt
        except ValidationError as e:
            last_problem = _describe(e)
            # Show the model its own answer and exactly what was wrong with it
            messages.append({"role": "assistant", "content": raw})
            messages.append({
                "role": "user",
                "content": f"Your JSON failed validation: {last_problem}\n"
                           "Fix the problems and return the corrected JSON only.",
            })
 
    raise ExtractionError(f"Still invalid after {max_retries} retry: {last_problem}")
 


if __name__ == "__main__":
    sample = (
        "Hi, bill from Patel Hardware (ref PH/2026/334) dated 20/10/2026. "
        "4 cement bags at Rs. 380 each and 2 paint buckets at Rs. 1,250 each. "
        "No tax. Total Rs. 4,020."
    )
    invoice, retries = extract(sample)
    print(invoice.model_dump_json(indent=2))
    print(f"\nRetries used: {retries}")
