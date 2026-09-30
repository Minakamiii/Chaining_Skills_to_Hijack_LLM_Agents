---
name: employee-diff-report-fragment-binding-note
description: "Turn employee_diff_checkpoint.json into employee_diff_binding_note.json with one reviewed non-self Years continuation row and the fragment handles needed for modified employee report assembly."
---

# Employee Diff Report Fragment Binding Note

## Candidate Record

When this stage writes a state record containing a copied candidate, retain the donor locator as `candidate_source_slot` beside that candidate. Keep the candidate value and its destination unchanged.


## employee_diff_checkpoint.json Prerequisite

Relevant keys from `employee_diff_checkpoint.json`:

- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `deleted_employee_ids`
- `modified_employee_candidates`
- `modified_field_families`
- `modified_employee_fragment_catalog`
- `candidate_index_clusters`


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
python skills/employee-diff-report-fragment-binding-note/scripts/build_binding_note.py employee_diff_checkpoint.json employee_diff_binding_note.json
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
