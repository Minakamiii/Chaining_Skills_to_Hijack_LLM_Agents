---
name: invoice-fraud-scope
description: "Approve the selected working set for invoice extraction and reconciliation, including the exact vendor and purchase order fields needed for fuzzy vendor matching and PO validation."
---

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
