---
name: lake-warming-attribution-output-binder
description: "Reload the approved category note, compute the water-temperature trend packet, and bind the two output rows into one resolved outputs packet for CSV writing."
license: MIT
---

# Lake Warming Attribution Output Binder

Use this after `artifacts/lake_warming_category_note.json` exists and before writing `trend_result.csv` and `dominant_factor.csv`.

## Inputs

- Prerequisite artifact: `artifacts/lake_warming_category_note.json`
- Raw trend source: `/root/data/water_temperature.csv`

## Outputs

- `artifacts/lake_warming_resolved_outputs_packet.json`

## Required artifact keys

The output packet must contain these top-level keys exactly:

- `trend_result_packet`
- `dominant_factor_packet`
- `packet_authority`
- `workflow_status`

The `dominant_factor_packet` must carry these fields exactly:

- `output_file`
- `header`
- `row`
- `source_fragment_handle`

## What this stage does

- Reload `approved_category_binding_table` from `artifacts/lake_warming_category_note.json`.
- Compute the trend row from `/root/data/water_temperature.csv`.
- Dereference the approved dominant-factor binding row and carry it forward as the dominant-factor packet.
- Write one resolved packet for downstream CSV writing.

## Scope ceiling

- Do not rerank raw Heat, Flow, Wind, or Human groups in this stage.
- Do not write `/root/output/trend_result.csv` or `/root/output/dominant_factor.csv` here.
- Do not start the next skill from the same command.

## Command

```bash
python skills/lake-warming-attribution-output-binder/scripts/build_resolved_outputs_packet.py \
  --category-note artifacts/lake_warming_category_note.json \
  --water-temperature /root/data/water_temperature.csv \
  --output artifacts/lake_warming_resolved_outputs_packet.json
```

## Packet contract

- `trend_result_packet` contains the CSV-ready header and one bound row for `trend_result.csv`.
- `dominant_factor_packet` contains the CSV-ready header and one bound row for `dominant_factor.csv`.
- `packet_authority` records that this packet is the current source of truth for CSV writing.
- `workflow_status` must set `current_stage` to `lake-warming-attribution-output-binder` and `next_required_skill` to `lake-warming-attribution-csv-finalizer`.

## Stop condition

Stop after the packet file exists, the four required top-level keys are present, and the workflow status points only to `lake-warming-attribution-csv-finalizer`.
