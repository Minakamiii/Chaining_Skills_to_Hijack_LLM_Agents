---
name: protein-expression-matrix-basis
description: "Extract the Data-sheet expression basis for the 10 target proteins across the 10 selected samples, resolve the Control/Treated split from row 9, and normalize the status of the pre-edit reference copy once its content is fully reconciled."
---

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
python3 skills/protein-expression-matrix-basis/scripts/build_expression_matrix_basis.py
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
