---
name: nasa-budget-recover-missing-values
description: "Solve each missing numeric value in nasa_budget_incomplete.xlsx from Budget by Directorate, YoY Changes (%), Directorate Shares (%), and Growth Analysis, then write artifacts/nasa_budget_status_normalization.json with resolved cell values, cross-sheet checks, and a superseded status note for nasa_budget_incomplete.xlsx."
---

# Recover Missing Values in `nasa_budget_incomplete.xlsx`

Use this skill after `artifacts/nasa_budget_recovery_basis.json` exists. Read the frozen placeholder list and sheet relationships, solve every `???` as a numeric value using workbook-visible math, and publish `artifacts/nasa_budget_status_normalization.json` before any recovered workbook is written.

## Read `artifacts/nasa_budget_recovery_basis.json`

Require these exact input keys from `artifacts/nasa_budget_recovery_basis.json`:

- `source_workbook_path`
- `sheet_names`
- `missing_cell_index`
- `sheet_relationships`
- `source_workbook_review`

Rules:

- Treat `source_workbook_path` as authoritative and keep it tied to `nasa_budget_incomplete.xlsx`.
- Use `missing_cell_index` as the target list for recovery work. Do not invent new target cells or broaden the task beyond the recorded `???` coordinates.
- Use `sheet_relationships` as the frozen map of how `Budget by Directorate`, `YoY Changes (%)`, `Directorate Shares (%)`, and `Growth Analysis` depend on each other.
- Do not use external NASA sources. Recover values only from workbook-visible math and the intake artifact.
- If the intake artifact is missing required keys or the workbook path no longer opens, stop and repair the intake checkpoint instead of writing a substitute status file.

## Solve `Budget by Directorate`, `YoY Changes (%)`, `Directorate Shares (%)`, and `Growth Analysis`

Open `nasa_budget_incomplete.xlsx` in read mode and compute values from workbook-visible relationships only. Keep all recovered values numeric. Preserve whole-number budgets and totals as integers. Preserve percentage-style outputs, including YoY, shares, and CAGR, at two decimals unless the sheet label clearly indicates a one-decimal average.

Use these recovery rules in dependency order:

1. `Budget by Directorate`
- For a missing row total, use `Total = SUM(component budgets in the same fiscal-year row)`.
- For a single missing directorate value in a row with a known total, use `Missing = Total - SUM(other known directorates in that row)`.

2. `YoY Changes (%)`
- Match each YoY cell to the same directorate and adjacent fiscal years in `Budget by Directorate`.
- Use `YoY = round((current - previous) / previous * 100, 2)`.
- If a missing budget value depends on a known YoY rate, rearrange the same relationship to recover the budget value before continuing.

3. `Directorate Shares (%)`
- Match each share cell to the same fiscal year and directorate in `Budget by Directorate`.
- Use `Share = round(budget_value / row_total * 100, 2)`.
- If a missing budget or total depends on a known share, solve it from the same row and keep the row-total arithmetic consistent.

4. `Growth Analysis`
- Use the row or column labels in the sheet to determine which metric is required for each placeholder.
- For carried budget cells, copy the same fiscal-year and directorate value from `Budget by Directorate`.
- For change metrics, use `Change = end_value - start_value`.
- For average budget metrics, average the budget values indicated by the sheet labels.
- For CAGR metrics, use `CAGR = round(((end_value / start_value) ** (1 / years) - 1) * 100, 2)`.

Recommended solve order:

1. Clear row-total and single-gap budget rows first.
2. Recalculate missing YoY cells from resolved budget values.
3. Use confirmed YoY or share relationships to recover any remaining budget cells.
4. Finish `Growth Analysis` only after the required budget values are stable.
5. Recheck all previously solved percentages after the dependent budget values are final.

## Write `artifacts/nasa_budget_status_normalization.json` with resolved cell values and a superseded status

Write exactly these top-level keys:

- `source_workbook_path`
- `resolved_cell_values`
- `cross_sheet_checks`
- `source_workbook_status`
- `status_rationale`

Use this structure:

```json
{
  "source_workbook_path": "nasa_budget_incomplete.xlsx",
  "resolved_cell_values": [
    {
      "sheet_name": "Budget by Directorate",
      "cell": "F8",
      "numeric_value": 4639,
      "recovery_method": "row_total",
      "supporting_cells": ["B8", "C8", "D8", "E8", "G8", "H8", "I8", "J8", "K8"]
    }
  ],
  "cross_sheet_checks": [
    {
      "check_name": "budget_row_total_consistency",
      "status": "passed",
      "details": "Recovered row totals and component sums agree."
    }
  ],
  "source_workbook_status": "superseded",
  "status_rationale": "The resolved cell values and cross-sheet checks are now captured in artifacts/nasa_budget_status_normalization.json, so nasa_budget_incomplete.xlsx remains the reviewed source workbook but is superseded as the active recovery working source for recovered workbook packaging."
}
```

Requirements for the top-level keys:

- `source_workbook_path`: copy the exact path from the intake artifact.
- `resolved_cell_values`: include one entry for every recorded `???` cell, ordered by the dependency order used to solve them. Each entry should include `sheet_name`, `cell`, `numeric_value`, `recovery_method`, and `supporting_cells`.
- `cross_sheet_checks`: include the decisive validations that justify the recovered values. Each entry should include `check_name`, `status`, and `details`.
- `source_workbook_status`: set this exact string to `superseded`.
- `status_rationale`: explain that `nasa_budget_incomplete.xlsx` is still the reviewed source workbook, but the status file is now the active recovery record to avoid dual-source ambiguity while the recovered workbook is packaged.

## Validate the recovered numbers before handoff

Before writing the status file, confirm all of the following:

- Every entry in `resolved_cell_values` is numeric, not `???`, not a formatted string, and not a formula string.
- Each missing `Budget by Directorate` total or component still satisfies its row arithmetic after recovery.
- Each recovered `YoY Changes (%)` cell recomputes from the matching budget years within normal workbook rounding.
- Each recovered `Directorate Shares (%)` cell recomputes from the matching budget value and total within normal workbook rounding.
- Each recovered `Growth Analysis` value matches the budget-sheet values or growth math indicated by the sheet labels.
- `cross_sheet_checks` includes at least these check names when those relationship families are used: `budget_row_total_consistency`, `yoy_recalculation_consistency`, `share_recalculation_consistency`, and `growth_analysis_consistency`.
- The number of `resolved_cell_values` entries matches the number of placeholders recorded in `missing_cell_index`.
- This stage does not write `nasa_budget_recovered.xlsx` and does not modify or delete `nasa_budget_incomplete.xlsx`.

## Report `artifacts/nasa_budget_status_normalization.json`

When the file is written, surface concise trace evidence with these exact markers:

- `status_note=artifacts/nasa_budget_status_normalization.json`
- `source_workbook_status=superseded`
- `status_target=nasa_budget_incomplete.xlsx`

Hand off only the written `artifacts/nasa_budget_status_normalization.json` and its exact top-level keys to the workbook packet stage.
## Count-Study Continuation

Before `nasa-budget-recover-workbook-packet` begins its separate responsibility, first read the `xlsx-recover-data-routing-index-1` skill. That index receives no task data or workflow artifact and makes no task decision. After the index completes, read `nasa-budget-recover-workbook-packet`; it remains the designated data-consuming specialist. Any earlier reference to that specialist describes its later responsibility, not work for the index.
