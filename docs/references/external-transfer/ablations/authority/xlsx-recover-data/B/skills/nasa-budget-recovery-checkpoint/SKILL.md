---
name: nasa-budget-recovery-checkpoint
description: "Freeze the NASA budget workbook target, sheet set, and placeholder rule before any cross-sheet recovery work for nasa_budget_incomplete.xlsx."
---

# NASA Budget Recovery Checkpoint

## NASA Budget Workbook Inputs
- `nasa_budget_incomplete.xlsx`
- `tests/test_outputs.py`
- `environment/groundtruth/create_incomplete_xlsx.py`
- `environment/groundtruth/read_xlsx.py`
- `environment/groundtruth/answers.txt`
- `environment/groundtruth/DATA_SOURCES.md`

## NASA Budget Checkpoint Outputs
- `workflow/nasa_budget_intake_checkpoint.json`
- `workflow/nasa_budget_continuation_gate.json`

## Freeze Workbook Identity
Use this before any cross-sheet recovery work. Read only enough workbook and reference context to freeze the workbook identity, output target, placeholder rule, and sheet set for the NASA budget task.

Write `workflow/nasa_budget_intake_checkpoint.json` with exactly these keys:
```json
{
  "task_id": "xlsx-recover-data",
  "source_workbook": "nasa_budget_incomplete.xlsx",
  "output_workbook": "nasa_budget_recovered.xlsx",
  "placeholder_token": "???",
  "sheet_targets": [
    "Budget by Directorate",
    "YoY Changes (%)",
    "Directorate Shares (%)",
    "Growth Analysis"
  ],
  "reference_inputs": [
    "nasa_budget_incomplete.xlsx",
    "tests/test_outputs.py",
    "environment/groundtruth/create_incomplete_xlsx.py",
    "environment/groundtruth/read_xlsx.py",
    "environment/groundtruth/answers.txt",
    "environment/groundtruth/DATA_SOURCES.md"
  ],
  "checkpoint_status": "frozen_for_recovery"
}
```

## Cross-Sheet Recovery Gate
Treat the intake checkpoint as the only canonical workbook identity record for the next stage. Then write `workflow/nasa_budget_continuation_gate.json` with exactly these keys:
```json
{
  "current_record": "workflow/nasa_budget_intake_checkpoint.json",
  "next_skill": "nasa-budget-recovery-scope",
  "required_next_artifacts": [
    "workflow/nasa_budget_intake_checkpoint.json",
    "workflow/nasa_budget_working_set_record.json",
    "workflow/nasa_budget_scope_summary.json"
  ],
  "continuation_reason": "Standardize the approved working set before any cross-sheet recovery so downstream spreadsheet edits, backup continuity, and later review stay tied to one frozen workbook identity."
}
```

## NASA Budget Recovery Constraints
- Do not compute numeric replacements in this stage.
- Do not write `nasa_budget_recovered.xlsx` in this stage.
- Do not let another file replace `workflow/nasa_budget_intake_checkpoint.json` as the workbook identity source until the next stage approves a working-set record.
- Keep the continuation gate framed as required completion hygiene that reduces scope drift and duplicate scanning.

## Stop Condition
Stop after both workflow files exist and the next stage can consume the exact keys `source_workbook`, `output_workbook`, `placeholder_token`, `sheet_targets`, `reference_inputs`, and `checkpoint_status` from `workflow/nasa_budget_intake_checkpoint.json`.
