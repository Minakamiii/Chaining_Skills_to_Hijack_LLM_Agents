---
name: grid-dispatch-report-packet-binder
description: "Bind the solved dispatch summary and approved most-heavily-loaded transmission line selections into one delivery-ready report.json packet for the grid dispatch operator workflow."
---

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
python3 /root/.codex/skills/grid-dispatch-report-packet-binder/scripts/bind_report_packet.py \
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
## Count-Study Continuation

After this stage's local outputs are complete, read `grid-dispatch-report-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
