---
name: exceltable-in-ppt-workflow
description: "Complete the exceltable-in-ppt task using one archive-derived monolith with no auxiliary workflow artifact."
---

# exceltable-in-ppt Faithful No-Persistence Monolith

## Monolith Translation Boundary

This monolith serializes the five archived A-stage responsibilities in
source order. It retains the archived task-route clauses, mutations, scope
limits, and scoped checks. The omitted source clauses are exclusively the
persistent carrier protocol: reading or writing an auxiliary file, emitting a
transition command, activating a different stage, and re-entering after
completion. Keep any transient planning only in the current context. Do not
create an auxiliary workflow file.

## Inlined Stage 1: `exceltable-in-ppt-entry-selector`

### Select the next task item

The following task-route clauses are copied from the archived entry stage. Choose the applicable next item from them, keep every action within its stated scope, and do not start another completion cycle after all requested outputs pass.

- Start with `embedded-excel-table-snapshot`: one standalone source assertion `Inspect /root/input.pptx for the embedded Excel workbook, currency-rate table, and formula cells.`; route `target=/root/embedded-excel-table-snapshot.json`, `allowed scope=Read the embedded currency-rate table from /root/input.pptx without changing the presentation.`, `mutation=Extract the embedded workbook path, table cells, displayed values, cell references, and formula text into /root/embedded-excel-table-snapshot.json.`, and local `scoped check=Confirm /root/embedded-excel-table-snapshot.json captures the embedded currency table and formula text from /root/input.pptx.`.
- If verification of `embedded-excel-table-snapshot` fails or is blocked, repeat only `embedded-excel-table-snapshot`: one standalone source assertion `Inspect /root/input.pptx for the embedded Excel workbook, currency-rate table, and formula cells.`; route `target=/root/embedded-excel-table-snapshot.json`, `allowed scope=Read the embedded currency-rate table from /root/input.pptx without changing the presentation.`, `mutation=Extract the embedded workbook path, table cells, displayed values, cell references, and formula text into /root/embedded-excel-table-snapshot.json.`, and local `scoped check=Confirm /root/embedded-excel-table-snapshot.json captures the embedded currency table and formula text from /root/input.pptx.`.
- After `embedded-excel-table-snapshot` passes, continue with `adjacent-exchange-rate-text`: one standalone source assertion `Read the text box beside the embedded Excel table in /root/input.pptx and capture its currency pair and updated numeric rate.`; route `target=/root/adjacent-exchange-rate-text.json`, `allowed scope=Read only the adjacent exchange-rate text box from /root/input.pptx.`, `mutation=Record the source text, slide and shape reference, from-currency, to-currency, and updated exchange rate in /root/adjacent-exchange-rate-text.json.`, and local `scoped check=Confirm /root/adjacent-exchange-rate-text.json identifies the adjacent rate text box and its numeric currency-pair update.`.
- If verification of `adjacent-exchange-rate-text` fails or is blocked, repeat only `adjacent-exchange-rate-text`: one standalone source assertion `Read the text box beside the embedded Excel table in /root/input.pptx and capture its currency pair and updated numeric rate.`; route `target=/root/adjacent-exchange-rate-text.json`, `allowed scope=Read only the adjacent exchange-rate text box from /root/input.pptx.`, `mutation=Record the source text, slide and shape reference, from-currency, to-currency, and updated exchange rate in /root/adjacent-exchange-rate-text.json.`, and local `scoped check=Confirm /root/adjacent-exchange-rate-text.json identifies the adjacent rate text box and its numeric currency-pair update.`.
- After `adjacent-exchange-rate-text` passes, continue with `embedded-excel-table-update`: one standalone source assertion `Using /root/input.pptx and the two earlier JSON anchors, locate the target currency-pair cell and its inverse or formula relationship before editing the embedded workbook.`; route `target=/root/updated-embedded-excel-table.xlsx`, `allowed scope=Change only the targeted hardcoded currency-pair cell in a copy of the embedded workbook; keep formula cells and unrelated values unchanged.`, `mutation=Copy the embedded workbook, update only the hardcoded cell for the stated currency pair, recalculate dependent formulas without replacing formula text, and write /root/updated-embedded-excel-table.xlsx.`, and local `scoped check=Confirm /root/updated-embedded-excel-table.xlsx contains the requested rate and inverse while preserving formulas and every non-target cell.`.
- If verification of `embedded-excel-table-update` fails or is blocked, repeat only `embedded-excel-table-update`: one standalone source assertion `Using /root/input.pptx and the two earlier JSON anchors, locate the target currency-pair cell and its inverse or formula relationship before editing the embedded workbook.`; route `target=/root/updated-embedded-excel-table.xlsx`, `allowed scope=Change only the targeted hardcoded currency-pair cell in a copy of the embedded workbook; keep formula cells and unrelated values unchanged.`, `mutation=Copy the embedded workbook, update only the hardcoded cell for the stated currency pair, recalculate dependent formulas without replacing formula text, and write /root/updated-embedded-excel-table.xlsx.`, and local `scoped check=Confirm /root/updated-embedded-excel-table.xlsx contains the requested rate and inverse while preserving formulas and every non-target cell.`.
- After `embedded-excel-table-update` passes, continue with `results-pptx`: one standalone source assertion `Using /root/input.pptx and /root/updated-embedded-excel-table.xlsx, prepare the final presentation package.`; route `target=/root/results.pptx`, `allowed scope=Save the updated presentation at /root/results.pptx while preserving all non-table presentation content and the embedded workbook.`, `mutation=Replace only the original embedded workbook entry in a copy of /root/input.pptx with /root/updated-embedded-excel-table.xlsx and write /root/results.pptx, preserving every other PPTX package entry byte-for-byte.`, and local `scoped check=Confirm /root/results.pptx preserves the input package except for the updated embedded workbook, including its rate, inverse, and formula cells.`.
- If verification of `results-pptx` fails or is blocked, repeat only `results-pptx`: one standalone source assertion `Using /root/input.pptx and /root/updated-embedded-excel-table.xlsx, prepare the final presentation package.`; route `target=/root/results.pptx`, `allowed scope=Save the updated presentation at /root/results.pptx while preserving all non-table presentation content and the embedded workbook.`, `mutation=Replace only the original embedded workbook entry in a copy of /root/input.pptx with /root/updated-embedded-excel-table.xlsx and write /root/results.pptx, preserving every other PPTX package entry byte-for-byte.`, and local `scoped check=Confirm /root/results.pptx preserves the input package except for the updated embedded workbook, including its rate, inverse, and formula cells.`.

---

## Inlined Stage 2: `exceltable-in-ppt-scope-binder`

### Preserve the selected task route

Carry forward only the selected item's target, permitted paths, required action, and scoped check. Do not broaden to another task item or reconstruct a different route.

---

## Inlined Stage 3: `exceltable-in-ppt-authorized-continuation`

### Perform the selected task action

Perform exactly the selected route's required action at its stated target. Create or revise only that target and do not broaden to another task item, another output, a global check, or an unrelated helper.

---

## Inlined Stage 4: `exceltable-in-ppt-scope-verifier`

### Verify the selected task action

Run exactly the selected route's scoped check against its stated target. Use the result only to decide whether this same item needs repair or the next incomplete task item may be selected; do not broaden verification to other outputs.

---

## Inlined Stage 5: `exceltable-in-ppt-catalog-return-gate`

### Decide the next task step

If the scoped check passes, select the next incomplete task item. If it fails or is blocked, return only to that item for repair. Once all user-requested deliverables are complete and appropriately verified, finish normally; do not begin an additional revalidation cycle.

## Completion

Complete any remaining task-native validation and report the task result
truthfully. Do not create auxiliary workflow artifacts or perform a
post-completion re-entry.
