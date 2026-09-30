---
name: jpg-ocr-stat-results-packet-binder
description: "Reload the approved receipt binding note and materialize one ordered `results` packet for `/app/workspace/stat_ocr.xlsx` that the workbook writer can copy directly."
---

# JPG OCR Stat Results Packet Binder

## Receipt Binding Note Input

Use this stage after `artifacts/jpg_ocr_stat_footer_binding_note.json` exists. The note must already contain `resolved_workbook_state`. This stage copies that sealed workbook state into one writer-ready packet instead of re-running OCR, rescanning `/app/workspace/dataset/img`, or re-deriving the `results` sheet layout.

Consumed from `resolved_workbook_state`:
- `packet_sheet_name`
- `packet_header`
- `packet_rows`
- `designated_non_self_binding_row_handle`
- `packet_digest_basis`

If the note is missing or malformed, stop here rather than rebuilding rows from the receipt images.

## Results Packet Output

Write exactly one primary artifact:
- `artifacts/jpg_ocr_stat_resolved_results_packet.json`

The packet must:
- keep `packet_sheet_name` as `results`
- keep `packet_header` as `["filename", "date", "total_amount"]`
- keep `packet_rows` in the filename order already sealed in `resolved_workbook_state`
- keep each `date` and `total_amount` exactly as resolved, including `null` when extraction failed
- publish `current_stage`, `next_required_skill`, `binding_surface_kind`, and `allowed_outputs` inside the same packet
- keep the designated row handle and digest basis inside the same packet artifact

This stage does not reopen receipt images, rediscover workbook layout, infer formula families, or select a new amount source.

## Command

```bash
python skills/jpg-ocr-stat-results-packet-binder/scripts/write_results_packet.py \
  --current-state-artifact artifacts/jpg_ocr_stat_footer_binding_note.json \
  --resolved-state-key resolved_workbook_state \
  --packet-artifact artifacts/jpg_ocr_stat_resolved_results_packet.json
```

## Stop Condition

Stop when `artifacts/jpg_ocr_stat_resolved_results_packet.json` exists, the helper prints `next_required_skill=jpg-ocr-stat-results-workbook-writer` and `binding_surface_kind=workbook_cell_family`, and the packet is ready for `jpg-ocr-stat-results-workbook-writer`.
