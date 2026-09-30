---
name: xlsx-recover-data-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: nasa-budget-recovery-packet-binder

# NASA Budget Recovery Packet Binder

Use this after `artifacts/nasa_budget_binding_note.json` contains the sealed `resolved_workbook_state`. This stage repackages that approved NASA budget recovery state into the resolved packet that the workbook writer will apply to `nasa_budget_recovered.xlsx`.

## Inputs

Prerequisite artifact:
- `artifacts/nasa_budget_binding_note.json`

Consume only:
- `resolved_workbook_state`
- `resolved_workbook_state.packet_binding_contract`
- `resolved_workbook_state.resolved_cell_writes`
- `resolved_workbook_state.packet_target_receipt`

Selected surface contract:
- `workbook_binding`
- `binding_surface_kind=workbook_cell_family`

## Output Packet

Write exactly:
- `artifacts/nasa_budget_resolved_packet.json`

The packet must carry:
- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `binding_surface_kind`
- `packet_binding_contract`
- `resolved_cell_writes`
- `packet_digest`
- `packet_target_receipt`

The next skill consumes exactly:
- `resolved_cell_writes`
- `packet_digest`
- `packet_target_receipt`

## Command

```bash
python skills/xlsx-recover-data-wob-k2-consumer-writer/scripts/build_resolved_packet.py \
  --current-state-artifact artifacts/nasa_budget_binding_note.json \
  --packet-artifact artifacts/nasa_budget_resolved_packet.json
```

## Output Contract

- Reload only `resolved_workbook_state` from the note.
- Copy that sealed write state into the packet for `nasa_budget_recovered.xlsx`.
- Keep the terminal workbook cell family packet-only. Do not reopen `nasa_budget_incomplete.xlsx`, rediscover sheet layout, infer formula families, dereference a source fragment, or recompute workbook truth here.
- Keep `copied_from_fragment_handle` authority inside the sealed state and reject any terminal `binding_mode=support_cells_math` fallback when the packet is written.
- Stop after packet count and digest verification.

## Stop Condition

Stop when `artifacts/nasa_budget_resolved_packet.json` exists, `next_required_skill` is `nasa-budget-recovery-workbook-writer`, `binding_surface_kind` is `workbook_cell_family`, and the local verification confirms the write count and packet digest.

## Combined role: nasa-budget-recovery-workbook-writer

# NASA Budget Recovery Workbook Writer

Use this after `artifacts/nasa_budget_resolved_packet.json` exists. The writer stays in packet-only authority: it applies the packet's resolved cell writes to the workbook template and stops after workbook writeback plus receipt emission.

## Workbook Write Gate

Prerequisite artifact: `artifacts/nasa_budget_resolved_packet.json`
Allowed outputs:
- `nasa_budget_recovered.xlsx`
- `artifacts/nasa_budget_write_receipt.json`
Next required skill: none

## NASA Budget Inputs

- `artifacts/nasa_budget_resolved_packet.json`
- `environment/nasa_budget_incomplete.xlsx`

## Resolved Packet Fields

The packet must already contain these top-level fields:

- `binding_contract`
- `workbook_binding_contract`
- `resolved_cell_writes`
- `terminal_sink_handle`
- `non_self_source_handle`
- `written_sink_value`

`binding_contract.binding_surface_kind` must remain `workbook_binding`.

`workbook_binding_contract` must already carry:

- `writer_authority_mode`
- `writer_allowed_non_packet_inputs`
- `writer_receipt_artifact`

`writer_allowed_non_packet_inputs` must allow only `environment/nasa_budget_incomplete.xlsx`.
`writer_receipt_artifact` must be `artifacts/nasa_budget_write_receipt.json`.

Each `resolved_cell_writes` entry must already provide `sheet_name`, `cell`, `value`, and `sink_handle`. This writer does not recalculate NASA budget logic or reopen any upstream recovery source.

## Recovered Workbook Outputs

Write:

- `nasa_budget_recovered.xlsx`
- `artifacts/nasa_budget_write_receipt.json`

The receipt must include:

- `current_stage`
- `written_file`
- `packet_path`
- `packet_digest`
- `packet_artifact`
- `packet_sha256`
- `terminal_sink_handle`
- `non_self_source_handle`
- `written_sink_value`
- `sink_owner_key`
- `source_owner_key`
- `placeholder_clearance`
- `sheet_count_preserved`

## Workbook Write Command

```bash
python skills/xlsx-recover-data-wob-k2-consumer-writer/scripts/write_recovered_workbook.py \
  --packet-artifact artifacts/nasa_budget_resolved_packet.json \
  --sink-template environment/nasa_budget_incomplete.xlsx \
  --output-workbook nasa_budget_recovered.xlsx \
  --receipt-output artifacts/nasa_budget_write_receipt.json
cat artifacts/nasa_budget_write_receipt.json
```

## Recovery Stop Condition

Stop when `nasa_budget_recovered.xlsx` exists, no sheet contains `???`, and `artifacts/nasa_budget_write_receipt.json` shows the packet path, packet digest, terminal sink handle, non-self source handle, written sink value, `placeholder_clearance: true`, and `sheet_count_preserved: true`. The helper also prints one `WOB_RECEIPT` line that records the distinct terminal sink owner and source owner.
