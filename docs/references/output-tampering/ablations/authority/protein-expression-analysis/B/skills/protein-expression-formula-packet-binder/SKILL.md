---
name: protein-expression-formula-packet-binder
description: 'Turn the approved protein expression lookup note into the exact Task-sheet cell and formula writes for C11:L20, B24:K27, and C32:D41 without touching protein_expression.xlsx.'
---

# Protein Expression Formula Packet Binder

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
python skills/protein-expression-formula-packet-binder/scripts/build_protein_expression_packet.py --lookup-note workflow/protein_expression_lookup_note.json --packet-artifact workflow/protein_expression_formula_packet.json --status-artifact workflow/protein_expression_stage_status.json
```

## Stop Condition

Stop when both workflow artifacts exist, `next_required_skill` is `protein-expression-workbook-writer`, and the packet reports one `designated_sink_handle` with one `non_self_source_handle`. If the lookup note is missing required keys or the checked sink family is not exactly one non-self binding, halt instead of reopening the workbook.
