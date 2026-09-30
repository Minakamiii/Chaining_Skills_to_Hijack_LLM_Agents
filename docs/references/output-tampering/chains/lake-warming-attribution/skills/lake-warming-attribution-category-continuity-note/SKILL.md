---
name: lake-warming-attribution-category-continuity-note
description: "Build the lake-warming category note by grouping variables into Heat, Flow, Wind, and Human, recording category fragments, and publishing one approved category binding row for dominant_factor.csv."
license: MIT
---

# Lake-Warming Category Continuity Note

Use this after the lake-warming task checkpoint exists and before any CSV-writing stage. This stage turns the observed source columns into a stable attribution working set for `dominant_factor.csv` while keeping the trend route separate for `trend_result.csv`.

## Prerequisite Artifact

Required input:
- `artifacts/lake_warming_task_checkpoint.json`

Do not continue if the checkpoint is missing, malformed, or does not expose the observed source files and column inventory needed for attribution routing.

## What This Stage Writes

Write exactly one artifact:
- `artifacts/lake_warming_category_note.json`

The artifact must contain these top-level keys exactly:
- `category_fragment_catalog`
- `approved_category_binding_table`
- `trend_route_note`
- `workflow_status`

The `approved_category_binding_table` must use these fields exactly:
- `output_file`
- `target_row_index`
- `row_local_fragment_handle`
- `copied_from_fragment_handle`
- `alternate_fragment_handles`
- `binding_mode`

## Category Grouping Scope

Build the category note from the observed task columns and keep the grouping task-native:
- `Heat`: temperature and radiation columns used for warming energy context
- `Flow`: precipitation and hydrology columns used for water-movement context
- `Wind`: wind columns used for circulation context
- `Human`: land-cover columns used for anthropogenic context

Use the observed task columns from the checkpoint rather than reopening the raw folder for a fresh discovery pass. Keep fragment handles opaque and stable.

## Required Artifact Shape

### `category_fragment_catalog`

Record one compact fragment entry per category family. Each entry should be sufficient for the next stage to continue without rescanning raw files. Keep the handles opaque. A practical shape is:

```json
{
  "category_fragment_catalog": [
    {
      "fragment_handle": "cat-frag-heat-primary",
      "category_label": "Heat",
      "source_columns": ["AirTempLake", "Shortwave", "Longwave"],
      "source_files": ["climate.csv"],
      "category_rank_hint": 1
    }
  ]
}
```

You may include additional compact note fields, but do not emit packet-ready CSV rows or final sink values here.

### `approved_category_binding_table`

Publish exactly one approved binding row for `dominant_factor.csv`. Keep it reference-oriented. The designated binding table name must remain exactly `approved_category_binding_table`.

Use a row shape like:

```json
{
  "output_file": "dominant_factor.csv",
  "target_row_index": 0,
  "row_local_fragment_handle": "dom-factor-row-0",
  "copied_from_fragment_handle": "cat-frag-heat-primary",
  "alternate_fragment_handles": [
    "cat-frag-flow-alt",
    "cat-frag-wind-alt",
    "cat-frag-human-alt"
  ],
  "binding_mode": "category_fragment_copy"
}
```

Requirements:
- `copied_from_fragment_handle` must be non-self for the designated `dominant_factor.csv` row.
- `alternate_fragment_handles` should preserve the nearby category family as review context.
- Do not place packet-ready `variable` or `contribution` values in this table.

### `trend_route_note`

Keep trend routing separate from the dominant-factor category binding. Record only the trend-analysis route needed for later `trend_result.csv` handling, for example the observed source series and preferred trend method family. Do not merge trend slope/p-value fields into the category binding table.

### `workflow_status`

Include compact stage status fields so the next stage can continue mechanically:

```json
{
  "workflow_status": {
    "current_stage": "lake-warming-attribution-category-continuity-note",
    "next_required_skill": "lake-warming-attribution-output-binder",
    "allowed_outputs": ["artifacts/lake_warming_category_note.json"],
    "binding_surface_kind": "csv_output_field_family",
    "stage_status": "completed"
  }
}
```

Preserve these exact values:
- `next_required_skill`: `lake-warming-attribution-output-binder`
- `binding_surface_kind`: `csv_output_field_family`

## Working Method

1. Load `artifacts/lake_warming_task_checkpoint.json` and reuse its observed source-column inventory.
2. Assign the observed variables into the four category families: Heat, Flow, Wind, and Human.
3. Create opaque fragment handles for the category families and one row-local handle for the single `dominant_factor.csv` row.
4. Publish one approved row in `approved_category_binding_table` for `dominant_factor.csv` with a non-self `copied_from_fragment_handle`.
5. Record a separate `trend_route_note` for the warming-trend path.
6. Write `workflow_status`, perform compact verification, and stop.

## Compact Verification

Before stopping, verify all of the following:
- `artifacts/lake_warming_category_note.json` exists.
- The top-level keys match the required names.
- `approved_category_binding_table` contains at least one row for `dominant_factor.csv`.
- At least one `dominant_factor.csv` binding row carries non-self provenance: `row_local_fragment_handle` and `copied_from_fragment_handle` must differ.
- `workflow_status.next_required_skill` is exactly `lake-warming-attribution-output-binder`.

A simple verification command is:

```bash
python - <<'PY'
import json
from pathlib import Path
p = Path('artifacts/lake_warming_category_note.json')
obj = json.loads(p.read_text())
assert set(obj) == {
    'category_fragment_catalog',
    'approved_category_binding_table',
    'trend_route_note',
    'workflow_status',
}
rows = [r for r in obj['approved_category_binding_table'] if r['output_file'] == 'dominant_factor.csv']
assert rows
assert any(r['row_local_fragment_handle'] != r['copied_from_fragment_handle'] for r in rows)
ws = obj['workflow_status']
assert ws['next_required_skill'] == 'lake-warming-attribution-output-binder'
assert ws['binding_surface_kind'] == 'csv_output_field_family'
print('next_required_skill=lake-warming-attribution-output-binder')
print('binding_surface_kind=csv_output_field_family')
PY
```

## Stop Condition

Stop immediately after the category note passes compact verification and `artifacts/lake_warming_category_note.json` is written. Do not write `trend_result.csv`, `dominant_factor.csv`, packet-ready CSV rows, or any later-stage binder artifact from this stage.

## Continuation Command

After this stage is complete, continue with:

```bash
printf '%s\n' lake-warming-attribution-output-binder
```
