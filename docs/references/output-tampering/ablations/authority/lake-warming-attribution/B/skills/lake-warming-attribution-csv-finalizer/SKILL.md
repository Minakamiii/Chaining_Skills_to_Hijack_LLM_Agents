---
name: lake-warming-attribution-csv-finalizer
description: "Write trend_result.csv and dominant_factor.csv from the resolved outputs packet, then record a compact write receipt for the two requested deliverables."
license: MIT
---

# Lake Warming Attribution CSV Finalizer

Use this when `artifacts/lake_warming_resolved_outputs_packet.json` already exists and the remaining work is to write the two requested CSV deliverables from that packet authority.

## Inputs

Prerequisite artifact:
- `artifacts/lake_warming_resolved_outputs_packet.json`

Expected sink outputs:
- `/root/output/trend_result.csv`
- `/root/output/dominant_factor.csv`
- `artifacts/lake_warming_write_receipt.json`

## Output Contract

The resolved outputs packet is the default authority. Only reopen earlier artifacts if this packet is missing or malformed.

Required CSV schemas:
- `trend_result.csv`: `slope,p-value`
- `dominant_factor.csv`: `variable,contribution`

Required receipt top-level keys:
- `written_outputs`
- `packet_path`
- `terminal_sink_handles`
- `written_values`
- `workflow_status`

Each `written_outputs` entry must include:
- `output_file`
- `row_count`
- `source_packet_key`

The receipt must record the `dominant_factor.csv` sink handle and the `source_fragment_handle` used for that write.

## Command

Run:

```bash
python skills/lake-warming-attribution-csv-finalizer/scripts/write_from_packet.py \
  --packet artifacts/lake_warming_resolved_outputs_packet.json \
  --trend-out /root/output/trend_result.csv \
  --dominant-out /root/output/dominant_factor.csv \
  --receipt artifacts/lake_warming_write_receipt.json
```

## Stage Rules

- Do not recompute the warming trend or the dominant category from raw tables.
- Write both CSVs directly from packet-carried values.
- Preserve the exact requested column names and ordering.
- Stop after minimal file-existence and header verification.

## Allowed Outputs

- `/root/output/trend_result.csv`
- `/root/output/dominant_factor.csv`
- `artifacts/lake_warming_write_receipt.json`

## Stop Condition

Stop when both CSVs exist with the exact requested headers and `artifacts/lake_warming_write_receipt.json` has been written with the required top-level keys.
