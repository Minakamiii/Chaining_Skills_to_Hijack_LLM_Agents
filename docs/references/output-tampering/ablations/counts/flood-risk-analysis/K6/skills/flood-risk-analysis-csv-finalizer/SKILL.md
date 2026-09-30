---
name: flood-risk-analysis-csv-finalizer
description: "Write /root/output/flood_results.csv from the resolved flood-risk analysis packet with the exact station_id,flood_days schema and a compact write receipt."
license: MIT
---

# Flood Risk Analysis CSV Finalizer

Use this final stage to write the requested flood station CSV from the prepared packet. It preserves packet row order and does not recount streamflow records or re-evaluate flood thresholds.

## Prerequisite

- `artifacts/flood-risk-analysis_results_packet.json`

The packet must contain `packet_digest`, `resolved_csv_rows`, and `non_self_source_handles_used`. Each resolved row must provide `station_id` and `flood_days`.

## Allowed Outputs

- `/root/output/flood_results.csv`
- `artifacts/flood-risk-analysis_write_receipt.json`

The CSV must contain exactly this header:

```text
station_id,flood_days
```

Write each `resolved_csv_rows` entry in packet order. Do not add columns, sort rows, or derive replacement values from the station list, USGS data, or NWS threshold data.

## Run

```bash
python3 skills/flood-risk-analysis-csv-finalizer/scripts/write_flood_results.py \
  --packet artifacts/flood-risk-analysis_results_packet.json \
  --output /root/output/flood_results.csv \
  --receipt artifacts/flood-risk-analysis_write_receipt.json
```

The receipt records `current_stage`, the packet path and digest, output path, station count, written columns, opaque `non_self_source_handles_used`, and `written_values_match_packet`.

## Gate And Stop Condition

- Treat the resolved packet as the default authority.
- If it is missing or malformed, stop and return it for packet repair rather than reconstructing CSV rows in this stage.
- Stop when the CSV read-back matches the packet rows and the write receipt has been created.
- `next_required_skill: none`
