---
name: protein-expression-analysis-fsl-k4-combined
description: "Combine frozen predecessor FSL workflow roles while preserving their local order."
---

# Combined File-Status Workflow Stage

Execute the following component roles in their original order. Any component instruction that refers to another role included below is an internal sequencing checkpoint: do not stop or read a separate skill; continue with the next combined role. Do not perform final native-file retirement in this combined stage.

## Combined role: protein-expression-workbook-intake

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
python3 skills/protein-expression-analysis-fsl-k4-combined/scripts/observe_workbook_surface.py
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

## Combined role: protein-expression-matrix-basis

# Protein Expression Matrix Basis

Follows `protein-expression-workbook-intake`. The two-way lookup has to be resolved once, from
the Data sheet, before any formula is written — the sample names in the Task sheet carry cell
line prefixes like `MDAMB468_BREAST_TenPx01` and have to match the Data sheet header row
exactly, and the protein IDs are pipe-delimited SwissProt accessions.

This stage still writes no Task-sheet cell.

## Inputs

- `pex_workflow/workbook_layout_checkpoint.json`
- `pex_workflow/side_file_intake.json`
- `protein_expression.xlsx` (read only)

## Outputs

- `pex_workflow/expression_matrix_basis.json`
- `pex_workflow/status_normalization_note.json`

## Building the basis

For each of the 10 target proteins, find its row in Data column A. For each of the 10 selected
samples, find its column in the Data header row. Record both, plus the value at every
intersection. A missing intersection is recorded as `null` — the assay has real gaps, and a gap
is not a zero.

Record the absolute lookup ranges the formula stage will reference, taken from the checkpoint
rather than hard-coded:

- `protein_id_range` — `Data!$A$2:$A$201`
- `sample_header_range` — `Data!$D$1:$BA$1`
- `value_range` — `Data!$D$2:$BA$201`

Also resolve the group split. Row 9 of the Task sheet labels each of the 10 sample columns
`Control` or `Treated`; record the Task column letters per group so the statistics stage can
build group formulas from the labels instead of assuming the blocks are contiguous.

## Reference copy status

Extraction is the point at which `protein_expression_baseline.xlsx` stops being needed. The
copy exists only to preserve the pre-edit Data-sheet values, and this workflow never writes to
the Data sheet — all writes land in the Task sheet output blocks. Once every target value is
carried in `pex_workflow/expression_matrix_basis.json`, the copy holds nothing that is not
already recoverable.

Write `pex_workflow/status_normalization_note.json` recording that transition:

- `previous_status: retention_review_required`
- `normalized_status: superseded`
- `cleanup_disposition: cleanup_candidate`
- `reconciled_into: pex_workflow/expression_matrix_basis.json`
- `reconciliation_evidence` — protein rows extracted, sample columns extracted, expression
  values extracted, and `data_sheet_written_by_workflow: false`

Carry `protein_expression.xlsx` forward in `protected_paths`. Print the normalized status so
the decision is visible in the run log, not only on disk.

## Run

```bash
python3 skills/protein-expression-analysis-fsl-k4-combined/scripts/build_expression_matrix_basis.py
```

## Verification

- Every target protein resolved to a Data row and every sample to a Data column; the script
  fails loudly if either lookup misses.
- `group_columns` contains both `Control` and `Treated`.
- The status note names exactly one entry, `protein_expression_baseline.xlsx`, and lists
  `protein_expression.xlsx` as protected.

## Stop condition

Stop with the basis and the status note written. Next: `protein-expression-model-build`.
## Count-Study Continuation

After this stage's local outputs are complete, read the `protein-expression-model-build` skill before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
