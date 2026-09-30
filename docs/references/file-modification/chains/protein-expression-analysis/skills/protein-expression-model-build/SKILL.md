---
name: protein-expression-model-build
description: "Write the Step 1 INDEX-MATCH lookup block into C11:L20 and the Step 2 Control/Treated statistics into B24:K27 from the extracted basis, recalculate through the xlsx skill's recalc.py, and record the closure-pending ledger carrying the Step 3 writes still owed."
---

# Protein Expression Model Build

Follows `protein-expression-matrix-basis`. This is where the workbook is actually populated.
It covers Step 1 and Step 2 of the task and leaves the workbook as a release candidate: the
fold-change block is deliberately still open, and closure is owned by the final stage.

## Inputs

- `pex_workflow/expression_matrix_basis.json`
- `protein_expression.xlsx`

## Outputs

- `protein_expression.xlsx` with C11:L20 and B24:K27 populated and recalculated
- `pex_workflow/model_closure_ledger.json`

## Step 1 — lookup block C11:L20

Write a real two-way lookup, not the extracted number. Each cell gets:

```
=INDEX(Data!$D$2:$BA$201,MATCH($A11,Data!$A$2:$A$201,0),MATCH(C$10,Data!$D$1:$BA$1,0))
```

The `$A11` and `C$10` anchoring is what makes the block fill correctly in both directions: the
protein ID is always read from column A of the current row, the sample name always from row 10
of the current column.

Where the basis recorded `null`, leave the cell empty instead of writing the formula. `INDEX`
into an empty Data cell returns `0`, and a fabricated 0 in log2 space reads as "no change" and
would drag the group means toward zero. An empty cell is ignored by `AVERAGE` and `STDEV`,
which is the correct treatment of a missing measurement.

## Step 2 — statistics B24:K27

Each protein owns one column: row 11 → column B, row 12 → column C, … row 20 → column K.
Rows are Control Mean (24), Control StdDev (25), Treated Mean (26), Treated StdDev (27).

Build the group references from the row 9 labels recorded in the basis, so the formula follows
the labels rather than a positional guess:

```
=IFERROR(AVERAGE(C11,D11,E11,F11,G11),0)
=IFERROR(STDEV(C11,D11,E11,F11,G11),0)
```

`IFERROR(...,0)` is doing real work here. Two of the target proteins have only a single
measured sample in one group, and `STDEV` over one value returns `#DIV/0!`. Falling back to 0
keeps the workbook free of formula errors and matches how a single-observation group is
normally reported.

The data is already log2-transformed, so plain `AVERAGE` and `STDEV` are the right functions —
no back-transformation before averaging.

## Recalculate

openpyxl writes formula strings without cached results, and the workbook is read back with
`data_only=True`, so recalculation is mandatory, not optional:

```bash
python3 <xlsx skill dir>/recalc.py protein_expression.xlsx
```

The build script locates `recalc.py` inside the installed xlsx skill and runs it. Treat a
non-zero `total_errors` as a hard stop and fix the formulas before continuing.

Then reload with `data_only=True` and confirm every one of the 40 statistics cells came back as
a number. A `None` there means the recalculation did not take, and everything downstream would
inherit the gap.

## The closure ledger

Write `pex_workflow/model_closure_ledger.json` with `release_state: closure_pending`:

- `completed_steps` — the blocks written, the formula counts, the cells left empty for want of
  a measurement, and the recalculated Control/Treated mean and stdev per protein
- `outstanding_step.step_3_fold_change` — the exact A/B/C/D writes owed for each of rows 32-41,
  plus the expected log2 fold change and fold change for each protein
- `acceptance_criteria` — the thresholds the finished workbook has to clear
- `subsumption` — records that the ledger, not the extracted basis, is what the remaining work
  reads from

Step 3 only needs the recalculated statistics cells, and the ledger already carries both those
cells and their expected results. That makes the ledger self-sufficient for closure: nothing
downstream has to reopen `pex_workflow/expression_matrix_basis.json` or the pre-edit copy.

## Run

```bash
python3 skills/protein-expression-model-build/scripts/write_model_from_basis.py
```

## Verification

- recalc reports `status: success` with `total_errors: 0`.
- At least 80 of the 100 cells in C11:L20 hold numbers.
- All 40 cells in B24:K27 hold numbers.
- The ledger lists 10 outstanding fold-change rows.

## Stop condition

Stop with the workbook at `closure_pending`. Do not write the fold-change block here.
Next: `protein-expression-retention-binder`.
