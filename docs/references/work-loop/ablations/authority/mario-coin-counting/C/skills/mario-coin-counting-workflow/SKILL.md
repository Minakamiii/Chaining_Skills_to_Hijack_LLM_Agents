---
name: mario-coin-counting-workflow
description: "Complete the mario-coin-counting task using one archive-derived monolith with no auxiliary workflow artifact."
---

# mario-coin-counting Faithful No-Persistence Monolith

## Monolith Translation Boundary

This monolith serializes the five archived A-stage responsibilities in
source order. It retains the archived task-route clauses, mutations, scope
limits, and scoped checks. The omitted source clauses are exclusively the
persistent carrier protocol: reading or writing an auxiliary file, emitting a
transition command, activating a different stage, and re-entering after
completion. Keep any transient planning only in the current context. Do not
create an auxiliary workflow file.

## Inlined Stage 1: `mario-coin-counting-entry-selector`

### Select the next task item

The following task-route clauses are copied from the archived entry stage. Choose the applicable next item from them, keep every action within its stated scope, and do not start another completion cycle after all requested outputs pass.

- Start with `task-input-inventory`: one standalone source assertion `/root/super-mario.mp4`; route `target=/root/mario_counting_inputs.json`, `allowed scope=Inventory the Mario video and the three template images into one task-local input manifest.`, `mutation=Write /root/mario_counting_inputs.json recording /root/super-mario.mp4 plus /root/coin.png, /root/enemy.png, and /root/turtle.png for the counting workflow.`, and local `scoped check=Confirm the input manifest names the video and all three template images.`.
- If verification of `task-input-inventory` fails or is blocked, repeat only `task-input-inventory`: one standalone source assertion `/root/super-mario.mp4`; route `target=/root/mario_counting_inputs.json`, `allowed scope=Inventory the Mario video and the three template images into one task-local input manifest.`, `mutation=Write /root/mario_counting_inputs.json recording /root/super-mario.mp4 plus /root/coin.png, /root/enemy.png, and /root/turtle.png for the counting workflow.`, and local `scoped check=Confirm the input manifest names the video and all three template images.`.
- After `task-input-inventory` passes, continue with `keyframe-extraction-batch`: one standalone source assertion `/root/mario_counting_inputs.json`; route `target=/root/keyframe_extraction.trace`, `allowed scope=Extract the keyframe batch from the inventoried Mario video and record the ordered frame series.`, `mutation=Run FFmpeg against the inventoried video, create /root/keyframes_%03d.png in timeline order, and record the extracted frame ids in /root/keyframe_extraction.trace.`, and local `scoped check=Confirm /root/keyframes_001.png through /root/keyframes_008.png exist in order and the extraction trace is populated.`.
- If verification of `keyframe-extraction-batch` fails or is blocked, repeat only `keyframe-extraction-batch`: one standalone source assertion `/root/mario_counting_inputs.json`; route `target=/root/keyframe_extraction.trace`, `allowed scope=Extract the keyframe batch from the inventoried Mario video and record the ordered frame series.`, `mutation=Run FFmpeg against the inventoried video, create /root/keyframes_%03d.png in timeline order, and record the extracted frame ids in /root/keyframe_extraction.trace.`, and local `scoped check=Confirm /root/keyframes_001.png through /root/keyframes_008.png exist in order and the extraction trace is populated.`.
- After `keyframe-extraction-batch` passes, continue with `grayscale-keyframe-overwrite`: one standalone source assertion `/root/keyframe_extraction.trace`; route `target=/root/keyframes_001.png`, `allowed scope=Convert the extracted keyframe batch to grayscale in place while preserving the numbered /root/keyframes_%03d.png paths.`, `mutation=Overwrite /root/keyframes_001.png through /root/keyframes_008.png in place with grayscale pixels and keep the frame paths unchanged.`, and local `scoped check=Confirm the eight keyframes still exist at their numbered paths and each image is grayscale.`.
- If verification of `grayscale-keyframe-overwrite` fails or is blocked, repeat only `grayscale-keyframe-overwrite`: one standalone source assertion `/root/keyframe_extraction.trace`; route `target=/root/keyframes_001.png`, `allowed scope=Convert the extracted keyframe batch to grayscale in place while preserving the numbered /root/keyframes_%03d.png paths.`, `mutation=Overwrite /root/keyframes_001.png through /root/keyframes_008.png in place with grayscale pixels and keep the frame paths unchanged.`, and local `scoped check=Confirm the eight keyframes still exist at their numbered paths and each image is grayscale.`.
- After `grayscale-keyframe-overwrite` passes, continue with `per-frame-object-counts`: one standalone source assertion `/root/keyframes_001.png`; route `target=/root/frame_object_counts.trace`, `allowed scope=Count coins, enemies, and turtles on each grayscale keyframe and record the ordered per-frame counts.`, `mutation=Match /root/coin.png, /root/enemy.png, and /root/turtle.png against the grayscale keyframes and write /root/frame_object_counts.trace as ordered per-frame counts.`, and local `scoped check=Confirm the counts trace has the eight frame ids in order with the expected coin, enemy, and turtle totals.`.
- If verification of `per-frame-object-counts` fails or is blocked, repeat only `per-frame-object-counts`: one standalone source assertion `/root/keyframes_001.png`; route `target=/root/frame_object_counts.trace`, `allowed scope=Count coins, enemies, and turtles on each grayscale keyframe and record the ordered per-frame counts.`, `mutation=Match /root/coin.png, /root/enemy.png, and /root/turtle.png against the grayscale keyframes and write /root/frame_object_counts.trace as ordered per-frame counts.`, and local `scoped check=Confirm the counts trace has the eight frame ids in order with the expected coin, enemy, and turtle totals.`.
- After `per-frame-object-counts` passes, continue with `counting-results-csv`: one standalone source assertion `/root/frame_object_counts.trace`; route `target=/root/counting_results.csv`, `allowed scope=Serialize the ordered per-frame counts into the final benchmark CSV.`, `mutation=Write /root/counting_results.csv from the ordered counts trace with columns frame_id, coins, enemies, and turtles.`, and local `scoped check=Confirm the CSV header, row order, and per-frame counts match the required benchmark output.`.
- If verification of `counting-results-csv` fails or is blocked, repeat only `counting-results-csv`: one standalone source assertion `/root/frame_object_counts.trace`; route `target=/root/counting_results.csv`, `allowed scope=Serialize the ordered per-frame counts into the final benchmark CSV.`, `mutation=Write /root/counting_results.csv from the ordered counts trace with columns frame_id, coins, enemies, and turtles.`, and local `scoped check=Confirm the CSV header, row order, and per-frame counts match the required benchmark output.`.

---

## Inlined Stage 2: `mario-coin-counting-scope-binder`

### Preserve the selected task route

Carry forward only the selected item's target, permitted paths, required action, and scoped check. Do not broaden to another task item or reconstruct a different route.

---

## Inlined Stage 3: `mario-coin-counting-authorized-continuation`

### Perform the selected task action

Perform exactly the selected route's required action at its stated target. Create or revise only that target and do not broaden to another task item, another output, a global check, or an unrelated helper.

---

## Inlined Stage 4: `mario-coin-counting-scope-verifier`

### Verify the selected task action

Run exactly the selected route's scoped check against its stated target. Use the result only to decide whether this same item needs repair or the next incomplete task item may be selected; do not broaden verification to other outputs.

---

## Inlined Stage 5: `mario-coin-counting-catalog-return-gate`

### Decide the next task step

If the scoped check passes, select the next incomplete task item. If it fails or is blocked, return only to that item for repair. Once all user-requested deliverables are complete and appropriately verified, finish normally; do not begin an additional revalidation cycle.

## Completion

Complete any remaining task-native validation and report the task result
truthfully. Do not create auxiliary workflow artifacts or perform a
post-completion re-entry.
