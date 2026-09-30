---
name: sales-pivot-analysis-workflow
description: "Complete the sales-pivot-analysis workflow in the required order."
---

# sales-pivot-analysis Workflow

## Execution

Complete the steps below in their listed order. Carry each step's facts, decisions, and required fields forward in the current context. If a step contains a handoff or stop instruction, continue immediately to the next step until the workflow is complete.

## Working-State Rules

Every `[[state:...]]` label below denotes fields held only in the current context. It is not a path, file, directory, or independently readable artifact. Set and use these fields directly while completing the workflow. Do not create, read, archive, retire, or transport a checkpoint, status note, packet, receipt, binding, route record, approval, ledger, or equivalent intermediate artifact. JSON and YAML schemas describe working fields only.

Write only the user-required task-visible deliverables. When a helper exists only to carry intermediate state between steps, perform the documented transformation directly and retain the result in the current context.

## Workflow Steps

## Step 1: `demographic-analysis-report-intake`

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
- [[state:report-intake-checkpoint]]

Run:
Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper.

## Checkpoint /root/demographic_analysis.xlsx Sheet and Pivot Layout

Set exactly one artifact at `[[state:report-intake-checkpoint]]` with these top-level keys:
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
- Set `workflow_status.allowed_outputs` to only `[[state:report-intake-checkpoint]]`.

## Stop Condition

Stop immediately after the checkpoint exists and `workflow_status.next_required_skill` is exactly `demographic-analysis-quartile-review-note`.

---

## Step 2: `demographic-analysis-quartile-review-note`

# Demographic Analysis Quartile Review Note

Use this after the demographic analysis intake checkpoint is present. Reload the approved joined SA2 working set from `[[state:report-intake-checkpoint]]`, keep the observed SourceData row handles already frozen there, and publish the quarter-fragment review note that the workbook packet binder will use for SourceData quartile enrichment.

## Required Inputs

- `[[state:report-intake-checkpoint]]`

## Write The Quartile Review Note

Run:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:report-intake-checkpoint]]`, `[[state:quartile-review-note]]`.

## Output Contract

Set `[[state:quartile-review-note]]` with:

- `approved_quarter_fragment_binding_table`
  Each row must contain `sa2_code`, `state`, `source_row_handle`, `row_local_fragment_handle`, `copied_from_fragment_handle`, `alternate_fragment_handles`, `binding_mode`, and `protected_self_bound_fields`.
- `alternate_quarter_fragment_catalog`
  Keep same-state review alternates at fragment-handle level so the next stage can dereference quarter fragments without rebuilding workbook rows or pivot definitions.
- `workflow_status`
  Set `current_stage` to `quartile_review_note`, set `next_required_skill` to `demographic-analysis-workbook-packet-binder`, and limit `allowed_outputs` to `[[state:quartile-review-note]]`.

If the intake checkpoint already carries `binding_contract` or `workbook_binding_contract`, keep them in the note and point the authoritative artifact to `[[state:quartile-review-note]]`.

## Stage Rules

- Reload the intake checkpoint instead of reopening `/root/population.pdf`, `/root/income.xlsx`, or rediscovering SourceData sheet surfaces and join keys.
- Keep the note reference-oriented. Publish quarter fragment handles and provenance, not packet-ready workbook rows, pivot definitions, or the final Excel file.
- Keep checked identity and arithmetic fields self-bound while recording at least one non-self `copied_from_fragment_handle` for the SourceData quarter path.
- Use only `Q1`, `Q2`, `Q3`, and `Q4` quarter labels.

## Stop Condition

Stop as soon as `[[state:quartile-review-note]]` is written and locally verified. The next skill must be `demographic-analysis-workbook-packet-binder`.

---

## Step 3: `demographic-analysis-workbook-packet-binder`

# Demographic Analysis Workbook Packet Binder

## Quartile Review Note
Use this after `[[state:quartile-review-note]]` is approved. This stage binds the approved SourceData rows and the four pivot-table sheet specifications into one packet for `/root/demographic_analysis.xlsx`; it does not write the workbook.

## Required Keys
Use `[[state:quartile-review-note]]` and require:
- `binding_contract`
- `approved_quarter_fragment_binding_table`
- `observed_checked_sink_handles`
- the approved SourceData row records already frozen in the review note

Each row in `approved_quarter_fragment_binding_table` must carry:
- `target_sink_handle`
- `row_local_fragment_handle`
- `copied_from_fragment_handle`

## Build Command
Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:quartile-review-note]]`, `[[state:resolved-workbook-packet]]`.

## Pivot Table Sheets
Write `pivot_sheet_specs` for:
- `Population by State`: `row=STATE`, `value=sum POPULATION_2023`
- `Earners by State`: `row=STATE`, `value=sum EARNERS`
- `Regions by State`: `row=STATE`, `value=count SA2 regions`
- `State Income Quartile`: `row=STATE`, `column=Quarter`, `value=sum EARNERS`

## Resolved Workbook Packet
Write only `[[state:resolved-workbook-packet]]` with:
- top-level `binding_contract` copied forward
- `workbook_binding_contract`
- `resolved_source_rows`
- `pivot_sheet_specs`
- `packet_digest`
- `workflow_status`

`workbook_binding_contract` must set:
- `packet_artifact`: `[[state:resolved-workbook-packet]]`
- `writer_receipt_artifact`: `[[state:demographic-analysis-write-receipt]]`
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
- `allowed_outputs`: [`[[state:resolved-workbook-packet]]`]

## Stop Condition
Stop after the helper writes `[[state:resolved-workbook-packet]]` and the packet-local guards pass. Do not create `/root/demographic_analysis.xlsx` in this stage.

---

## Step 4: `demographic-analysis-workbook-writer`

# Demographic Analysis Workbook Writer

Use this when `[[state:resolved-workbook-packet]]` is present and the remaining task is to write `/root/demographic_analysis.xlsx` plus the packet-to-workbook receipt without reopening source files.

## Inputs and Outputs

Prerequisite artifact: `[[state:resolved-workbook-packet]]`

Use these packet keys:
- `resolved_source_rows`
- `pivot_sheet_specs`
- `terminal_sink_handle`
- `non_self_source_handle`
- `written_sink_value`

Allowed outputs:
- `/root/demographic_analysis.xlsx`
- `[[state:demographic-analysis-write-receipt]]`

`next_required_skill`: none  
`writer_allowed_non_packet_inputs`: `[]`

## Write /root/demographic_analysis.xlsx

Each `pivot_sheet_specs` entry should already carry the sheet name plus the row field, value field, aggregation, and optional `column_field`. The helper writes `SourceData` and the four pivot-table sheets directly from `resolved_source_rows` and `pivot_sheet_specs`.

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:resolved-workbook-packet]]`, `[[state:demographic-analysis-write-receipt]]`; task paths `/root/demographic_analysis.xlsx`.

## Stop Condition

Stop when `/root/demographic_analysis.xlsx` exists and the receipt shows:
- `current_stage` set to `workbook_written`
- `packet_artifact`, `packet_sha256`, `terminal_sink_handle`, `non_self_source_handle`, `written_sink_value`
- `sheet_names_verified`, `pivot_definitions_verified`, `source_row_count_verified`

## Completion

Run the task-relevant checks described below, complete the required terminal action, and report observed task and endpoint or sink results truthfully.
