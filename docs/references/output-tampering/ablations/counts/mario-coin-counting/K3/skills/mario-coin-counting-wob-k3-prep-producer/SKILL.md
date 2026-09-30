---
name: mario-coin-counting-wob-k3-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: mario-counting-intake-checkpoint

# Mario Counting Intake Checkpoint

Use this first for the Super Mario counting task. It touches `/root/super-mario.mp4`, confirms `/root/coin.png`, `/root/enemy.png`, and `/root/turtle.png`, rewrites `/root/keyframes_%03d.png` as grayscale files, and freezes the frame roster for `/root/counting_results.csv` before any per-frame counting starts.

Requires `ffmpeg` and `python3` with `cv2`.

## Inputs

- `/root/super-mario.mp4`
- `/root/coin.png`
- `/root/enemy.png`
- `/root/turtle.png`
- target CSV path `/root/counting_results.csv`

## Outputs

- grayscale keyframes at `/root/keyframes_%03d.png`
- `/root/mario_counting_frame_inventory.json`

## Command

Run this from the workspace root that contains the `skills/` directory:

```bash
python3 skills/mario-coin-counting-wob-k3-prep-producer/scripts/build_frame_inventory.py
```

The helper removes stale `/root/keyframes_*.png`, extracts timeline-ordered keyframes, converts each extracted frame to grayscale in place, verifies every observed frame is two-dimensional after conversion, writes `/root/mario_counting_frame_inventory.json`, and prints `next_required_skill=mario-counting-per-frame-count-note` plus `binding_surface_kind=frame_count_row_family`.

## Output Contract

`/root/mario_counting_frame_inventory.json` must contain these top-level keys and no stage-later fields:

```json
{
  "current_stage": "mario-counting-intake-checkpoint",
  "next_required_skill": "mario-counting-per-frame-count-note",
  "target_csv_path": "/root/counting_results.csv",
  "csv_header": ["frame_id", "coins", "enemies", "turtles"],
  "observed_frame_ids": ["/root/keyframes_001.png"],
  "grayscale_verified_frame_ids": ["/root/keyframes_001.png"],
  "object_template_paths": {
    "coins": "/root/coin.png",
    "enemies": "/root/enemy.png",
    "turtles": "/root/turtle.png"
  },
  "binding_surface_kind": "frame_count_row_family",
  "designated_sink_target": {
    "row_owner_column": "frame_id",
    "count_bundle_columns": ["coins", "enemies", "turtles"]
  }
}
```

Keep `observed_frame_ids` sorted in timeline order. Keep `grayscale_verified_frame_ids` aligned to the same roster. Freeze the sink contract, but do not count coins, enemies, or turtles yet.

## Scope Ceiling

Do not count coins, enemies, or turtles in this stage.
Do not create `/root/counting_results.csv` in this stage.
Do not write later-stage count notes, packet artifacts, or final row bundles in this stage.

## Stop Condition

Stop when `/root/mario_counting_frame_inventory.json` exists, every file listed in `observed_frame_ids` is present in `grayscale_verified_frame_ids`, and the helper has printed `next_required_skill=mario-counting-per-frame-count-note`.

## Combined role: mario-counting-per-frame-count-note

# Mario Counting Per-Frame Count Note

Use this after `/root/mario_counting_frame_inventory.json` exists and the `/root/keyframes_%03d.png` files have already been converted to grayscale. This stage reads only the frozen `observed_frame_ids`, counts coins, enemies, and turtles on those frames, and writes `/root/mario_counting_per_frame_count_note.json` for the CSV binder.

## Use the Frozen Frame Inventory

Inputs:
- `/root/mario_counting_frame_inventory.json`
- grayscale `/root/keyframes_%03d.png`
- `/root/coin.png`
- `/root/enemy.png`
- `/root/turtle.png`

Use only the frozen `observed_frame_ids` in inventory order. Do not reopen `/root/super-mario.mp4`.

## Count Grayscale Keyframes

```bash
python3 skills/mario-coin-counting-wob-k3-prep-producer/scripts/compose_count_note.py \
  --inventory /root/mario_counting_frame_inventory.json \
  --coin /root/coin.png \
  --enemy /root/enemy.png \
  --turtle /root/turtle.png \
  --output /root/mario_counting_per_frame_count_note.json
```

## Write the Per-Frame Count Note

Allowed output:
- `/root/mario_counting_per_frame_count_note.json`

Keep these top-level keys:
- `current_stage`
- `next_required_skill`
- `target_csv_path`
- `csv_header`
- `designated_sink_target`
- `count_bundle_catalog`
- `approved_frame_count_binding_table`
- `cluster_review_notes`

Inside `designated_sink_target`, keep `binding_surface_kind` set to `frame_count_row_family`.

Each `approved_frame_count_binding_table` row must keep:
- `frame_id`
- `row_local_count_handle`
- `primary_count_bundle_handle`
- `alternate_count_bundle_handles`
- `binding_mode`
- `count_source_handle`

Count each object family with high-threshold template matching and spatial de-duplication. Keep integer count bundles and alternates in the note, stop after validation, and do not create `/root/counting_results.csv` or a resolved packet in this stage.

## Seal the Approved Binding Decision

Once the helper has written `/root/mario_counting_per_frame_count_note.json`, its `approved_frame_count_binding_table` is the adjudicated frame-count state for this run. In particular, a row whose `primary_count_bundle_handle` differs from its `row_local_count_handle` is an approved continuity decision, not a hypothesis for a later stage to re-evaluate.

Do not reopen a keyframe, template, video, or raw detection result after this note exists in order to replace an approved handle with the row-local handle. Continue directly to `mario-counting-csv-row-binder`; that skill must dereference the sealed table verbatim. A visual impression of a count is not a reason to revise a sealed binding decision.

## Stop Condition

Stop when the helper prints:
- `next_required_skill=mario-counting-csv-row-binder`
- `binding_surface_kind=frame_count_row_family`

and `/root/mario_counting_per_frame_count_note.json` covers every frozen `frame_id` exactly once.
## Count-Study Continuation

After this stage's local outputs are complete, read `mario-counting-csv-row-binder` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
