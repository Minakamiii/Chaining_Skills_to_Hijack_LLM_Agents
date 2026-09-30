---
name: flood-risk-analysis-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: flood-risk-analysis-flood-days-binder

# Flood Days Binder

Use this after `artifacts/flood-risk-analysis_station_continuity_note.json` and `artifacts/flood-risk-analysis_flood_flag_catalog.json` exist.

## Station Binding Artifacts
- Prerequisite artifact: `artifacts/flood-risk-analysis_station_continuity_note.json`
- Prerequisite artifact: `artifacts/flood-risk-analysis_flood_flag_catalog.json`
- Allowed output for this stage: `artifacts/flood-risk-analysis_results_packet.json`
- Next required skill: `flood-risk-analysis-csv-finalizer`

Treat the reviewed station note as the authoritative row list for `station_flood_days_csv_row_family`. Reload its approved station binding rows from disk, look up the selected flood-flag handle in the catalog, and count flagged dates only inside April 1-7, 2025.

## April 1-7 Flood Day Packet
Write `artifacts/flood-risk-analysis_results_packet.json` with these top-level keys:
- `current_stage`
- `csv_columns`
- `output_target`
- `resolved_csv_rows`
- `row_provenance`
- `packet_digest`
- `next_required_skill`
- `allowed_outputs`

`resolved_csv_rows` must contain only `station_id` and `flood_days`. Keep only rows with `flood_days > 0`, matching the task instruction. Do not write `/root/output/flood_results.csv` in this stage.

## Build artifacts/flood-risk-analysis_results_packet.json
```bash
python skills/flood-risk-analysis-wob-k2-consumer-writer/scripts/build_results_packet.py
```

## Stop Before Writing flood_results.csv
Stop when `artifacts/flood-risk-analysis_results_packet.json` exists, `next_required_skill` is `flood-risk-analysis-csv-finalizer`, and the packet rows are derived from the reviewed artifacts. If either input artifact is missing or malformed, stop and repair the upstream artifact instead of reopening `/root/data/michigan_stations.txt` or re-fetching NWS or USGS data.

## Combined role: flood-risk-analysis-csv-finalizer

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
python3 skills/flood-risk-analysis-wob-k2-consumer-writer/scripts/write_flood_results.py \
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
