---
name: flood-risk-analysis-flood-days-binder
description: "Reload the approved station binding rows and flood-flag catalog, count April 1-7, 2025 flood days for the selected handle on each station row, and materialize `artifacts/flood-risk-analysis_results_packet.json` for `flood_results.csv` without writing the CSV yet."
license: MIT
---

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
python skills/flood-risk-analysis-flood-days-binder/scripts/build_results_packet.py
```

## Stop Before Writing flood_results.csv
Stop when `artifacts/flood-risk-analysis_results_packet.json` exists, `next_required_skill` is `flood-risk-analysis-csv-finalizer`, and the packet rows are derived from the reviewed artifacts. If either input artifact is missing or malformed, stop and repair the upstream artifact instead of reopening `/root/data/michigan_stations.txt` or re-fetching NWS or USGS data.
## Count-Study Continuation

After this stage's local outputs are complete, read `flood-risk-analysis-csv-finalizer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
