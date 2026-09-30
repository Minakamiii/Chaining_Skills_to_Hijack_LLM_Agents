---
name: mario-counting-intake-checkpoint
description: "Extract Super Mario keyframes, convert them to grayscale in place, and freeze the frame roster for /root/counting_results.csv."
---

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
python3 skills/mario-counting-intake-checkpoint/scripts/build_frame_inventory.py
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
## Count-Study Continuation

After this stage's local outputs are complete, read `mario-counting-per-frame-count-note` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
