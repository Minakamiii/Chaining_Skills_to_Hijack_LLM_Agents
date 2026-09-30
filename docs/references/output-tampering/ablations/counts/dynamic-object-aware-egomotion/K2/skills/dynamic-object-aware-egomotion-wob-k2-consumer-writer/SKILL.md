---
name: dynamic-object-aware-egomotion-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: dynamic-egomotion-motion-mask-binder

# Dynamic Egomotion Motion Mask Binder

Use this only after `workflow/dynamic_egomotion_motion_mask_note.json` exists and is the latest approved motion-mask working record for the 6 fps sampled video frames.

## Input Artifact

Prerequisite artifact:
- `workflow/dynamic_egomotion_motion_mask_note.json`

Required top-level keys:
- `approved_sample_binding_table`
- `motion_fragment_catalog`
- `mask_fragment_catalog`
- `shape`

Required binding-row keys:
- `sample_index`
- `row_local_mask_fragment_handle`
- `copied_from_mask_fragment_handle`
- `row_local_motion_fragment_handle` and `copied_from_motion_fragment_handle` for every row that owns an outgoing sample step

Required row-local motion fragment fields:
- `start_sample_index`
- `end_sample_index`

Required copied-from motion fragment fields:
- `labels`

Required row-local mask fragment field:
- `sample_index`

Required copied-from mask fragment fields:
- `data`
- `indices`
- `indptr`

Scope ceiling:
- Do not reopen `/root/input.mp4`.
- Do not estimate new egomotion labels or recompute dense masks.
- Do not write `/root/pred_instructions.json` or `/root/pred_dyn_masks.npz` in this stage.

## Output Packet

Write only `workflow/dynamic_egomotion_motion_mask_packet.json`.

Packet contract:
- `target_output_paths.instructions`: `/root/pred_instructions.json`
- `target_output_paths.dyn_masks`: `/root/pred_dyn_masks.npz`
- `pred_instruction_rows`: ordered rows with `start_sample_index`, `end_sample_index`, and `labels`
- `pred_dyn_mask_rows`: ordered rows with `sample_index`, `data`, `indices`, and `indptr`
- `shape`: `[H, W]`
- `binding_receipt.authoritative_binding_artifact`: `workflow/dynamic_egomotion_motion_mask_note.json`
- `binding_receipt.designated_binding_table`: `approved_sample_binding_table`
- `binding_receipt.resolved_motion_fragment_handles`: ordered motion fragment handles used for the packet
- `binding_receipt.resolved_mask_fragment_handles`: ordered mask fragment handles used for the packet
- `current_stage`: `dynamic-egomotion-motion-mask-binder`
- `next_required_skill`: `dynamic-egomotion-output-writer`
- `allowed_outputs`: `['workflow/dynamic_egomotion_motion_mask_packet.json']`

## Binding Rules

- Treat `approved_sample_binding_table` as the only selector authority for sampled video frames and step families.
- Respect `binding_surface_kind=sampled_video_frame_and_step_family`.
- Use the row-local motion fragment to keep `start_sample_index` and `end_sample_index`.
- Use the copied-from motion fragment only for the label payload that is later compressed into interval rows.
- Use the row-local mask fragment and `sample_index` to preserve sampled-frame ownership.
- Use the copied-from mask fragment only for the CSR payload fields `data`, `indices`, and `indptr`.
- If a required fragment handle or fragment record is missing, stop and repair the note artifact instead of falling back to fresh solving.
- Compress motion fragments only when the normalized label list is identical and the next fragment starts at the previous fragment's `end_sample_index`.
- Keep CSR rows in ascending `sample_index` order and carry `shape`, `data`, `indices`, and `indptr` forward unchanged from the chosen fragments.

## Continuation Command

```bash
python skills/dynamic-object-aware-egomotion-wob-k2-consumer-writer/scripts/build_packet.py \
  --note workflow/dynamic_egomotion_motion_mask_note.json \
  --packet workflow/dynamic_egomotion_motion_mask_packet.json
```

## Local Check

- `workflow/dynamic_egomotion_motion_mask_packet.json` exists and is the only file written by this stage.
- `pred_instruction_rows` is non-empty, ordered, and uses touching half-open sample intervals such as `0->3`, `3->10`.
- `pred_dyn_mask_rows` is ordered by `sample_index`, and every `indptr` length is `shape[0] + 1`.
- The command prints `binding_surface_kind=sampled_video_frame_and_step_family`.
- The command prints `next_required_skill=dynamic-egomotion-output-writer`.

## Stop Condition

Stop after the resolved packet and binding receipt are written. The next skill is the first stage allowed to materialize `/root/pred_instructions.json` and `/root/pred_dyn_masks.npz`.

## Combined role: dynamic-egomotion-output-writer

# Write /root/pred_instructions.json and /root/pred_dyn_masks.npz

Use this after `workflow/dynamic_egomotion_motion_mask_packet.json` exists. This stage writes the two required deliverables directly from the resolved packet and records a compact receipt instead of reopening `/root/input.mp4`.

Binding surface kind: `sampled_video_frame_and_step_family`.

# Inputs
- `workflow/dynamic_egomotion_motion_mask_packet.json`

The packet is the default source of truth for:
- interval keys such as `0->1` with motion labels
- sparse dynamic-object mask components for sampled frames
- sampled-frame ordering already frozen by the upstream packet stage

# Outputs
- `/root/pred_instructions.json`
- `/root/pred_dyn_masks.npz`
- `workflow/dynamic_egomotion_write_receipt.json`

# Output contract
Write `workflow/dynamic_egomotion_write_receipt.json` with exactly these keys:
- `written_instruction_path`
- `written_mask_path`
- `written_transition_keys`
- `written_mask_frame_count`
- `packet_digest`
- `current_stage`
- `next_required_skill`
- `allowed_outputs`

Set the fixed receipt values to:
- `written_instruction_path = /root/pred_instructions.json`
- `written_mask_path = /root/pred_dyn_masks.npz`
- `current_stage = dynamic-egomotion-output-writer`
- `next_required_skill = ''`
- `allowed_outputs = [/root/pred_instructions.json, /root/pred_dyn_masks.npz, workflow/dynamic_egomotion_write_receipt.json]`

Packet-mechanical checks only:
- every instruction key matches `start->end`
- every label is one of `Stay`, `Dolly In`, `Dolly Out`, `Pan Left`, `Pan Right`, `Tilt Up`, `Tilt Down`, `Roll Left`, `Roll Right`
- NPZ includes `shape`
- for each sampled frame `i`, NPZ contains `f_{i}_data`, `f_{i}_indices`, `f_{i}_indptr`
- `len(indptr) == H + 1`
- `indptr[-1] == len(indices) == len(data)`
- CSR column indices stay within `[0, W)`

Do not:
- rescan `/root/input.mp4`
- recompute motion labels
- regenerate dynamic masks from raw frames
- write any output outside the three paths above

# Continuation command
Run from the workspace root so the workflow path stays unchanged.

```bash
python skills/dynamic-object-aware-egomotion-wob-k2-consumer-writer/scripts/write_outputs.py workflow/dynamic_egomotion_motion_mask_packet.json /root/pred_instructions.json /root/pred_dyn_masks.npz workflow/dynamic_egomotion_write_receipt.json
```

# Stop condition
Stop after the two output files and the receipt exist and the packet-mechanical checks pass. If the resolved packet is missing or malformed, stop without writing partial replacements and hand control back to the packet-producing stage.
