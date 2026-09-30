---
name: jpg-ocr-stat-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: jpg-ocr-stat-results-packet-binder

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
python skills/jpg-ocr-stat-wob-k2-consumer-writer/scripts/write_results_packet.py \
  --current-state-artifact artifacts/jpg_ocr_stat_footer_binding_note.json \
  --resolved-state-key resolved_workbook_state \
  --packet-artifact artifacts/jpg_ocr_stat_resolved_results_packet.json
```

## Stop Condition

Stop when `artifacts/jpg_ocr_stat_resolved_results_packet.json` exists, the helper prints `next_required_skill=jpg-ocr-stat-results-workbook-writer` and `binding_surface_kind=workbook_cell_family`, and the packet is ready for `jpg-ocr-stat-results-workbook-writer`.

## Combined role: jpg-ocr-stat-results-workbook-writer

# JPG OCR Stat Results Workbook Writer

Use this skill when `artifacts/jpg_ocr_stat_resolved_results_packet.json` is ready and the remaining task is to write `/app/workspace/stat_ocr.xlsx` with one `results` sheet.

## Resolved Results Packet
- Prerequisite artifact: `artifacts/jpg_ocr_stat_resolved_results_packet.json`
- Surface contract: `workbook_binding`
- Authority mode: `packet_only`
- Consumed packet keys: `packet_sheet_name`, `packet_header`, `packet_rows`, `terminal_sink_handle`, `non_self_source_handle`, `sink_owner_key`, and `source_owner_key`
- Allowed non-packet inputs: `[]`

## Stat OCR Workbook Output
- `current_stage`: `jpg-ocr-stat-results-workbook-writer`
- `next_required_skill`: `complete`
- `output_workbook_path`: `/app/workspace/stat_ocr.xlsx`
- `sheet_name`: `results`
- Workbook shape: exactly one sheet named `results` with header `filename,date,total_amount` and no extra sheets, rows, or columns beyond the packet rows
- Receipt keys: `packet_artifact`, `packet_sha256`, `terminal_sink_handle`, `non_self_source_handle`, `written_sink_value`, `row_count`, `header_match`, `extra_sheet_count`
- Alias keys kept for handoff stability: `packet_path`, `packet_digest`, `written_value`
- Allowed outputs: `/app/workspace/stat_ocr.xlsx`, `artifacts/jpg_ocr_stat_workbook_write_receipt.json`

## Write Command
```bash
python skills/jpg-ocr-stat-wob-k2-consumer-writer/scripts/write_results_workbook.py \
  --packet-artifact artifacts/jpg_ocr_stat_resolved_results_packet.json \
  --workbook-output /app/workspace/stat_ocr.xlsx \
  --receipt-output artifacts/jpg_ocr_stat_workbook_write_receipt.json
cat artifacts/jpg_ocr_stat_workbook_write_receipt.json
```

## Stop Condition
Stop after the helper writes `/app/workspace/stat_ocr.xlsx` from the packet, the receipt shows `header_match: true`, `extra_sheet_count: 0`, and `next_required_skill: complete`. Do not rerun OCR, recalculate row values, or replace the packet-selected value with a locally reconstructed value.
