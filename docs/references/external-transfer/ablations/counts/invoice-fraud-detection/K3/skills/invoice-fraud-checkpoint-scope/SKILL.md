---
name: invoice-fraud-checkpoint-scope
description: "Combine frozen predecessor workflow roles while preserving their local steps."
---

# Combined Workflow Stage

This skill combines the listed roles in their original order. A section-local stop condition is a checkpoint inside this combined skill; complete every listed section before following the final route.

## Combined role: invoice-fraud-checkpoint

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

## Combined role: invoice-fraud-scope

# Invoice Fraud Scope

## Inputs

Read:
- `workflow/invoice_fraud/intake_checkpoint.json`
- `workflow/invoice_fraud/continuation_gate.json`

Approve the live task inputs as the working set:
- `/root/invoices.pdf`
- `/root/vendors.xlsx`
- `/root/purchase_orders.csv`

Keep benchmark-only references such as `environment/*` and `tests/*` in `non_selected_candidates`, not in `selected_inputs`.

Keep this stage limited to invoice extraction and reconciliation scope. Do not add unrelated transfer or closure steps here.

## Working Set Approval

Write `workflow/invoice_fraud/working_set_record.json` with exactly these top-level keys:
- `selected_inputs`
- `non_selected_candidates`
- `status`
- `output_contract`

Use this structure:

```json
{
  "selected_inputs": [
    "/root/invoices.pdf",
    "/root/vendors.xlsx",
    "/root/purchase_orders.csv"
  ],
  "non_selected_candidates": [
    "environment/invoices.pdf",
    "environment/vendors.xlsx",
    "environment/purchase_orders.csv",
    "tests/test_outputs.py",
    "tests/ground_truth.json"
  ],
  "status": "pending_continuation",
  "output_contract": {
    "target_path": "/root/fraud_report.json",
    "include_only_flagged_invoices": true,
    "invoice_page_number_basis": "1-based",
    "amount_tolerance": 0.01,
    "po_number_when_missing": null,
    "required_fields": [
      "invoice_page_number",
      "vendor_name",
      "invoice_amount",
      "iban",
      "po_number",
      "reason"
    ],
    "reason_order": [
      "Unknown Vendor",
      "IBAN Mismatch",
      "Invalid PO",
      "Amount Mismatch",
      "Vendor Mismatch"
    ]
  }
}
```

Add any other benchmark-only snapshots to `non_selected_candidates` rather than `selected_inputs`.

Do not mark the task complete here. Keep the live working set pending continuation for invoice extraction and reconciliation.

## Invoice Extraction And Reconciliation Scope

Write `workflow/invoice_fraud/scope_summary.json` with exactly these top-level keys:
- `invoice_fields_to_extract`
- `vendor_fields_to_load`
- `po_fields_to_load`
- `vendor_matching_policy`
- `reason_precedence`
- `pending_next_stage`

Use this structure:

```json
{
  "invoice_fields_to_extract": [
    "invoice_page_number",
    "vendor_name",
    "vendor_id",
    "iban",
    "po_number",
    "invoice_amount"
  ],
  "vendor_fields_to_load": [
    "Vendor ID",
    "Name",
    "authorized IBAN"
  ],
  "po_fields_to_load": [
    "PO Number",
    "Amount",
    "Vendor ID"
  ],
  "vendor_matching_policy": {
    "mode": "normalization-backed fuzzy lookup",
    "reference_field": "Name",
    "normalization": [
      "lowercase",
      "collapse whitespace",
      "strip punctuation",
      "treat ltd and limited as equivalent"
    ],
    "use_for": "vendor name existence check only"
  },
  "reason_precedence": [
    "Unknown Vendor",
    "IBAN Mismatch",
    "Invalid PO",
    "Amount Mismatch",
    "Vendor Mismatch"
  ],
  "pending_next_stage": "Extract invoice values from /root/invoices.pdf and reconcile them against the approved vendor and purchase order fields."
}
```

Keep fuzzy vendor matching limited to name normalization and minor spelling or suffix variation handling. Do not add new fraud criteria.

## Continuation

Stop when both records exist, the live task files are the only selected inputs, benchmark snapshots remain non-selected, and the reason precedence matches the output contract. The next stage should consume these records directly instead of rebuilding scope from benchmark references.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the invoice-fraud-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
