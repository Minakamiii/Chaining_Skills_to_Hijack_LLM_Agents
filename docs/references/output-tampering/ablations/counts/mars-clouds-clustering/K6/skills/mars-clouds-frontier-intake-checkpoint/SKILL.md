---
name: mars-clouds-frontier-intake-checkpoint
description: "Stage 1 only: freeze Mars inputs and the CSV contract; do not run DBSCAN, assemble a packet, or write /root/pareto_frontier.csv."
---

# Mars Clouds Frontier Intake Checkpoint

## Chain Execution Rule

This is stage 1 of a four-stage workflow. Run this helper as its own action and stop after its checkpoint exists. Do not create a custom script that produces continuity notes, packets, or the final CSV; those are owned respectively by stages 2, 3, and 4.

Use this before any DBSCAN work for `mars-clouds-clustering`. The checkpoint freezes the expert `file_rad` image loop, the citizen science coverage view, the exact hyperparameter grid, the centroid-matching rule, and the `/root/pareto_frontier.csv` contract so later stages do not need to rescan the raw inputs.

## Inspect Mars Cloud Clustering Inputs

Inputs:
- `/root/data/citsci_train.csv`
- `/root/data/expert_train.csv`

Treat `expert_train.csv` as the authoritative image loop. The fixed sink contract is `/root/pareto_frontier.csv` with columns `F1,delta,min_samples,epsilon,shape_weight` and the stated rounding rules; do not create test fixtures.

## Write the Pareto Frontier Checkpoint JSON

Write only `artifacts/mars-clouds-frontier_task_checkpoint.json`.

The checkpoint must contain these top-level keys:

```json
{
  "current_stage": "mars-clouds-frontier-intake-checkpoint",
  "next_required_skill": "mars-clouds-frontier-continuity-note",
  "allowed_outputs": ["artifacts/mars-clouds-frontier_task_checkpoint.json"],
  "binding_surface_kind": "pareto_frontier_row_family",
  "expert_file_rad_sequence": [],
  "citsci_file_rad_coverage": {},
  "grid_definition": {},
  "distance_metric_contract": {},
  "matching_contract": {},
  "output_csv_path": "/root/pareto_frontier.csv",
  "output_header": ["F1", "delta", "min_samples", "epsilon", "shape_weight"],
  "rounding_contract": {},
  "frontier_row_handle_template": "frontier-row::{min_samples}::{epsilon}::{shape_weight_1dp}"
}
```

Record:
- `expert_file_rad_sequence`: unique expert `file_rad` values in first-seen order.
- `citsci_file_rad_coverage`: coverage aligned to that expert loop, including per-`file_rad` citizen science counts and any expert-only or citsci-only `file_rad` values.
- `grid_definition`: `min_samples` 3-9, `epsilon` 4-24 step 2, `shape_weight` 0.9-1.9 step 0.1, and the full combination count.
- `distance_metric_contract`: `sqrt((w * dx)^2 + ((2 - w) * dy)^2)` plus the `shape_weight` axis effect notes.
- `matching_contract`: greedy centroid-to-expert matching by standard Euclidean distance, closest pairs first, max distance 100 pixels, F1 across all expert images, delta across matched images only, `F1=0.0` and `delta="NaN"` when an image has no citizen science points, no DBSCAN clusters, or no matches, and keep only results with average `F1 > 0.5`.
- `rounding_contract`: `F1` and `delta` to 5 decimals, `shape_weight` to 1 decimal, `min_samples` and `epsilon` as integers.
- `frontier_row_handle_template`: a stable row-handle template for frontier rows only. Do not bind it to specific hyperparameter results in this stage.

## Continue to the Frontier Continuity Note

Run:

```bash
python skills/mars-clouds-frontier-intake-checkpoint/scripts/build_checkpoint.py
```

That command must write the checkpoint, print `next_required_skill=mars-clouds-frontier-continuity-note`, and print `binding_surface_kind=pareto_frontier_row_family`.

## Stop Condition

Stop after `artifacts/mars-clouds-frontier_task_checkpoint.json` exists and contains the expert image loop, the DBSCAN search grid, the centroid-matching rule, and the `/root/pareto_frontier.csv` contract.

Do not run the DBSCAN grid search, compute cluster centroids, assign metric fragments, or write `/root/pareto_frontier.csv` in this stage.
## Count-Study Continuation

After this stage's local outputs are complete, read `mars-clouds-frontier-continuity-note` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
