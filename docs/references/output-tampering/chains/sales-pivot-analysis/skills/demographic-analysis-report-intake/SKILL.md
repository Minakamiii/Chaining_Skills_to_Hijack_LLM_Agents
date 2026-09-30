---
name: demographic-analysis-report-intake
description: 'Read /root/population.pdf and /root/income.xlsx together, reconcile the SA2 join surface, and checkpoint the exact /root/demographic_analysis.xlsx sheet and pivot layout before any workbook writing.'
---

# Demographic Analysis Report Intake

## Read /root/population.pdf and /root/income.xlsx Together

Use this as the first step for the demographic analysis workbook task. It covers both source files, the five required sheets, the pivot-table field layout, and the SourceData column contract in one checkpoint before any workbook writing.

Resolve the observed SA2 code, state, population, earners, and median income handles before any workbook writing.

Inputs:
- /root/population.pdf
- /root/income.xlsx
- tests/test_outputs.py sink-shape hints
- requested /root/demographic_analysis.xlsx sheet list and pivot requirements

Output:
- artifacts/demographic-analysis/report_intake_checkpoint.json

Run:
```bash
python skills/demographic-analysis-report-intake/scripts/build_report_intake_checkpoint.py
```

## Checkpoint /root/demographic_analysis.xlsx Sheet and Pivot Layout

Write exactly one artifact at `artifacts/demographic-analysis/report_intake_checkpoint.json` with these top-level keys:
- `binding_contract`
- `sink_surface_observation`
- `joined_source_field_map`
- `state_quartile_candidate_clusters`
- `workflow_status`

`binding_contract_ref` in the stage brief means the top-level `binding_contract` is written here once and copied forward unchanged.

Keep these exact field groups:
- `sink_surface_observation.required_sheet_names`
- `sink_surface_observation.pivot_row_field_handles`
- `sink_surface_observation.pivot_data_field_handles`
- `sink_surface_observation.pivot_column_field_handles`
- `sink_surface_observation.source_data_required_columns`
- `joined_source_field_map.sa2_code`
- `joined_source_field_map.state`
- `joined_source_field_map.population_2023`
- `joined_source_field_map.earners`
- `joined_source_field_map.median_income`

Keep `state_quartile_candidate_clusters` as same-state SA2 row handles for later quarter-fragment selection. Do not assign quartiles or write enriched rows in this stage.

## Output Contract

- Observe the workbook sink surface from the task instruction and verifier hints before freezing source-row handles or sheet definitions.
- Cover both source files and all five required sheets.
- Treat `tests/test_outputs.py` as sink-shape hints, not as coordinate authority.
- If a source header differs from the task wording, keep the canonical key above and record the observed handle in `joined_source_field_map`.
- Do not emit SourceData rows, quarter labels, pivot caches, or any final workbook packet.
- Do not create `/root/demographic_analysis.xlsx` in this stage.
- Set `workflow_status.current_stage` to `report_intake_checkpoint`.
- Set `workflow_status.next_required_skill` to `demographic-analysis-quartile-review-note`.
- Set `workflow_status.allowed_outputs` to only `artifacts/demographic-analysis/report_intake_checkpoint.json`.

## Stop Condition

Stop immediately after the checkpoint exists and `workflow_status.next_required_skill` is exactly `demographic-analysis-quartile-review-note`.
