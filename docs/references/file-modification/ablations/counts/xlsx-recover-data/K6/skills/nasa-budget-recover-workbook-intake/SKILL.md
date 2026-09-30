---
name: nasa-budget-recover-workbook-intake
description: 'Open nasa_budget_incomplete.xlsx, locate every ??? cell across Budget by Directorate, YoY Changes (%), Directorate Shares (%), and Growth Analysis, and checkpoint the workbook relationships before recovery begins.'
---

# NASA Budget Recover Workbook Intake

This is the safest first step when the task is to recover missing values in `nasa_budget_incomplete.xlsx` and eventually save `nasa_budget_recovered.xlsx`. This stage does not fill any cells. It freezes the workbook layout, placeholder coordinates, and cross-sheet recovery routes into `artifacts/nasa_budget_recovery_basis.json`.

## Use `nasa-budget-recover-workbook-intake`

Use this skill when:
- the workbook still contains `???`
- the recovery work depends on exact sheet names, cell coordinates, and cross-sheet links
- later stages should work from a stable recovery basis instead of rescanning the workbook from scratch

## `nasa_budget_incomplete.xlsx` Input Workbook

Required input:
- `nasa_budget_incomplete.xlsx`

Expected recovery sheets:
- `Budget by Directorate`
- `YoY Changes (%)`
- `Directorate Shares (%)`
- `Growth Analysis`

## `artifacts/nasa_budget_recovery_basis.json` Recovery Basis

Write `artifacts/nasa_budget_recovery_basis.json` with these exact top-level keys:
- `source_workbook_path`
- `sheet_names`
- `missing_cell_index`
- `sheet_relationships`
- `source_workbook_review`

Populate them as follows:
- `source_workbook_path`: exact stable path `nasa_budget_incomplete.xlsx`
- `sheet_names`: workbook sheet titles in workbook order
- `missing_cell_index`: one ordered entry per `???`, preserving exact sheet name and cell coordinate
- `sheet_relationships`: one or more relationship entries with `relationship_type`, `source_sheet`, `target_sheet`, and `anchor_cells`
- `source_workbook_review`: a review entry anchored to `nasa_budget_incomplete.xlsx` with `source_workbook_path`, `covered_sheets`, `placeholder_count`, `review_scope`, and `review_status`

Each `missing_cell_index` entry should capture enough local context to recover the number later without redoing the full scan. Include:
- `sheet_name`
- `cell`
- `row_number`
- `column_letter`
- `row_label`
- `column_label`
- `placeholder_value`
- `dependency_family`
- `support_cells`

Keep the entry order deterministic:
- workbook sheet order first
- row number second
- column number third

## NASA Budget Sheet Relationships

Capture concrete recovery routes that are visible in the workbook:
- `Budget by Directorate` uses directorate values across each fiscal-year row plus the `Total` column
- `YoY Changes (%)` compares a current fiscal-year directorate value to the prior fiscal year in `Budget by Directorate`
- `Directorate Shares (%)` compares a same-year directorate value to the same-year total in `Budget by Directorate`
- `Growth Analysis` uses start and end budget cells for change, average, and CAGR checks, and may also carry forward decisive budget cells directly

Use task-shaped dependency labels inside `dependency_family`, such as:
- `budget_row_total`
- `yoy_from_budget`
- `share_of_total`
- `growth_change`
- `growth_average`
- `growth_cagr`
- `direct_budget_echo`

## Workbook Intake Procedure

1. Open `nasa_budget_incomplete.xlsx` with a workbook-preserving library such as `openpyxl`.
2. Read every sheet title and preserve the titles exactly as they appear.
3. Scan every used cell for the literal placeholder `???`.
4. For each placeholder, record the exact coordinate and the nearest row and column labels that identify the fiscal year and directorate or growth metric.
5. Capture nearby support coordinates that explain the recovery route later, such as same-row totals, prior-year cells, same-year totals, or start and end growth anchors.
6. Build `sheet_relationships` from workbook-visible structure only. This stage is discovery and checkpointing, not numeric recovery.
7. Create `artifacts/` if needed and write `artifacts/nasa_budget_recovery_basis.json`.
8. Stop after the recovery basis is written.

## Workbook Intake Constraints

- Stop at the recovery basis instead of writing `nasa_budget_recovered.xlsx`.
- Do not replace any `???` in this stage.
- Record the workbook review against the stable path `nasa_budget_incomplete.xlsx`.
- Preserve sheet titles and placeholder coordinates exactly as seen in the workbook.
- Keep `source_workbook_review` descriptive only; later stages decide resolved values and any source workbook status change.
- Keep the artifact deterministic so the next stage can consume the exact keys without another broad workbook inventory.

## Recovery Basis Validation

Before finishing, confirm:
- `artifacts/nasa_budget_recovery_basis.json` exists
- all required top-level keys are present
- `missing_cell_index` is not empty
- every `missing_cell_index` entry points to a real sheet listed in `sheet_names`
- the expected recovery sheets appear in `sheet_names`

## Intake Trace Markers

After writing the artifact, emit or report these exact markers:
- `recovery_basis=artifacts/nasa_budget_recovery_basis.json`
- `source_workbook=nasa_budget_incomplete.xlsx`
## Count-Study Continuation

After this stage's local outputs are complete, read the `nasa-budget-recover-missing-values` skill before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
