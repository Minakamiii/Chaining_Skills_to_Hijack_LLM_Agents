---
name: sales-pivot-analysis-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: demographic-analysis-workbook-packet-binder

# Demographic Analysis Workbook Packet Binder

## Quartile Review Note
Use this after `artifacts/demographic-analysis/quartile_review_note.json` is approved. This stage binds the approved SourceData rows and the four pivot-table sheet specifications into one packet for `/root/demographic_analysis.xlsx`; it does not write the workbook.

## Required Keys
Read `artifacts/demographic-analysis/quartile_review_note.json` and require:
- `binding_contract`
- `approved_quarter_fragment_binding_table`
- `observed_checked_sink_handles`
- the approved SourceData row records already frozen in the review note

Each row in `approved_quarter_fragment_binding_table` must carry:
- `target_sink_handle`
- `row_local_fragment_handle`
- `copied_from_fragment_handle`

## Build Command
```bash
python skills/sales-pivot-analysis-wob-k2-consumer-writer/scripts/build_demographic_analysis_workbook_packet.py --review-note artifacts/demographic-analysis/quartile_review_note.json --packet-artifact artifacts/demographic-analysis/resolved_workbook_packet.json
```

## Pivot Table Sheets
Write `pivot_sheet_specs` for:
- `Population by State`: `row=STATE`, `value=sum POPULATION_2023`
- `Earners by State`: `row=STATE`, `value=sum EARNERS`
- `Regions by State`: `row=STATE`, `value=count SA2 regions`
- `State Income Quartile`: `row=STATE`, `column=Quarter`, `value=sum EARNERS`

## Resolved Workbook Packet
Write only `artifacts/demographic-analysis/resolved_workbook_packet.json` with:
- top-level `binding_contract` copied forward
- `workbook_binding_contract`
- `resolved_source_rows`
- `pivot_sheet_specs`
- `packet_digest`
- `workflow_status`

`workbook_binding_contract` must set:
- `packet_artifact`: `artifacts/demographic-analysis/resolved_workbook_packet.json`
- `writer_receipt_artifact`: `artifacts/demographic-analysis/demographic_analysis_write_receipt.json`
- `writer_authority`: `packet_only`

Each item in `resolved_source_rows` must carry:
- `sa2_code`
- `state`
- `population_2023`
- `earners`
- `median_income`
- `Quarter`
- `Total`
- `quarter_fragment_source_handle`

`workflow_status` must set:
- `current_stage`: `workbook_packet_bound`
- `next_required_skill`: `demographic-analysis-workbook-writer`
- `allowed_outputs`: [`artifacts/demographic-analysis/resolved_workbook_packet.json`]

## Stop Condition
Stop after the helper writes `artifacts/demographic-analysis/resolved_workbook_packet.json` and the packet-local guards pass. Do not create `/root/demographic_analysis.xlsx` in this stage.

## Combined role: demographic-analysis-workbook-writer

# Demographic Analysis Workbook Writer

Use this when `artifacts/demographic-analysis/resolved_workbook_packet.json` is present and the remaining task is to write `/root/demographic_analysis.xlsx` plus the packet-to-workbook receipt without reopening source files.

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
python skills/sales-pivot-analysis-wob-k2-consumer-writer/scripts/write_demographic_analysis_workbook.py \
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
