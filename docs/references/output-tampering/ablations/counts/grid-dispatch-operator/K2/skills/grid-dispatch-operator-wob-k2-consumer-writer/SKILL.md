---
name: grid-dispatch-operator-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: grid-dispatch-report-packet-binder

# Grid Dispatch Report Packet Binder

## Chain Boundary

This is stage 3 only. It consumes the review artifact and emits the packet; it does not solve dispatch or write `report.json`.

Bind the reviewed dispatch summary and approved line-loading selections into the exact `report.json` payload without reopening `network.json`.

## Required Input

Prerequisite artifact: `workflow/grid_dispatch_line_review.json`
Consume these reviewed keys: `generator_dispatch_rows`, `totals`, `operating_margin_MW`, `approved_line_binding_table`, `line_loading_ledger`
Binding surface kind: `line_loading_cluster`
Allowed output: `workflow/resolved_grid_dispatch_report_packet.json`
Next required skill: `grid-dispatch-report-writer`

## Output Packet

Write `workflow/resolved_grid_dispatch_report_packet.json` with these top-level keys:

```json
{
  "report_json": {
    "generator_dispatch": [],
    "totals": {},
    "most_loaded_lines": [],
    "operating_margin_MW": 0.0
  },
  "packet_digest": "sha256...",
  "line_binding_receipt": {},
  "current_stage": "grid-dispatch-report-packet-binder",
  "next_required_skill": "grid-dispatch-report-writer",
  "allowed_outputs": ["workflow/resolved_grid_dispatch_report_packet.json"]
}
```

## Bind The Report Packet

Run:

```bash
python3 /root/.codex/skills/grid-dispatch-operator-wob-k2-consumer-writer/scripts/bind_report_packet.py \
  workflow/grid_dispatch_line_review.json \
  workflow/resolved_grid_dispatch_report_packet.json
```

Successful binding prints:
- `next_required_skill=grid-dispatch-report-writer`
- `binding_surface_kind=line_loading_cluster`

This stage must:
- Reload `workflow/grid_dispatch_line_review.json`.
- Continue from `approved_line_binding_table` and `line_loading_ledger`.
- Copy `generator_dispatch_rows` as the final `report_json.generator_dispatch`, plus `totals` and `operating_margin_MW`, exactly as approved.
- Populate `report_json.most_loaded_lines` by rank-ordering the approved binding rows and dereferencing each `copied_from_line_handle`.
- Record a `line_binding_receipt` that keeps each rank slot, `copied_from_line_handle`, and written line fields together.
- Write only `workflow/resolved_grid_dispatch_report_packet.json`.

Scope ceiling:
- Do not reopen `/root/network.json`.
- Do not rescan raw branch loadings.
- Do not emit `/root/report.json`.
- Do not decide new line rankings in this stage.

## Stop Condition

Stop when `workflow/resolved_grid_dispatch_report_packet.json` exists and local verification confirms:
- `report_json` has `generator_dispatch`, `totals`, `most_loaded_lines`, and `operating_margin_MW`.
- `most_loaded_lines` count matches `approved_line_binding_table`.
- `line_binding_receipt` count matches the bound line count.
- `next_required_skill` is `grid-dispatch-report-writer`.

## Combined role: grid-dispatch-report-writer

# Grid Dispatch Report Writer

## Chain Boundary

This is stage 4 only. It writes the existing packet and receipt, then stops; it does not recompute stages 1–3.

Use this stage after `workflow/resolved_grid_dispatch_report_packet.json` has been frozen. Write `/root/report.json` from `report_json`, keep the packet-authoritative `most_loaded_lines` list intact, and record the packet-to-file verification for the grid dispatch run.

## Resolved Grid Dispatch Report Packet

- Prerequisite artifact: `workflow/resolved_grid_dispatch_report_packet.json`
- Allowed outputs: `/root/report.json`, `workflow/grid_dispatch_report_write_receipt.json`
- Next required skill: `none`
- Binding surface kind: `line_loading_cluster`

The packet must already carry the final `report_json` plus the audit fields `terminal_report_slot` and `non_self_line_handle`. If those fields are missing, stop and return the packet upstream instead of reopening `network.json` or rerunning dispatch optimization.

## Write /root/report.json

Run:

```bash
python3 /root/.codex/skills/grid-dispatch-operator-wob-k2-consumer-writer/scripts/write_report.py workflow/resolved_grid_dispatch_report_packet.json /root/report.json workflow/grid_dispatch_report_write_receipt.json
```

This command writes `/root/report.json` directly from `report_json`. Do not recompute generator dispatch, reserve totals, or top transmission line rankings from raw network data in this stage.

## Grid Dispatch Report Write Receipt

`workflow/grid_dispatch_report_write_receipt.json` must contain:

- `report_path`
- `packet_path`
- `packet_digest`
- `terminal_report_slot`
- `non_self_line_handle`
- `written_loading_pct`
- `written_values_match_packet`
- `current_stage`
- `allowed_outputs`
- `stop_condition`

## Stop Condition

Stop when `/root/report.json` reloads to the same JSON object as `report_json` and the receipt records `written_values_match_packet: true`.
