---
name: protein-expression-workbook-intake-checkpoint
description: "Inspect protein_expression.xlsx and freeze the live Task and Data sheet surfaces: target protein rows 11-20, sample headers in row 10, group labels in row 9, yellow statistics cells in rows 24-27, and fold-change cells in rows 32-41."
---

# Protein Expression Workbook Intake Checkpoint

Use this first for `protein_expression.xlsx`. It is the safest entry point because the later cross-sheet lookup note and formula stages should follow the observed `Task` and `Data` sheet surface, not stale row assumptions.

## Inputs

- `protein_expression.xlsx`

## Outputs

- `workflow/protein_expression_workbook_checkpoint.json`
- `workflow/protein_expression_stage_status.json`

## Workbook Surface To Freeze

Write only the workbook path, sheet names, and the live handles needed for later work:

- `task_target_rows`
- `task_sample_headers`
- `task_group_labels`
- `task_expression_block`
- `task_statistics_blocks`
- `task_fold_change_block`
- `data_protein_id_column`
- `data_sample_header_row`
- `current_stage`
- `next_required_skill`
- `allowed_outputs`

Do not serialize full `Data` sheet expression values. Do not write lookup formulas, statistics formulas, or fold-change formulas in this stage.

## Run

```bash
python skills/protein-expression-workbook-intake-checkpoint/scripts/observe_workbook_surface.py
```

## Output Contract

```python
NEXT_REQUIRED_SKILL = "protein-expression-crosssheet-lookup-note"
artifact = {
    "next_required_skill": NEXT_REQUIRED_SKILL,
}
```

The checkpoint artifact must contain these top-level keys:

- `workbook_path`
- `task_sheet_name`
- `data_sheet_name`
- `task_target_rows`
- `task_sample_headers`
- `task_group_labels`
- `task_expression_block`
- `task_statistics_blocks`
- `task_fold_change_block`
- `data_protein_id_column`
- `data_sample_header_row`
- `current_stage`
- `next_required_skill`
- `allowed_outputs`

## Verification

- Both workflow files exist.
- `workflow/protein_expression_stage_status.json` sets `current_stage` to `protein-expression-workbook-intake-checkpoint`.
- `workflow/protein_expression_stage_status.json` sets `next_required_skill` to `protein-expression-crosssheet-lookup-note`.
- `workflow/protein_expression_workbook_checkpoint.json` contains the required top-level keys.

## Stop Condition

Stop after the checkpoint and stage status are written and verified. The next step is `protein-expression-crosssheet-lookup-note`.
## Count-Study Continuation

After this stage's local outputs are complete, read `protein-expression-crosssheet-lookup-note` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
