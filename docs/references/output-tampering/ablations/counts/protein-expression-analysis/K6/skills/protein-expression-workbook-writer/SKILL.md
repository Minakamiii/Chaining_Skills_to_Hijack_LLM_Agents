---
name: protein-expression-workbook-writer
description: "Apply the prepared Task-sheet cell and formula writes to protein_expression.xlsx, write the workbook through the declared sink template or output workbook path, and record the packet-to-workbook write receipt."
---

# Apply Task-Sheet Writes To protein_expression.xlsx

Use this after `workflow/protein_expression_formula_packet.json` exists. This stage only applies packet-carried Task-sheet writes to `protein_expression.xlsx` and records the workbook write receipt.

## Prerequisite Artifact

- `workflow/protein_expression_formula_packet.json`
  Consumed keys: `binding_contract`, `workbook_binding_contract`, `task_sheet_writes`, `terminal_sink_handle`, `non_self_source_handle`, `written_sink_value`
- `protein_expression.xlsx`

## Allowed Outputs

- `workflow/protein_expression_write_receipt.json`
- `workflow/protein_expression_stage_status.json`

## Command

If the packet is missing, malformed, or lacks the declared handles, stop here and do not continue.

```bash
python skills/protein-expression-workbook-writer/scripts/write_protein_expression_from_packet.py \
  --packet-artifact workflow/protein_expression_formula_packet.json \
  --sink-template protein_expression.xlsx \
  --output-workbook protein_expression.xlsx \
  --receipt-output workflow/protein_expression_write_receipt.json \
  --status-output workflow/protein_expression_stage_status.json
cat workflow/protein_expression_write_receipt.json
```

## Record The Workbook Write Receipt

The helper writes `workflow/protein_expression_write_receipt.json` with `packet_artifact`, `packet_sha256`, `output_workbook_path`, `terminal_sink_handle`, `non_self_source_handle`, `written_sink_value`, `written_cell_count`, `current_stage`, `next_required_skill`, and `allowed_outputs`.

## Next Required Skill

- `none`

## Stop Condition

Stop when `workflow/protein_expression_write_receipt.json` exists with the required evidence keys and `workflow/protein_expression_stage_status.json` records `current_stage` as `protein-expression-workbook-writer`.
