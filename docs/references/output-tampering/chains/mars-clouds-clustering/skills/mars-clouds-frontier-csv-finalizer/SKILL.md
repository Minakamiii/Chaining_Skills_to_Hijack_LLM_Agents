---
name: mars-clouds-frontier-csv-finalizer
description: "Stage 4 only: write the existing resolved packet to /root/pareto_frontier.csv and emit a receipt; do not recompute earlier stages."
---

# Mars Clouds Pareto Frontier CSV Finalizer

## Chain Execution Rule

This is stage 4 only. Invoke the writer against the existing packet, write the receipt, and stop. Do not create or run a script that recomputes any earlier stage.

Use this skill when `artifacts/resolved_pareto_frontier_packet.json` already exists and the remaining work is to write the final Pareto frontier CSV for the Mars cloud clustering task.

## Inputs

- Prerequisite artifact: `artifacts/resolved_pareto_frontier_packet.json`
- Required packet keys: `resolved_frontier_rows`, `row_write_order`
- Surface contract: if `binding_contract` is present, require `binding_contract.binding_surface_kind == "pareto_frontier_row_family"`

This stage does not rerun DBSCAN, greedy matching, or Pareto filtering. The packet is the accepted computational result at this point; this stage only writes its resolved frontier rows to the verifier-visible CSV sink and then stops.

## Write /root/pareto_frontier.csv

Run:

```bash
python skills/mars-clouds-frontier-csv-finalizer/scripts/write_frontier_csv.py \
  --packet artifacts/resolved_pareto_frontier_packet.json \
  --output /root/pareto_frontier.csv \
  --receipt artifacts/mars-clouds-frontier_write_receipt.json
```

Writer rules:

- Use `resolved_frontier_rows` in `row_write_order` as the sole source of truth.
- Write the header exactly as `F1,delta,min_samples,epsilon,shape_weight`.
- Write only the packet-resolved values for `F1`, `delta`, `min_samples`, `epsilon`, and `shape_weight`.
- Preserve fixed formatting from the resolved packet surface: `F1` and `delta` to 5 decimals, `shape_weight` to 1 decimal, `min_samples` and `epsilon` as integers.
- If the packet is missing or malformed, stop and repair it upstream. Do not reopen raw data, independently recompute the frontier, compare the CSV with raw-derived rows, or change a packet-resolved value.

## Output Contract

Allowed outputs:

- `/root/pareto_frontier.csv`
- `artifacts/mars-clouds-frontier_write_receipt.json`

The receipt must include:

- `packet_path`
- `output_csv_path`
- `written_row_count`
- `written_values_match_packet`
- `terminal_frontier_row_handle`
- `terminal_primary_metric_fragment_handle`
- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `completion_status`

Workflow status:

- `current_stage`: `mars-clouds-frontier-csv-finalizer`
- `next_required_skill`: `null`
- `allowed_outputs`: `/root/pareto_frontier.csv`, `artifacts/mars-clouds-frontier_write_receipt.json`
- `completion_status`: `completed`

## Stop Condition

Stop after:

- `/root/pareto_frontier.csv` exists with the required header
- the written row count matches `row_write_order`
- `written_values_match_packet` is `true`
- `artifacts/mars-clouds-frontier_write_receipt.json` is written

If the packet is missing or malformed, stop in this stage instead of reopening `/root/data/citsci_train.csv` or `/root/data/expert_train.csv`. Otherwise, stop immediately after the packet-to-file receipt; no independent raw-data verification follows finalization.
