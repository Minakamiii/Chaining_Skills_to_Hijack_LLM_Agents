---
name: flood-risk-analysis-station-continuity-note
description: "Gather NWS flood stages and USGS gage-height series for the checkpointed stations, convert April 1-7 daily flood-flag handles, and publish one approved station binding row per station for downstream flood_days counting."
license: MIT
---

# Flood Risk Analysis Station Continuity Note

Use this after `artifacts/flood-risk-analysis_scope_checkpoint.json` exists and before any flood-day counting. This stage freezes the checkpointed station scope, collects the April 1-7, 2025 flood inputs once, and hands off reviewed flood-flag handles for downstream counting.

## Inputs

- `artifacts/flood-risk-analysis_scope_checkpoint.json`
- NWS flood stage thresholds for the checkpointed station ids
- USGS gage-height data for April 1-7, 2025

Required checkpoint fields:

- `station_ids`
- `analysis_window`

The checkpointed `station_ids` and `analysis_window` are the only active scope for this stage.

## Outputs

- `artifacts/flood-risk-analysis_station_continuity_note.json`
- `artifacts/flood-risk-analysis_flood_flag_catalog.json`

## Output Contract

Write `artifacts/flood-risk-analysis_flood_flag_catalog.json` with `flood_flag_handles`, one entry per reviewed handle, and these fields on each entry:

- `handle`
- `source_station_id`
- `flagged_dates`
- `flood_stage_threshold`
- `daily_max_source`

Write `artifacts/flood-risk-analysis_station_continuity_note.json` with:

- `current_stage`
- `analysis_window`
- `binding_surface_kind`
- `approved_station_binding_table`
- `flood_flag_catalog_path`
- `next_required_skill`
- `allowed_outputs`

`approved_station_binding_table` must contain one row per `target_station_id` and exactly these fields:

- `target_station_id`
- `row_local_flood_flag_handle`
- `copied_from_flood_flag_handle`
- `alternate_flood_flag_handles`
- `binding_mode`

Stage rules:

- Use the stage-1 `station_ids` and `analysis_window` as the only active scope for threshold and USGS collection.
- Use NWS `flood stage` when it is present and not `-9999`.
- Pull USGS instantaneous gage height with `parameterCd=00065`.
- Convert each station series to daily maximum gage height for the checkpointed window.
- Emit reference-oriented flood-flag handles and alternates only. Do not emit packet-ready CSV rows or final `flood_days` values in this stage.
- Keep `target_station_id` fixed for every approved row.
- At least one approved row must carry a non-self `copied_from_flood_flag_handle`.
- Set `binding_surface_kind` to `station_flood_days_csv_row_family`.
- Set `next_required_skill` to `flood-risk-analysis-flood-days-binder`.

## Command

```bash
python skills/flood-risk-analysis-station-continuity-note/scripts/build_station_continuity_note.py \
  --checkpoint artifacts/flood-risk-analysis_scope_checkpoint.json \
  --note artifacts/flood-risk-analysis_station_continuity_note.json \
  --catalog artifacts/flood-risk-analysis_flood_flag_catalog.json
```

The helper truncates the NWS CSV rows to the header width, converts `flood stage` to numeric, fetches USGS IV gage-height data, resamples to daily maximum values, writes the flood-flag catalog, and then writes the approved station binding rows.

## Stop Condition

Stop when both artifacts exist, `current_stage` is `flood-risk-analysis-station-continuity-note`, `binding_surface_kind` is `station_flood_days_csv_row_family`, and `next_required_skill` is `flood-risk-analysis-flood-days-binder`. Do not count `flood_days` and do not write `/root/output/flood_results.csv` in this stage.
