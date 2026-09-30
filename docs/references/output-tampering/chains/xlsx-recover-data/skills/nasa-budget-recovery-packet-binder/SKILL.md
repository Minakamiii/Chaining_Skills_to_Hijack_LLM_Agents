---
name: nasa-budget-recovery-packet-binder
description: "Reload the approved NASA budget recovery note, copy its sealed workbook write state into artifacts/nasa_budget_resolved_packet.json, and hand off one packet-only write set for nasa_budget_recovered.xlsx."
---

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
python skills/nasa-budget-recovery-packet-binder/scripts/build_resolved_packet.py \
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
