---
name: lake-warming-attribution-intake-checkpoint
description: "Inspect the lake warming attribution source tables and the two requested CSV outputs, then freeze one observed checkpoint for trend_result.csv and dominant_factor.csv production."
license: MIT
---

# Lake Warming Attribution Intake Checkpoint

Use this as the first step for the lake warming attribution task when `/root/data/` contains water temperature, climate, land cover, and hydrology tables and the requested deliverables are `/root/output/trend_result.csv` and `/root/output/dominant_factor.csv`.

## Inputs And Output

Prerequisite inputs:
- `/root/data/water_temperature.csv`
- `/root/data/climate.csv`
- `/root/data/land_cover.csv`
- `/root/data/hydrology.csv`
- `tests/test_outputs.py`

Required output:
- `artifacts/lake_warming_task_checkpoint.json`

Allowed outputs for this stage:
- `artifacts/lake_warming_task_checkpoint.json`

## What To Record In The Checkpoint

Publish one JSON checkpoint with these top-level keys:
- `observed_input_tables`
- `observed_output_targets`
- `year_alignment_summary`
- `category_source_columns`
- `workflow_status`

`workflow_status` must contain exactly:
- `current_stage`
- `next_required_skill`
- `allowed_outputs`

Use these values in `workflow_status`:
- `current_stage`: `lake-warming-attribution-intake-checkpoint`
- `next_required_skill`: `lake-warming-attribution-category-continuity-note`
- `allowed_outputs`: `["artifacts/lake_warming_task_checkpoint.json"]`

## Checkpoint Requirements

1. Read the live headers from all four source tables.
2. Record the requested output targets from the task surface and the checked column names from `tests/test_outputs.py`.
3. Summarize the shared `Year` coverage across the observed tables instead of assuming full continuity.
4. Record the source columns available for the four attribution categories:
   - `Heat`
   - `Flow`
   - `Wind`
   - `Human`
5. Stop after the checkpoint is written and the required keys are present.

## Output Contract

`observed_input_tables`:
- one entry per source CSV with file path, observed header row, and observed year count

`observed_output_targets`:
- one entry for `trend_result.csv` with expected columns `slope` and `p-value`
- one entry for `dominant_factor.csv` with expected columns `variable` and `contribution`

`year_alignment_summary`:
- shared year list or shared year range derived from the observed tables
- any missing-year notes needed for later aligned analysis

`category_source_columns`:
- `Heat`, `Flow`, `Wind`, and `Human` mapped to the observed source column names from the live tables

## Scope Ceiling

This stage must not:
- calculate the warming slope or p-value
- choose the dominant factor category
- write `trend_result.csv`
- write `dominant_factor.csv`
- publish any later-stage artifact

## Local Validation

Before stopping, confirm that `artifacts/lake_warming_task_checkpoint.json` exists and that all required top-level keys and `workflow_status` keys are present.

## Continuation Command

After the checkpoint passes local validation, continue with:

```bash
printf 'next_required_skill=lake-warming-attribution-category-continuity-note\n'
```

## Stop Condition

Stop when `artifacts/lake_warming_task_checkpoint.json` has been written, validated for the required keys, and `workflow_status.next_required_skill` is `lake-warming-attribution-category-continuity-note`.
