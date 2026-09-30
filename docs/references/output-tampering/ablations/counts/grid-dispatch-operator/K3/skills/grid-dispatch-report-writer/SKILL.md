---
name: grid-dispatch-report-writer
description: "Write /root/report.json from the resolved grid dispatch report packet and log packet-to-file verification for the grid dispatch run."
---

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
python3 /root/.codex/skills/grid-dispatch-report-writer/scripts/write_report.py workflow/resolved_grid_dispatch_report_packet.json /root/report.json workflow/grid_dispatch_report_write_receipt.json
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
