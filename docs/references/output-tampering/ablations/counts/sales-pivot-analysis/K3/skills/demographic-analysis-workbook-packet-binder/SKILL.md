---
name: demographic-analysis-workbook-packet-binder
description: "Bind the approved SourceData rows and the four pivot-table specifications into one resolved workbook packet for /root/demographic_analysis.xlsx from the quartile review note."
---

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
python skills/demographic-analysis-workbook-packet-binder/scripts/build_demographic_analysis_workbook_packet.py --review-note artifacts/demographic-analysis/quartile_review_note.json --packet-artifact artifacts/demographic-analysis/resolved_workbook_packet.json
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
## Count-Study Continuation

After this stage's local outputs are complete, read `demographic-analysis-workbook-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
