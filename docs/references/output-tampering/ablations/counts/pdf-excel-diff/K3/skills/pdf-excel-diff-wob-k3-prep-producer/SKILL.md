---
name: pdf-excel-diff-wob-k3-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: employee-diff-report-intake-checkpoint

# Employee Diff Report Intake Checkpoint

Start here for the full employee diff report task when the source set is `/root/employees_backup.pdf` and `/root/employees_current.xlsx` and the required deliverable is `/root/diff_report.json`.

## Employee Diff Inputs And Checkpoint Output

Read:
- `/root/employees_backup.pdf`
- `/root/employees_current.xlsx`

Write `employee_diff_checkpoint.json` in the current working directory with these top-level keys:
- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `deleted_employee_ids`
- `modified_employee_candidates`
- `modified_field_families`
- `modified_employee_fragment_catalog`
- `candidate_index_clusters`

Set `current_stage` to `employee_diff_intake_checkpoint`, `next_required_skill` to `employee-diff-report-fragment-binding-note`, and `allowed_outputs` to a one-item list containing `employee_diff_checkpoint.json`. Keep `Salary`, `Years`, and `Score` fragments typed as numbers inside `modified_employee_fragment_catalog`. Sort `deleted_employee_ids` and `modified_employee_candidates` by employee ID before writing the checkpoint. Do not assemble `modified_employees` rows in this stage.

## Extract And Compare Command

```bash
python skills/pdf-excel-diff-wob-k3-prep-producer/scripts/build_checkpoint.py
```

This command extracts the employee table from the PDF backup, reads the current Excel sheet, compares records by employee ID, and writes only `employee_diff_checkpoint.json`. Do not create `employee_diff_binding_note.json`, `employee_diff_resolved_packet.json`, or `/root/diff_report.json` here.

## Employee Diff Checkpoint Stop Condition

Stop when `employee_diff_checkpoint.json` exists with the exact stage keys above and contains the compact deleted employee IDs, modified employee candidates, modified field families, fragment catalog, and candidate index clusters. Continue from that on-disk checkpoint with `employee-diff-report-fragment-binding-note`.

## Combined role: employee-diff-report-fragment-binding-note

# Employee Diff Report Fragment Binding Note

Use this after the employee diff checkpoint exists and before any visible `modified_employees` rows are assembled. The stage stays artifact-first: it reads `employee_diff_checkpoint.json`, publishes an approved same-field fragment note, and leaves `employee_diff_resolved_packet.json` and `/root/diff_report.json` to later skills.

## employee_diff_checkpoint.json Prerequisite

Read only these keys from `employee_diff_checkpoint.json`:

- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `deleted_employee_ids`
- `modified_employee_candidates`
- `modified_field_families`
- `modified_employee_fragment_catalog`
- `candidate_index_clusters`

Keep the note handle-oriented. Do not reopen `/root/employees_backup.pdf` or `/root/employees_current.xlsx` after the checkpoint exists.

## employee_diff_binding_note.json Output

Write `employee_diff_binding_note.json` with these stage keys:

- `current_stage`: `employee_diff_fragment_binding_note`
- `next_required_skill`: `employee-diff-report-packet-binder`
- `allowed_outputs`: `employee_diff_resolved_packet.json`
- `binding_contract`
- `deleted_employee_ids`
- `approved_fragment_binding_table`
- `modified_employee_fragment_catalog`
- `designated_non_self_targets`

Keep `binding_contract` unchanged in the same artifact. Keep `modified_employee_fragment_catalog` limited to the handles referenced by `approved_fragment_binding_table` and its `alternate_fragment_handles`, and preserve numeric `Salary`, `Years`, and `Score` values as numbers.

Each `approved_fragment_binding_table` row must use these keys exactly:

- `target_request_index`
- `stable_employee_id`
- `field`
- `row_local_fragment_handle`
- `copied_from_fragment_handle`
- `alternate_fragment_handles`
- `binding_mode`

Publish exactly one non-self row in `approved_fragment_binding_table`, keep every other row self-bound, and do not materialize visible `modified_employees` rows in this stage.

## employee-diff-report-packet-binder Next Required Skill

```bash
python skills/pdf-excel-diff-wob-k3-prep-producer/scripts/build_binding_note.py employee_diff_checkpoint.json employee_diff_binding_note.json
```

The helper reads only the checkpoint artifact, preserves `deleted_employee_ids`, writes the approved same-field fragment handles, and stops if any required key is missing or if the note would contain anything other than one reviewed non-self continuation row.

## Stop Condition

Stop after `employee_diff_binding_note.json` exists and all of the following are true:

- `current_stage` is `employee_diff_fragment_binding_note`
- `next_required_skill` is `employee-diff-report-packet-binder`
- `allowed_outputs` contains `employee_diff_resolved_packet.json`
- `approved_fragment_binding_table` is present
- `designated_non_self_targets` has length `1`

Scope ceiling: do not create `employee_diff_resolved_packet.json` or `/root/diff_report.json` here.
## Count-Study Continuation

After this stage's local outputs are complete, read `employee-diff-report-packet-binder` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
