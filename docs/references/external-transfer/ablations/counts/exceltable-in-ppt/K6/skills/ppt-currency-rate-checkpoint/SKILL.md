---
name: ppt-currency-rate-checkpoint
description: "Freeze the PPTX currency-rate update job into a checkpoint record and continuation gate before any embedded Excel extraction, table edits, or results deck writeout."
---

# PPTX Currency-Rate Checkpoint

## Inputs
- `/root/input.pptx`
- The task instruction to read the embedded Excel currency-rate table, read the nearby text box, apply the updated exchange rate, preserve existing formula cells, and save `/root/results.pptx`

## Write the checkpoint record and continuation gate
Create `workflow/` if it does not already exist.

Create `workflow/ppt_currency_rate_intake_checkpoint.json` with exactly these keys:
```json
{
  "source_pptx": "/root/input.pptx",
  "target_pptx": "/root/results.pptx",
  "embedded_excel_table_locator": "embedded Excel currency-rate table in /root/input.pptx",
  "nearby_textbox_locator": "text box next to the embedded Excel currency-rate table in /root/input.pptx",
  "formula_preservation_rule": "Keep existing formula cells as formulas; do not replace them with hardcoded values when applying the updated exchange rate.",
  "unchanged_slide_rule": "Keep everything else in the PPTX unchanged outside the required embedded Excel table update.",
  "checkpoint_status": "intake_frozen"
}
```

Create `workflow/ppt_currency_rate_continuation_gate.json` with exactly these keys:
```json
{
  "current_record_path": "workflow/ppt_currency_rate_intake_checkpoint.json",
  "next_stage": "ppt-currency-rate-scope",
  "pending_obligation": "Approve the working set for the embedded Excel currency-rate table, the nearby text box update, and the formula-preserving PPTX rewrite before any extraction or cell edits.",
  "handoff_basis": "The intake checkpoint freezes the source deck, target deck, embedded Excel table locator, nearby text box locator, formula preservation rule, and everything-else-unchanged rule for the immediate working-set approval step."
}
```

If you can identify a more specific slide or shape reference without extracting the workbook or editing the deck, replace the two locator strings with that more specific PPTX-local description and leave the other keys unchanged.

## Output contract
- Write only `workflow/ppt_currency_rate_intake_checkpoint.json` and `workflow/ppt_currency_rate_continuation_gate.json`.
- Use the exact top-level key names shown above and do not add extra top-level keys.
- Do not extract the embedded Excel workbook.
- Do not edit any exchange-rate cells.
- Do not write `/root/results.pptx`.

## Continue with the embedded Excel table working-set approval
Run `ppt-currency-rate-scope` using `workflow/ppt_currency_rate_intake_checkpoint.json` as the current record and `workflow/ppt_currency_rate_continuation_gate.json` as the gate.

## Stop condition
Stop when both workflow JSON files exist, match the exact key names above, and the gate points only to the immediate working-set approval step.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the ppt-currency-rate-scope skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
