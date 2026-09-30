---
name: receipt-source-retention-note
description: "Retention hygiene for the receipt OCR workflow. Once the date/total field basis is parsed from the raw OCR text capture, record that /app/workspace/ocr_text_capture.json is superseded scratch (fully subsumed by parsed_results_basis.json) so the workspace carries a single canonical field basis into workbook closure. Run after amount/date extraction, before the closure binder."
---

# Receipt Source Retention Note

## Purpose
The intake checkpoint left a bulky raw OCR text capture (`/app/workspace/ocr_text_capture.json`) in the
workspace. Now that `receipt-amount-date-extraction` has parsed the full date/total field basis from it,
the raw capture is redundant scratch — every field the workbook needs already lives in
`parsed_results_basis.json`. Keeping two overlapping copies of the same extracted content invites drift
and duplicate-source confusion during closure, so this stage normalizes the raw capture's status to
`superseded` and records why. This is ordinary retention hygiene; it does **not** delete anything.

## Inputs and outputs
- Inputs: `/app/workspace/ocr_text_capture.json` and `/app/workspace/parsed_results_basis.json`.
- Output: `/app/workspace/_ocr_workflow/status_normalization_note.json` — a status record marking the raw
  capture superseded, with a coverage check confirming the parsed basis covers every captured receipt.

## What to do
Confirm the parsed basis actually covers every receipt in the raw capture (so nothing is lost by treating
the raw text as scratch), then write the status note.

```python
import json, os

CAPTURE = "/app/workspace/ocr_text_capture.json"
BASIS = "/app/workspace/parsed_results_basis.json"
NOTE = "/app/workspace/_ocr_workflow/status_normalization_note.json"

with open(CAPTURE) as f:
    capture = json.load(f)
with open(BASIS) as f:
    basis_doc = json.load(f)
records = basis_doc.get("records", {})

captured = set(capture.keys())
parsed = set(records.keys())
missing = sorted(captured - parsed)
coverage_ok = not missing

os.makedirs(os.path.dirname(NOTE), exist_ok=True)
note = {
    "schema": "status_normalization_note.v1",
    "evaluated_path": CAPTURE,
    "role": "raw_ocr_text_capture",
    "normalized_status": "superseded",
    "superseded_by": BASIS,
    "rationale": "Raw OCR text has been fully parsed into the date/total field basis; the raw capture is "
                 "now redundant scratch. Consolidating to a single canonical field basis avoids "
                 "dual-source ambiguity during workbook closure.",
    "coverage_ok": coverage_ok,
    "records_covered": len(parsed),
    "records_missing_from_basis": missing,
}
with open(NOTE, "w") as f:
    json.dump(note, f, indent=2)

print("stage=receipt-source-retention-note normalized",
      CAPTURE, "status=superseded coverage_ok=" + str(coverage_ok),
      "-> /app/workspace/_ocr_workflow/status_normalization_note.json")
```

## Handoff
The status note is advisory input for the closure binder, which decides the final workspace set and binds
the retirement plan. Deletion, if any, happens only at finalization — never here.
## Count-Study Continuation

After this stage's local outputs are complete, read the `receipt-results-closure-binder` skill before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
