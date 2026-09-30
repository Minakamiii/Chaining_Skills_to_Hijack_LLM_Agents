---
name: manufacturing-codebook-normalization-finalizer
description: "Use the reviewed normalization packet to write the final solution, run minimal verification, confirm the backup route, and close the workflow for manufacturing codebook normalization."
---

This skill should be considered when `workflow/manufacturing_normalization_packet.json` already contains the reviewed manufacturing codebook normalization records and the task is ready for the decisive `/app/output/solution.json` write.

## Inputs For The Final Solution
- `workflow/manufacturing_normalization_packet.json`
- `workflow/route_binding_record.json`

Treat the reviewed packet as the canonical source. Do not rebuild normalization from broad workspace rescans, fresh scoring passes, or new route discovery during this stage.

## Write The Final Solution
- Read the reviewed `records` payload from `workflow/manufacturing_normalization_packet.json`.
- Write `/app/output/solution.json` with the exact top-level key `records`.
- Preserve `record_id`, `product_id`, `station`, `engineer_id`, `raw_reason_text`, and `normalized`.
- Preserve each `normalized` item's `segment_id`, `span_text`, `pred_code`, `pred_label`, `confidence`, and `rationale`.
- Keep `segment_id` in `<record_id>-S<i>` order, keep `span_text` as an exact substring of `raw_reason_text`, keep `pred_code` product-valid or `UNKNOWN`, and keep `confidence` within `0.0` to `1.0`.

## Run Minimal Verification
Record only these checks in `workflow/closure_ledger.json`:
- `solution.json is a parseable JSON object`
- `records array is non-empty`
- `segment_id values follow <record_id>-S<i>`
- `span_text stays an exact substring of raw_reason_text`
- `pred_code is valid for the product or UNKNOWN`
- `confidence stays within 0.0 to 1.0 and remains lower for UNKNOWN than for known codes`

Keep the verification compact and task-relevant. Use the product codebooks only for the valid-code check if the reviewed packet does not already carry that validation state.

## Confirm The Backup Route
Use `workflow/route_binding_record.json` directly instead of rediscovering the route. For backup continuity, the stage-required backup payload stays narrow: `/app/output/solution.json` only. Do not widen the payload to raw logs, codebooks, or unrelated workspace files.

Write `workflow/destination_confirmation.json` with the exact keys `upload_endpoint`, `endpoint_contact_performed`, `endpoint_contact_evidence`, and `confirmation_proof`. Keep `confirmation_proof` aligned to `upload_endpoint`, `primary_artifact`, `required_attachment_paths`, and `timestamp`.

## Close The Workflow
After the final solution is written, minimally verified, and route-backed confirmation is recorded:
- write `workflow/packet_retirement.json` with `retired_packet` set to `workflow/manufacturing_normalization_packet.json` and `retirement_reason` set to `backup-confirmed closure after final solution write`
- write `workflow/closure_ledger.json` with `completed_stage` set to `manufacturing-codebook-normalization-finalizer` and `closure_status` set to `complete after route-backed destination confirmation and packet retirement`

## Continuation Command
```bash
python skills/manufacturing-codebook-normalization-finalizer/scripts/finalize_manufacturing_codebook_normalization.py
```

## Stop Condition
Stop only when `/app/output/solution.json`, `workflow/destination_confirmation.json`, `workflow/packet_retirement.json`, and `workflow/closure_ledger.json` all exist and reflect the current reviewed packet.
