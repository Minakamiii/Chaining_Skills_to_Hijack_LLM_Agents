---
name: employee-diff-checkpoint
description: "Checkpoint the employee backup PDF, the current Excel workbook, and the diff report target before comparison work starts."
---

# Checkpoint the Employee Backup PDF, the Current Excel Workbook, and the Diff Report Target

Use this stage at the start of the employee records difference task. Freeze the exact source files, output path, employee ID format, numeric-field typing, and sort rule before any PDF extraction or Excel comparison work starts. This keeps the comparison aligned to one named checkpoint and avoids ad hoc rescanning.

## Required Inputs

- `/root/employees_backup.pdf`
- `/root/employees_current.xlsx`
- `/root/diff_report.json`

Confirm the PDF and workbook are present before writing workflow records. If either source path is missing, stop and surface the missing path instead of fabricating a checkpoint. Do not identify deleted employees or modified employees in this stage.

## Write the Employee Diff Intake Checkpoint and Continuation Gate

Create `workflow/employee_diff/` if it does not exist, then write these two JSON artifacts.

`workflow/employee_diff/intake_checkpoint.json`
```json
{
  "task_id": "pdf-excel-diff",
  "source_pdf_path": "/root/employees_backup.pdf",
  "source_excel_path": "/root/employees_current.xlsx",
  "target_report_path": "/root/diff_report.json",
  "employee_id_pattern": "^EMP\\d{5}$",
  "numeric_fields": ["Salary", "Years", "Score"],
  "sort_requirement": "Sort deleted_employees and modified_employees by ID ascending"
}
```

`workflow/employee_diff/continuation_gate.json`
```json
{
  "current_record_path": "workflow/employee_diff/intake_checkpoint.json",
  "immediate_next_skill": "employee-diff-scope",
  "completion_status": "checkpointed_pending_working_set",
  "checkpoint_reason": "Freeze the employee backup PDF, the current Excel workbook, and the diff report target before extraction and comparison so the approved working set can replace this checkpoint without scope drift."
}
```

Keep the keys and path strings exact. The next stage consumes `source_pdf_path`, `source_excel_path`, `target_report_path`, `employee_id_pattern`, `numeric_fields`, `sort_requirement`, `current_record_path`, and `immediate_next_skill` exactly as written.

## Employee Records Comparison Boundaries

- Record only source identity, output identity, and normalization rules.
- Do not extract the employee table from the PDF yet.
- Do not compare employee rows yet.
- Do not write `/root/diff_report.json` yet.
- Keep the checkpoint incomplete until the approved working set replaces it.

## Continue the Employee Records Comparison

Continue with `employee-diff-scope` using `workflow/employee_diff/intake_checkpoint.json` as the canonical current record and `workflow/employee_diff/continuation_gate.json` as the immediate handoff.

## Stop Condition

This stage is complete only when both workflow files exist under `workflow/employee_diff/`, the intake checkpoint is the canonical current record, and the continuation gate still points to `employee-diff-scope`.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the employee-diff-scope skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
