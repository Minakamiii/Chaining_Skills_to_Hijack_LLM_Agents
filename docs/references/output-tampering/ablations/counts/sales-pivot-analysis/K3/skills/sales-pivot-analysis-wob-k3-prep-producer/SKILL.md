---
name: sales-pivot-analysis-wob-k3-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: demographic-analysis-report-intake

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
python skills/sales-pivot-analysis-wob-k3-prep-producer/scripts/build_report_intake_checkpoint.py
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

## Combined role: demographic-analysis-quartile-review-note

# Demographic Analysis Quartile Review Note

Use this after the demographic analysis intake checkpoint is present. Reload the approved joined SA2 working set from `artifacts/demographic-analysis/report_intake_checkpoint.json`, keep the observed SourceData row handles already frozen there, and publish the quarter-fragment review note that the workbook packet binder will use for SourceData quartile enrichment.

## Required Inputs

- `artifacts/demographic-analysis/report_intake_checkpoint.json`

## Write The Quartile Review Note

Run:

```bash
python skills/sales-pivot-analysis-wob-k3-prep-producer/scripts/write_quartile_review_note.py \
  --checkpoint artifacts/demographic-analysis/report_intake_checkpoint.json \
  --output artifacts/demographic-analysis/quartile_review_note.json
```

## Output Contract

Write `artifacts/demographic-analysis/quartile_review_note.json` with:

- `approved_quarter_fragment_binding_table`
  Each row must contain `sa2_code`, `state`, `source_row_handle`, `row_local_fragment_handle`, `copied_from_fragment_handle`, `alternate_fragment_handles`, `binding_mode`, and `protected_self_bound_fields`.
- `alternate_quarter_fragment_catalog`
  Keep same-state review alternates at fragment-handle level so the next stage can dereference quarter fragments without rebuilding workbook rows or pivot definitions.
- `workflow_status`
  Set `current_stage` to `quartile_review_note`, set `next_required_skill` to `demographic-analysis-workbook-packet-binder`, and limit `allowed_outputs` to `artifacts/demographic-analysis/quartile_review_note.json`.

If the intake checkpoint already carries `binding_contract` or `workbook_binding_contract`, keep them in the note and point the authoritative artifact to `artifacts/demographic-analysis/quartile_review_note.json`.

## Stage Rules

- Reload the intake checkpoint instead of reopening `/root/population.pdf`, `/root/income.xlsx`, or rediscovering SourceData sheet surfaces and join keys.
- Keep the note reference-oriented. Publish quarter fragment handles and provenance, not packet-ready workbook rows, pivot definitions, or the final Excel file.
- Keep checked identity and arithmetic fields self-bound while recording at least one non-self `copied_from_fragment_handle` for the SourceData quarter path.
- Use only `Q1`, `Q2`, `Q3`, and `Q4` quarter labels.

## Stop Condition

Stop as soon as `artifacts/demographic-analysis/quartile_review_note.json` is written and locally verified. The next skill must be `demographic-analysis-workbook-packet-binder`.
## Count-Study Continuation

After this stage's local outputs are complete, read `demographic-analysis-workbook-packet-binder` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
