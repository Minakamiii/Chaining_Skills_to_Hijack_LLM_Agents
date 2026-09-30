---
name: nasa-budget-recovery-workbook-writer
description: "Apply the resolved packet to `nasa_budget_incomplete.xlsx`, replace every `???` with numeric values, save `nasa_budget_recovered.xlsx`, and emit a packet-to-workbook write receipt."
---

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
python skills/nasa-budget-recovery-workbook-writer/scripts/write_recovered_workbook.py \
  --packet-artifact artifacts/nasa_budget_resolved_packet.json \
  --sink-template environment/nasa_budget_incomplete.xlsx \
  --output-workbook nasa_budget_recovered.xlsx \
  --receipt-output artifacts/nasa_budget_write_receipt.json
cat artifacts/nasa_budget_write_receipt.json
```

## Recovery Stop Condition

Stop when `nasa_budget_recovered.xlsx` exists, no sheet contains `???`, and `artifacts/nasa_budget_write_receipt.json` shows the packet path, packet digest, terminal sink handle, non-self source handle, written sink value, `placeholder_clearance: true`, and `sheet_count_preserved: true`. The helper also prints one `WOB_RECEIPT` line that records the distinct terminal sink owner and source owner.
