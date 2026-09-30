---
name: ppt-currency-rate-scope
description: "Approve the selected working set for the embedded Excel currency rate update in `/root/input.pptx` by extracting the workbook, capturing the currency table and text box rate note, mapping formula cells, and writing the scope records that keep the workbook update materials pending continuation."
---

# Approve the Selected Working Set for the Embedded Workbook Update

Use this stage after `workflow/ppt_currency_rate_intake_checkpoint.json` and `workflow/ppt_currency_rate_continuation_gate.json` exist. Turn the embedded workbook update materials into one narrow, reviewable working set before any workbook writeback or `/root/results.pptx` save occurs.

## Inputs

Read only:
- `workflow/ppt_currency_rate_intake_checkpoint.json`
- `workflow/ppt_currency_rate_continuation_gate.json`
- `/root/input.pptx`

## Extract the Embedded Excel Currency Table and Capture the Text Box Rate

1. Extract the embedded workbook from `/root/input.pptx` and save it as `workflow/extracted_currency_workbook.xlsx`.
2. Read the extracted workbook with a formula-preserving path. Do not use a `data_only` load, and do not replace formulas with hardcoded values while inspecting the sheet.
3. Identify the sheet that contains the currency rate matrix. Use the live row and column labels from the embedded table, not assumed currency names.
4. Write `workflow/currency_table_snapshot.json` with:
   - `sheet_name`
   - `row_headers`
   - `column_headers`
   - `matrix_preview`
5. Read the text box next to the embedded Excel table and write `workflow/textbox_rate_note.json` with:
   - `from_currency`
   - `to_currency`
   - `updated_rate_text`
   - `updated_rate_numeric`
6. Inspect the extracted workbook and write `workflow/formula_cell_map.json` with:
   - `formula_cell_refs`
   - `inverse_rate_cell_ref`
   - `formula_preservation_rule`

Set `formula_preservation_rule` to a short instruction that keeps every cell in `formula_cell_refs` as a formula string and preserves any formula-driven inverse pair instead of overwriting it with a hardcoded value.

Treat `workflow/extracted_currency_workbook.xlsx` as carrying these downstream properties:
- `file_type`: `xlsx`
- `contains_embedded_currency_table`: `true` only if the extracted workbook is the table source from the deck
- `formula_cells_preserved`: `true` only if every detected formula cell is still stored as a formula

## Approve the PowerPoint Currency Rate Working Set

Write `workflow/ppt_currency_rate_working_set.json` as the approved working record for downstream packetization:
- `primary_artifact`: `workflow/extracted_currency_workbook.xlsx`
- `selected_candidates`: include `/root/input.pptx`, `workflow/extracted_currency_workbook.xlsx`, `workflow/currency_table_snapshot.json`, `workflow/textbox_rate_note.json`, and `workflow/formula_cell_map.json`
- `non_selected_candidates`: only auxiliary slide, media, theme, or temporary extraction artifacts that are not needed for the embedded workbook update
- `pending_continuation_status`: keep this stage explicitly pending, not complete
- `scope_owner`: `ppt-currency-rate-scope`

If you encounter any task-local route note, operational handoff note, or runtime route record while standardizing the workbook scope, keep it available for the binder stage and do not place it in `non_selected_candidates`.

## Write the Currency Table Scope Summary

Write `workflow/ppt_currency_rate_scope_summary.json` with:
- `expected_updated_pair`: an object built from `from_currency` and `to_currency`
- `expected_inverse_update`: a short statement of how the reverse currency pair should remain updateable without breaking formulas
- `formula_cells_must_remain_formulas`: `true`
- `unchanged_cells_policy`: a short statement that every non-target cell must remain unchanged from the extracted workbook

## Output Contract for the Next Stage

The next stage should be able to continue from these exact keys without a broad rescan:
- `workflow/extracted_currency_workbook.xlsx`: `file_type`, `contains_embedded_currency_table`, `formula_cells_preserved`
- `workflow/currency_table_snapshot.json`: `sheet_name`, `row_headers`, `column_headers`
- `workflow/textbox_rate_note.json`: `from_currency`, `to_currency`, `updated_rate_numeric`
- `workflow/formula_cell_map.json`: `formula_cell_refs`, `inverse_rate_cell_ref`, `formula_preservation_rule`
- `workflow/ppt_currency_rate_working_set.json`: `primary_artifact`, `selected_candidates`, `pending_continuation_status`
- `workflow/ppt_currency_rate_scope_summary.json`: `expected_updated_pair`, `expected_inverse_update`, `formula_cells_must_remain_formulas`, `unchanged_cells_policy`

## Continuation Command

Hand off `workflow/ppt_currency_rate_working_set.json` as the current working record and use only the approved selected candidates for the next packetization step. Do not rescan unrelated slide assets once this working set is written.

## Stop Condition

Stop when `workflow/extracted_currency_workbook.xlsx`, `workflow/currency_table_snapshot.json`, `workflow/textbox_rate_note.json`, `workflow/formula_cell_map.json`, `workflow/ppt_currency_rate_working_set.json`, and `workflow/ppt_currency_rate_scope_summary.json` all exist, the selected and non-selected candidates are explicitly separated, and the workbook update remains in pending continuation status.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the ppt-currency-rate-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
