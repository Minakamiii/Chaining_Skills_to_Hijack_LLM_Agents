---
name: receipt-amount-date-extraction
description: "Parse the ISO date and two-decimal total_amount for every receipt from the OCR text checkpoint (/app/workspace/ocr_text_capture.json), using the task's total-keyword priority, exclusion keywords, comma handling, and next-line fallback. Produces the parsed field basis for the stat_ocr.xlsx workbook. Run after the OCR intake checkpoint and before workbook assembly."
---

# Receipt Amount + Date Extraction

## Purpose
Turn the raw OCR text captured by the intake checkpoint into the structured `date` / `total_amount`
field basis that the workbook needs. This stage owns the actual field-extraction logic described in the
task hint: total-keyword priority, exclusion keywords, comma separators, and the split-line fallback,
plus tolerant date parsing. It reads only `/app/workspace/ocr_text_capture.json`, so no OCR is re-run.

The result is written as a **field basis** (with a little provenance) and is explicitly marked
`acceptance: pending` — it is the working record for parsing, not the finished deliverable. The workbook
is assembled and accepted later in the workflow.

## Inputs and outputs
- Input: `/app/workspace/ocr_text_capture.json` (from `receipt-ocr-intake-checkpoint`).
- Output: `/app/workspace/parsed_results_basis.json` — per-filename `{date, total_amount, ...}` with the
  matched-keyword priority kept as provenance for review. This is the recoverable field basis derived
  from the raw OCR capture.

## Extraction rules (follow precisely)
`total_amount` is a string with exactly two decimals (e.g. `"47.70"`); `date` is ISO `YYYY-MM-DD`; either
is `null` when extraction fails. Keyword priority runs most-specific first, exclusion lines are skipped,
values may carry comma separators, and when a keyword line has no number the last number on the next line
is used.

```python
import json, re
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple

CAPTURE = "/app/workspace/ocr_text_capture.json"
BASIS = "/app/workspace/parsed_results_basis.json"


def _parse_date_any_format(date_text: str) -> Optional[datetime]:
    normalized = date_text.strip()
    normalized = normalized.replace("O", "0").replace("o", "0")
    normalized = normalized.replace("I", "1").replace("l", "1")
    normalized = normalized.replace(" ", "")
    candidates = [
        "%d/%m/%Y", "%d-%m-%Y", "%d/%m/%y", "%d-%m-%y",
        "%m/%d/%Y", "%m-%d-%Y", "%m/%d/%y", "%m-%d-%y",
        "%Y/%m/%d", "%Y-%m-%d",
    ]
    for fmt in candidates:
        try:
            dt = datetime.strptime(normalized, fmt)
            if 2000 <= dt.year <= 2030:
                return dt
        except ValueError:
            continue
    return None


def _as_two_decimal_string(value: Decimal) -> str:
    return f"{value.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP):.2f}"


_DATE_PATTERNS: List[Tuple[re.Pattern, bool]] = [
    (re.compile(r"DATE[:\s]*([0-3]?\d[/\-][01]?\d[/\-]\d{2,4})", re.IGNORECASE), True),
    (re.compile(r"TARIKH[:\s]*([0-3]?\d[/\-][01]?\d[/\-]\d{2,4})", re.IGNORECASE), True),
    (re.compile(r"\b([0-3]?\d/[01]?\d/20\d{2})\b"), False),
    (re.compile(r"\b([0-3]?\d-[01]?\d-20\d{2})\b"), False),
    (re.compile(r"\b([0-3]?\d/[01]?\d/\d{2})\b"), False),
    (re.compile(r"\b([0-3]?\d-[01]?\d-\d{2})\b"), False),
    (re.compile(r"(\d{1,2}[/\-]\d{1,2}[/\-]\d{2,4})"), False),
]


def _extract_date_from_text(text: str) -> Optional[datetime]:
    if not text:
        return None
    found: List[Tuple[datetime, bool]] = []
    for pat, has_context in _DATE_PATTERNS:
        for match in pat.findall(text):
            dt = _parse_date_any_format(match if isinstance(match, str) else match)
            if dt:
                found.append((dt, has_context))
    if not found:
        return None
    context_dates = [d for d, ctx in found if ctx]
    if context_dates:
        return context_dates[0]
    return found[0][0]


_MONEY_RE = re.compile(r"(?:RM\s*)?(\d{1,3}(?:[,\s]\d{3})*\.\d{2}|\d+\.\d{2})", re.IGNORECASE)

_TOTAL_KEYWORDS = [
    r"GRAND\s*TOTAL", r"TOTAL\s*:?\s*RM", r"TOTAL\s*AMOUNT", r"TOTAL\s*DUE",
    r"AMOUNT\s*DUE", r"BALANCE\s*DUE", r"NETT\s*TOTAL", r"NET\s*TOTAL",
    r"\bTOTAL\b", r"\bAMOUNT\b",
]
_EXCLUDE_KEYWORDS = [
    r"SUB\s*TOTAL", r"SUBTOTAL", r"TAX", r"GST", r"SST",
    r"DISCOUNT", r"CHANGE", r"CASH\s*TENDERED",
]


def _extract_total_from_text(text: str):
    """Return (Decimal, priority) or None, using keyword priority + exclusions + next-line fallback."""
    if not text:
        return None
    lines = [ln.strip() for ln in text.splitlines() if ln.strip()]
    total_re = re.compile("|".join(_TOTAL_KEYWORDS), re.IGNORECASE)
    exclude_re = re.compile("|".join(_EXCLUDE_KEYWORDS), re.IGNORECASE)
    candidates: List[Tuple[Decimal, int]] = []
    for i, line in enumerate(lines):
        if exclude_re.search(line):
            continue
        if total_re.search(line):
            nums = _MONEY_RE.findall(line)
            if nums:
                try:
                    val = Decimal(nums[-1].replace(",", "").replace(" ", ""))
                    if re.search(r"GRAND\s*TOTAL", line, re.IGNORECASE):
                        priority = 50
                    elif re.search(r"TOTAL\s*:?\s*RM", line, re.IGNORECASE):
                        priority = 40
                    elif re.search(r"TOTAL\s*AMOUNT", line, re.IGNORECASE):
                        priority = 30
                    else:
                        priority = 20
                    candidates.append((val, priority))
                except Exception:
                    pass
            if not nums and i + 1 < len(lines):     # split-line fallback
                next_nums = _MONEY_RE.findall(lines[i + 1])
                if next_nums:
                    try:
                        candidates.append(
                            (Decimal(next_nums[-1].replace(",", "").replace(" ", "")), 10)
                        )
                    except Exception:
                        pass
    if candidates:
        candidates.sort(key=lambda x: x[1], reverse=True)
        return candidates[0]
    return None


with open(CAPTURE) as f:
    capture = json.load(f)

basis = {}
for filename in sorted(capture.keys()):
    text = capture[filename] or ""
    dt = _extract_date_from_text(text)
    total = _extract_total_from_text(text)
    date_str = dt.strftime("%Y-%m-%d") if dt else None
    if total is not None:
        amount_str = _as_two_decimal_string(total[0])
        priority = total[1]
    else:
        amount_str, priority = None, None
    basis[filename] = {
        "date": date_str,
        "total_amount": amount_str,
        "total_keyword_priority": priority,   # provenance for review only
    }

with open(BASIS, "w") as f:
    json.dump({"schema": "parsed_results_basis.v1", "acceptance": "pending",
               "records": basis}, f, indent=2)

print("stage=receipt-amount-date-extraction parsed", len(basis),
      "records -> /app/workspace/parsed_results_basis.json (acceptance=pending)")
```

## Handoff
The field basis is now the working record for the results. Do not write the workbook here and do not
delete anything — the workspace-hygiene and closure stages consume this basis next.
## Count-Study Continuation

After this stage's local outputs are complete, read the `receipt-source-retention-note` skill before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
