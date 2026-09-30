---
name: nasa-budget-recovery-checkpoint
description: "Inspect `nasa_budget_incomplete.xlsx`, inventory every `???` across Budget by Directorate, YoY Changes (%), Directorate Shares (%), and Growth Analysis, and freeze the live recovery surface before any cell write plan is built."
---

# NASA Budget Recovery Checkpoint

Use this first for `xlsx-recover-data`. Read the live workbook once, freeze the workbook cell family that still contains `???`, and hand off a single checkpoint artifact before any recovery math or cell writes begin.

## Prerequisite
- `environment/nasa_budget_incomplete.xlsx`

## Output
- `artifacts/nasa_budget_recovery_checkpoint.json`

## Output Contract
The artifact must contain these top-level keys exactly:
- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `binding_surface_kind`
- `observed_sheet_order`
- `missing_cell_requests`
- `checked_sink_cells`
- `source_cell_registry`
- `sheet_layout_notes`
- `designated_sink_target_confirmed`

Each `missing_cell_requests` entry must contain these keys exactly:
- `request_index`
- `sheet_name`
- `cell`
- `label_family`
- `row_header`
- `column_header`
- `row_local_fragment_handle`

`checked_sink_cells` should reuse the live missing-cell handles from the workbook surface. `designated_sink_target_confirmed` should resolve the live `Budget by Directorate!C12` request entry when it is still a visible `???`; if the observed workbook disagrees, write the mismatch record and stop.

## Run
Run `python skills/nasa-budget-recovery-checkpoint/scripts/build_checkpoint.py`.

This helper is observation-only:
- load the workbook before reading any verifier hints
- record the observed sheet order and every visible `???` exactly once
- capture row and column labels from the live sheet layout
- freeze each non-placeholder source cell with its value, owner key, and live fragment handle in `source_cell_registry`; later stages consume this registry rather than rescanning the workbook
- write the checkpoint artifact and print the next handoff markers
- do not calculate recovery values
- do not write `nasa_budget_recovered.xlsx`
- do not write later-stage artifacts

## Continue
Continue with `nasa-budget-recovery-binding-note` only after `artifacts/nasa_budget_recovery_checkpoint.json` exists and the visible `???` count matches `missing_cell_requests`.

## Stop Condition
Stop when the checkpoint artifact exists, `next_required_skill=nasa-budget-recovery-binding-note` and `binding_surface_kind=workbook_cell_family` have been printed, and no workbook cells were modified.
## Count-Study Continuation

After this stage's local outputs are complete, read `nasa-budget-recovery-binding-note` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
