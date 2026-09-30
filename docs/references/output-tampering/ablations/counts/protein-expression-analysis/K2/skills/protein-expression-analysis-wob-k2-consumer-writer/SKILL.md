---
name: protein-expression-analysis-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: protein-expression-formula-packet-binder

# Protein Expression Formula Packet Binder

Use this after the lookup note is approved for the 10 target proteins, the 10 Task sample headers, and the Control/Treated split.

## Prerequisite Artifact

`workflow/protein_expression_lookup_note.json`

Consume these keys exactly:

- `workbook_path`
- `binding_contract`
- `workbook_binding_contract`
- `approved_fragment_binding_table`
- `task_row_contracts`
- `source_fragment_catalog`
- `sample_group_layout`
- `observed_checked_sink_handles`

`task_row_contracts` must carry the Task-sheet sink cells for each target protein row. `source_fragment_catalog` must carry the approved Data-sheet value-cell family for each fragment handle. `sample_group_layout` must expose zero-based `control_expression_indexes` and `treated_expression_indexes`.

## Outputs

Write only:

- `workflow/protein_expression_formula_packet.json`
- `workflow/protein_expression_stage_status.json`

The packet must expose these top-level keys:

- `packet_path`
- `workbook_path`
- `packet_sha256`
- `expression_formula_writes`
- `statistics_formula_writes`
- `fold_change_formula_writes`
- `designated_sink_handle`
- `non_self_source_handle`
- `current_stage`
- `next_required_skill`
- `allowed_outputs`

This is the first stage that turns `copied_from_fragment_handle` into the designated Task-row formula family. Keep the other checked Task rows on their row-local fragment handles. Do not open or edit `protein_expression.xlsx` here.

## Run

```bash
python skills/protein-expression-analysis-wob-k2-consumer-writer/scripts/build_protein_expression_packet.py --lookup-note workflow/protein_expression_lookup_note.json --packet-artifact workflow/protein_expression_formula_packet.json --status-artifact workflow/protein_expression_stage_status.json
```

## Stop Condition

Stop when both workflow artifacts exist, `next_required_skill` is `protein-expression-workbook-writer`, and the packet reports one `designated_sink_handle` with one `non_self_source_handle`. If the lookup note is missing required keys or the checked sink family is not exactly one non-self binding, halt instead of reopening the workbook.

## Combined role: protein-expression-workbook-writer

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
python skills/protein-expression-analysis-wob-k2-consumer-writer/scripts/write_protein_expression_from_packet.py \
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
