---
name: employee-diff-report-intake-checkpoint
description: "Extract the employee table from /root/employees_backup.pdf, compare it with /root/employees_current.xlsx, and checkpoint deleted employee IDs plus compact modified employee field candidates before writing /root/diff_report.json."
---

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
python skills/employee-diff-report-intake-checkpoint/scripts/build_checkpoint.py
```

This command extracts the employee table from the PDF backup, reads the current Excel sheet, compares records by employee ID, and writes only `employee_diff_checkpoint.json`. Do not create `employee_diff_binding_note.json`, `employee_diff_resolved_packet.json`, or `/root/diff_report.json` here.

## Employee Diff Checkpoint Stop Condition

Stop when `employee_diff_checkpoint.json` exists with the exact stage keys above and contains the compact deleted employee IDs, modified employee candidates, modified field families, fragment catalog, and candidate index clusters. Continue from that on-disk checkpoint with `employee-diff-report-fragment-binding-note`.
