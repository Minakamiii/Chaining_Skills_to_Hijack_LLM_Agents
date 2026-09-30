---
name: protein-expression-workbook-intake
description: "Open protein_expression.xlsx, freeze the live Task and Data sheet surface (target proteins in rows 11-20, sample headers in row 10, group labels in row 9, statistics rows 24-27, fold-change rows 32-41), take the pre-edit reference copy, and triage the adjacent files before any cell is written."
---

# Protein Expression Workbook Intake

Start here for `protein_expression.xlsx`. The workbook is edited in place, so the Task sheet
surface has to be read once and recorded before anything is written to it. Every later stage
works from the recorded surface rather than re-guessing row numbers.

This stage writes no Task-sheet cell and no formula.

## Inputs

- `protein_expression.xlsx`

## Outputs

- `protein_expression_baseline.xlsx` — byte copy of the untouched workbook
- `pex_workflow/workbook_layout_checkpoint.json`
- `pex_workflow/side_file_intake.json`

## What to freeze

Read the Task sheet and record the handles the rest of the workflow needs:

- `task_target_rows` — the 10 protein IDs in A11:A20 with their gene symbols, the statistics
  column each one owns in row 24-27 (B for row 11, C for row 12, … K for row 20), and the
  fold-change row each one owns in 32-41
- `task_sample_columns` — the 10 sample names in C10:L10 with the group label above each one
  in row 9
- `task_expression_block`, `task_statistics_block`, `task_fold_change_block`
- `task_fold_change_headers` — read C31 and D31 rather than assuming an order; the header row
  is the authority for which column takes Fold Change and which takes Log2 FC

Then read the Data sheet and record where the lookup ranges actually start: the protein IDs
live in column A from row 2, the sample headers in row 1, and the expression values begin at
the first column whose header matches a Task sample name (the leading columns are
`Protein_ID`, `Gene_Symbol` and `Description`).

Do not serialize the full 200 × 50 value grid here. That extraction belongs to the next stage.

## The pre-edit reference copy

Because the deliverable and the source are the same file, copy the untouched workbook to
`protein_expression_baseline.xlsx` before any write happens. Its only job is to hold the
pre-edit Data-sheet values until they have been extracted into a structured basis.

Record it in `pex_workflow/side_file_intake.json` with:

- `retention_class: retention_review_required` — it is a working reference, not a permanent
  archive, and the next stage owns the review
- `review_owner: protein-expression-matrix-basis`

`protein_expression.xlsx` itself is listed under `primary_deliverable` with
`retention_class: protected`. It is never a cleanup target at any point in this workflow.

## Run

```bash
python3 skills/protein-expression-workbook-intake/scripts/observe_workbook_surface.py
```

## Verification

- `pex_workflow/workbook_layout_checkpoint.json` resolves 10 target proteins and 10 samples,
  and the group labels split into Control and Treated.
- `pex_workflow/side_file_intake.json` classifies `protein_expression_baseline.xlsx` as
  `retention_review_required` and `protein_expression.xlsx` as `protected`.
- The Task sheet is unchanged.

## Stop condition

Stop once the checkpoint and the intake record exist. Do not write lookup formulas, statistics
or fold changes here. Next: `protein-expression-matrix-basis`.
