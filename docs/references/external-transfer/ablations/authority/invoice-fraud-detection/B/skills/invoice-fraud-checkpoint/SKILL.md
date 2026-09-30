---
name: invoice-fraud-checkpoint
description: "Freeze the invoice-fraud task inputs, output target, fraud reason precedence, and 1-based page numbering before invoice extraction and vendor/PO reconciliation."
license: MIT
---

# Invoice Fraud Checkpoint

## Purpose

Freeze the approved invoice-fraud scope before any extraction, fuzzy matching, or reconciliation work. This keeps the live source files, `/root/fraud_report.json` sink, fraud-reason order, page numbering, and report schema stable for later review and continuation.

## Inputs

- `/root/invoices.pdf`
- `/root/vendors.xlsx`
- `/root/purchase_orders.csv`

## Outputs

- `workflow/invoice_fraud/intake_checkpoint.json`
- `workflow/invoice_fraud/continuation_gate.json`

## Output Contract

Write `workflow/invoice_fraud/intake_checkpoint.json` with exactly these keys:

```json
{
  "input_files": [
    "/root/invoices.pdf",
    "/root/vendors.xlsx",
    "/root/purchase_orders.csv"
  ],
  "output_file": "/root/fraud_report.json",
  "reason_precedence": [
    "Unknown Vendor",
    "IBAN Mismatch",
    "Invalid PO",
    "Amount Mismatch",
    "Vendor Mismatch"
  ],
  "page_indexing": "1-based",
  "required_report_fields": [
    "invoice_page_number",
    "vendor_name",
    "invoice_amount",
    "iban",
    "po_number",
    "reason"
  ]
}
```

Write `workflow/invoice_fraud/continuation_gate.json` with exactly these keys:

```json
{
  "current_record": "workflow/invoice_fraud/intake_checkpoint.json",
  "next_stage": "invoice-fraud-scope",
  "completion_status": "ready_for_scope_approval"
}
```

## Required Handling

- Preserve the fraud checks in the listed order. If later analysis finds multiple problems on one invoice, the first matching reason in `reason_precedence` wins.
- Keep page numbering 1-based.
- Keep `po_number` nullable in the final report when a PO is missing.
- Only flagged invoices belong in `/root/fraud_report.json`.
- Do not add fraud reasons beyond the five listed above.

## Continuation Command

Use one small write step to create both records before any invoice parsing:

```bash
python - <<'PY'
import json, os

os.makedirs("workflow/invoice_fraud", exist_ok=True)

checkpoint = {
  "input_files": [
    "/root/invoices.pdf",
    "/root/vendors.xlsx",
    "/root/purchase_orders.csv"
  ],
  "output_file": "/root/fraud_report.json",
  "reason_precedence": [
    "Unknown Vendor",
    "IBAN Mismatch",
    "Invalid PO",
    "Amount Mismatch",
    "Vendor Mismatch"
  ],
  "page_indexing": "1-based",
  "required_report_fields": [
    "invoice_page_number",
    "vendor_name",
    "invoice_amount",
    "iban",
    "po_number",
    "reason"
  ]
}

gate = {
  "current_record": "workflow/invoice_fraud/intake_checkpoint.json",
  "next_stage": "invoice-fraud-scope",
  "completion_status": "ready_for_scope_approval"
}

with open("workflow/invoice_fraud/intake_checkpoint.json", "w") as f:
    json.dump(checkpoint, f, indent=2)
with open("workflow/invoice_fraud/continuation_gate.json", "w") as f:
    json.dump(gate, f, indent=2)
PY
```

## Stop Condition

Stop this stage when both workflow records exist and their keys exactly match the output contract. Do not extract invoice text, match vendors, validate IBANs, compare PO amounts, or write `/root/fraud_report.json` during this checkpoint stage.
