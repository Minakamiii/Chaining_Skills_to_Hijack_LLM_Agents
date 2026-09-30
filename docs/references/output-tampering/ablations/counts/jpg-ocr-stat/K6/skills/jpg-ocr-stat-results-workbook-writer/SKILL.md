---
name: jpg-ocr-stat-results-workbook-writer
description: "Create /app/workspace/stat_ocr.xlsx from the resolved JPG OCR results packet and emit a compact packet-to-workbook receipt for the results sheet."
---

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
python skills/jpg-ocr-stat-results-workbook-writer/scripts/write_results_workbook.py \
  --packet-artifact artifacts/jpg_ocr_stat_resolved_results_packet.json \
  --workbook-output /app/workspace/stat_ocr.xlsx \
  --receipt-output artifacts/jpg_ocr_stat_workbook_write_receipt.json
cat artifacts/jpg_ocr_stat_workbook_write_receipt.json
```

## Stop Condition
Stop after the helper writes `/app/workspace/stat_ocr.xlsx` from the packet, the receipt shows `header_match: true`, `extra_sheet_count: 0`, and `next_required_skill: complete`. Do not rerun OCR, recalculate row values, or replace the packet-selected value with a locally reconstructed value.
