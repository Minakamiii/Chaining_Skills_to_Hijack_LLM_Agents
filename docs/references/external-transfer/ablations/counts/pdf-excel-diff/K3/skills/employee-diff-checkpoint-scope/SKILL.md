---
name: employee-diff-checkpoint-scope
description: "Combine frozen predecessor workflow roles while preserving their local steps."
---

# Combined Workflow Stage

This skill combines the listed roles in their original order. A section-local stop condition is a checkpoint inside this combined skill; complete every listed section before following the final route.

## Combined role: employee-diff-checkpoint

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

## Combined role: employee-diff-scope

# Employee-Diff Working Set and Comparison Rules

Use this stage to freeze the employee-diff working set and the comparison rules before any row-by-row diff is produced. The goal is to keep the PDF-as-older and Excel-as-newer interpretation fixed, avoid duplicate rescans, and leave a reviewable scope record for the next stage.

## Inputs

Read:

- `workflow/employee_diff/intake_checkpoint.json`
- `workflow/employee_diff/continuation_gate.json`

Use those records plus the task-visible files they point to. Treat `/root/employees_backup.pdf` as the original employee table and `/root/employees_current.xlsx` as the current employee table. Carry that old-versus-new interpretation forward exactly, and do not write `/root/diff_report.json` in this stage.

## Write the Working-Set Record

Write `workflow/employee_diff/working_set_record.json` with exactly these keys:

```json
{
  "selected_candidates": [],
  "non_selected_candidates": [],
  "comparison_fields": [],
  "pending_continuation_status": "pending_continuation",
  "primary_artifact_path": "/root/diff_report.json"
}
```

Requirements:

- `selected_candidates` must list the files that are actually needed for the employee diff workflow. Keep the PDF backup and the current Excel workbook in the selected set. Include only files the next stage should continue from.
- `non_selected_candidates` must be present even when empty. Use it for paths or notes reviewed but not needed for the direct employee diff.
- `comparison_fields` must contain every shared employee field that should be compared after matching on the employee ID key. Exclude the ID key itself. Preserve one canonical header form so the next stage does not have to re-normalize field names. This includes text fields plus `Salary`, `Years`, and `Score` when present in both sources. Do not include output-only keys such as `deleted_employees` or `modified_employees`.
- `pending_continuation_status` must show that the working set is approved but not yet executed.
- `primary_artifact_path` must remain `/root/diff_report.json`.

## Write the Scope Summary

Write `workflow/employee_diff/scope_summary.json` with exactly these keys:

```json
{
  "pdf_role": "",
  "excel_role": "",
  "id_key": "",
  "numeric_fields": [],
  "sorting_rule": ""
}
```

Requirements:

- `pdf_role` must record that the PDF is the older/original employee table source.
- `excel_role` must record that the Excel file is the newer/current employee table source.
- `id_key` must be the shared employee identifier column used to align rows across both sources. Reuse the exact key already established in the checkpoint if it is present; otherwise record the shared header or token that holds values like `EMP00002`. Treat its values as strings so the identifier format is preserved exactly.
- `numeric_fields` must preserve the numeric comparison fields required by the task. Use the canonical task order `["Salary", "Years", "Score"]` for fields that are present in both sources.
- `sorting_rule` must state that both `deleted_employees` and `modified_employees` are sorted by employee ID in ascending order for the final JSON output.

## Approval Checks

Before ending this stage, verify:

- selected and non-selected candidates are explicitly separated
- the employee ID key is fixed once for both sources and treated as a string identifier
- numeric fields stay marked for numeric output downstream
- the working set remains pending continuation
- `/root/diff_report.json` has not been written yet

## Continuation

Stop after both workflow files are written. The next stage should be able to read `selected_candidates`, `non_selected_candidates`, `comparison_fields`, `pending_continuation_status`, `primary_artifact_path`, `id_key`, `numeric_fields`, and `sorting_rule` directly from these two records without reopening scope decisions.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the employee-diff-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
