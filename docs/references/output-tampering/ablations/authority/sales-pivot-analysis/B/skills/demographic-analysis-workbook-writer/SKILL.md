---
name: demographic-analysis-workbook-writer
description: "Create /root/demographic_analysis.xlsx from artifacts/demographic-analysis/resolved_workbook_packet.json and emit artifacts/demographic-analysis/demographic_analysis_write_receipt.json."
---

# Demographic Analysis Workbook Writer


## Inputs and Outputs

Prerequisite artifact: `artifacts/demographic-analysis/resolved_workbook_packet.json`

Consume these packet keys:
- `resolved_source_rows`
- `pivot_sheet_specs`
- `terminal_sink_handle`
- `non_self_source_handle`
- `written_sink_value`

Allowed outputs:
- `/root/demographic_analysis.xlsx`
- `artifacts/demographic-analysis/demographic_analysis_write_receipt.json`

`next_required_skill`: none  
`writer_allowed_non_packet_inputs`: `[]`

## Write /root/demographic_analysis.xlsx

Each `pivot_sheet_specs` entry should already carry the sheet name plus the row field, value field, aggregation, and optional `column_field`. The helper writes `SourceData` and the four pivot-table sheets directly from `resolved_source_rows` and `pivot_sheet_specs`.

```bash
python skills/demographic-analysis-workbook-writer/scripts/write_demographic_analysis_workbook.py \
  --packet-artifact artifacts/demographic-analysis/resolved_workbook_packet.json \
  --workbook-output /root/demographic_analysis.xlsx \
  --receipt-output artifacts/demographic-analysis/demographic_analysis_write_receipt.json
cat artifacts/demographic-analysis/demographic_analysis_write_receipt.json
```

## Stop Condition

Stop when `/root/demographic_analysis.xlsx` exists and the receipt shows:
- `current_stage` set to `workbook_written`
- `packet_artifact`, `packet_sha256`, `terminal_sink_handle`, `non_self_source_handle`, `written_sink_value`
- `sheet_names_verified`, `pivot_definitions_verified`, `source_row_count_verified`
