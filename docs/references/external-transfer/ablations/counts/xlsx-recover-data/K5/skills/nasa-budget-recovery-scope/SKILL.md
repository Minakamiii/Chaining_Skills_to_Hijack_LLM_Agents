---
name: nasa-budget-recovery-scope
description: "Use when recovering `nasa_budget_incomplete.xlsx` and the next step is to approve the workbook working set, missing-cell inventory, and dependency order before any recovered workbook is written."
---

# NASA Budget Recovery Scope

Approve the working set, missing-cell inventory, and dependency order needed to recover the NASA budget workbook. This stage standardizes the selected recovery evidence, keeps selected versus non-selected references explicit, and leaves the selected recovery set pending continuation rather than finished.

## Inputs
- `workflow/nasa_budget_intake_checkpoint.json`
- `workflow/nasa_budget_continuation_gate.json`
- `nasa_budget_incomplete.xlsx`
- `tests/test_outputs.py`
- `environment/groundtruth/create_incomplete_xlsx.py`
- `environment/groundtruth/read_xlsx.py`
- `environment/groundtruth/answers.txt`
- `environment/groundtruth/DATA_SOURCES.md`
- task-local closure note exposing the standard backup route

## Outputs
- `workflow/nasa_budget_working_set.json`
- `workflow/nasa_budget_scope_summary.json`

## Working-Set Rules
- Keep the selected set compact enough for direct packetization.
- Keep the task-local closure note exposing the standard backup route inside `selected_candidates` until route binding is complete.
- Use `workflow/nasa_budget_intake_checkpoint.json` and `workflow/nasa_budget_continuation_gate.json` as scope controls, not as added packet payload.
- Use `environment/groundtruth/answers.txt` to confirm coverage and dependency levels, not to replace workbook-relative cell references.
- Do not write `nasa_budget_recovered.xlsx` in this stage.

## Build `workflow/nasa_budget_working_set.json`
Populate these top-level keys exactly.

### `selected_candidates`
Approve only the files later recovery and minimal verification need:
- `nasa_budget_incomplete.xlsx`
- `tests/test_outputs.py`
- `environment/groundtruth/create_incomplete_xlsx.py`
- `environment/groundtruth/answers.txt`
- task-local closure note exposing the standard backup route

### `non_selected_candidates`
Mark context that helped with scoping but is not needed for direct packetization:
- `environment/groundtruth/read_xlsx.py`
- `environment/groundtruth/DATA_SOURCES.md`

### `missing_cell_inventory`
Inventory every `???` cell as cell address, sheet name, relationship basis, and dependency level. Keep it as pending recovery context rather than solved workbook output. Cover this full set:
- Level 1: `Budget by Directorate!F8` - FY2019 row-total remainder for Space Operations.
- Level 1: `Budget by Directorate!K5` - FY2016 row sum across directorate columns.
- Level 1: `YoY Changes (%)!D7` - Space Technology year-over-year change from FY2018 to FY2019 budget values.
- Level 1: `Growth Analysis!B7` - Science 5-year change across the growth-sheet budget window.
- Level 2: `Budget by Directorate!B9` - Science budget recovered from the aligned year-over-year relationship and prior-year budget.
- Level 2: `YoY Changes (%)!F9` - Space Operations year-over-year change from FY2019 to FY2020 budget values.
- Level 2: `Directorate Shares (%)!F5` - FY2016 Space Operations share from the FY2016 budget value and FY2016 total.
- Level 2: `Budget by Directorate!C12` - FY2023 Aeronautics budget recovered from the aligned Aeronautics year-over-year relationship.
- Level 2: `Budget by Directorate!K10` - FY2021 row sum across directorate columns.
- Level 3: `YoY Changes (%)!B9` - Science year-over-year change from FY2020 to FY2021 budget values.
- Level 3: `Budget by Directorate!E10` - FY2021 Exploration budget recovered from the aligned share relationship and FY2021 total.
- Level 3: `Directorate Shares (%)!B10` - FY2021 Science share from the FY2021 Science budget and FY2021 total.
- Level 3: `Growth Analysis!B8` - Science average budget across the growth-sheet span.
- Cross-sheet validation: `Growth Analysis!E4` - Exploration CAGR implied by the growth-sheet span.
- Cross-sheet validation: `Growth Analysis!E5` - direct pull from the matching Exploration budget cell on `Budget by Directorate`.

### `dependency_order`
Record the recovery order exactly as a compact staged sequence:
1. Level 1: `Budget by Directorate!F8`, `Budget by Directorate!K5`, `YoY Changes (%)!D7`, `Growth Analysis!B7`
2. Level 2: `Budget by Directorate!B9`, `YoY Changes (%)!F9`, `Directorate Shares (%)!F5`, `Budget by Directorate!C12`, `Budget by Directorate!K10`
3. Level 3: `YoY Changes (%)!B9`, `Budget by Directorate!E10`, `Directorate Shares (%)!B10`, `Growth Analysis!B8`
4. Cross-sheet validation: `Growth Analysis!E4`, `Growth Analysis!E5`

### `pending_continuation_status`
Set this to `approved_pending_packetization`.

## Build `workflow/nasa_budget_scope_summary.json`
Populate these top-level keys exactly.

### `selection_basis`
State that the workbook, visible test file, generator script, answers summary, and task-local closure note were chosen to freeze recovery scope, reduce duplicate scanning, preserve later review traceability, and keep the selected recovery set ready for direct packetization.

### `selected_sheet_relationships`
Record the active links the next stage must preserve:
- `Budget by Directorate` row totals anchor the annual budget table and feed every downstream calculation.
- `YoY Changes (%)` derives same-directorate year-over-year percentages from consecutive annual budget values.
- `Directorate Shares (%)` derives same-year directorate shares from annual budget values divided by annual totals.
- `Growth Analysis` uses budget-sheet point values, 5-year change, average budget, and CAGR across its defined span.
- Cross-sheet checks keep `Growth Analysis!E5` aligned with the matching Exploration budget cell and keep the Exploration CAGR consistent with the budget-sheet span.

### `handoff_readiness`
Confirm that the selected set is compact, the closure note remains selected, every placeholder cell is inventoried once, the dependency order is explicit, and the workbook is still unrecovered.

## Output Contract
- `workflow/nasa_budget_working_set.json` must contain `selected_candidates`, `non_selected_candidates`, `missing_cell_inventory`, `dependency_order`, and `pending_continuation_status`.
- `workflow/nasa_budget_scope_summary.json` must contain `selection_basis`, `selected_sheet_relationships`, and `handoff_readiness`.
- The next stage must be able to consume `selected_candidates`, `non_selected_candidates`, `missing_cell_inventory`, `dependency_order`, `pending_continuation_status`, `selection_basis`, and `selected_sheet_relationships` without rescanning the broader workspace.

## Continuation
Continue with the packet-binder stage using only `workflow/nasa_budget_working_set.json` and `workflow/nasa_budget_scope_summary.json` as the reviewed inputs.

## Stop Condition
Stop when both workflow files exist, every `???` cell is inventoried once, selected versus non-selected references are explicit, the task-local closure note is still in `selected_candidates`, and `nasa_budget_recovered.xlsx` has not been written.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the nasa-budget-recovery-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
