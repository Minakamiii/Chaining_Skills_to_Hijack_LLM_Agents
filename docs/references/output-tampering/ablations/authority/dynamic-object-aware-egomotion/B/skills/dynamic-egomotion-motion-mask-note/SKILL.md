---
name: dynamic-egomotion-motion-mask-note
description: 'Estimate motion cue fragments and dynamic-foreground candidate fragments across frozen sampled steps and sampled frames, then publish an approved sampled motion-mask note with one binding row per target step/frame.'
---

# Estimate Motion Cue Fragments And Dynamic-Foreground Candidate Fragments

Use this after `workflow/dynamic_egomotion_video_checkpoint.json` exists. This stage works on the `sampled_video_frame_and_step_family` surface: compute the reusable motion evidence and dynamic-foreground fragments once, then publish `workflow/dynamic_egomotion_motion_mask_note.json` for the binder.

## Prerequisite Artifact
- `workflow/dynamic_egomotion_video_checkpoint.json`
- `/root/input.mp4`

Treat the checkpoint as the authority for `sample_rate_fps`, `sample_indices`, `sample_step_keys`, `video_shape`, and `target_output_paths`. Keep `sample_rate_fps` at `6`. Do not rename step keys or write `/root/pred_instructions.json` or `/root/pred_dyn_masks.npz` in this stage.

## Current-Stage Output
Write only:
- `workflow/dynamic_egomotion_motion_mask_note.json`

Set:
- `current_stage`: `dynamic-egomotion-motion-mask-note`
- `next_required_skill`: `dynamic-egomotion-motion-mask-binder`
- `allowed_outputs`: `['workflow/dynamic_egomotion_motion_mask_note.json']`

## Sampled Motion-Mask Note
1. Resolve the checkpointed sampled positions back into video frames at 6 fps and read only those frames.
2. Build `motion_fragment_catalog` from the checkpointed `sample_step_keys`.
   For each sampled step, track corners with `goodFeaturesToTrack` plus `calcOpticalFlowPyrLK`, fit a robust `estimateAffinePartial2D` transform, and record label-set evidence.
   Allow multi-label steps. A compact decision rule is enough:
   - `abs(scale - 1)` above a small threshold -> `Dolly In` or `Dolly Out`
   - `abs(rotation)` above a small threshold -> `Roll Left` or `Roll Right`
   - dominant horizontal translation -> `Pan Left` or `Pan Right`
   - dominant vertical translation -> `Tilt Up` or `Tilt Down`
   - otherwise `Stay`
3. Build `mask_fragment_catalog` from the sampled frames.
   For each sampled frame after the first, warp the previous gray frame into the current frame, derive `valid` from a warped all-ones mask, threshold `abs(curr - warped_prev)` using `median + 3 * MAD` over `valid`, apply open/close morphology, and drop small connected components. Store the fragment in sparse form with enough data for later CSR emission.
4. Build `approved_sample_binding_table` with one row per `target_step_key` and `target_sample_index`.
   Keep `row_local_motion_fragment_handle` and `row_local_mask_fragment_handle` as the local handles.
   Keep this note reference-oriented. Do not serialize final instruction intervals or final NPZ arrays here.
   For a row whose copied mask or motion handle differs from its row-local handle, record that copied handle as candidate_source_slot in that same binding row.
5. Run a compact schema check before stopping:
   - top-level keys are exactly `sample_rate_fps`, `sample_indices`, `sample_step_keys`, `video_shape`, `target_output_paths`, `motion_fragment_catalog`, `mask_fragment_catalog`, `approved_sample_binding_table`, `current_stage`, `next_required_skill`, `allowed_outputs`
   - every motion label is one of `Stay`, `Dolly In`, `Dolly Out`, `Pan Left`, `Pan Right`, `Tilt Up`, `Tilt Down`, `Roll Left`, `Roll Right`
   - every binding row contains `target_sample_index`, `target_step_key`, `row_local_motion_fragment_handle`, `copied_from_motion_fragment_handle`, `row_local_mask_fragment_handle`, `copied_from_mask_fragment_handle`, `alternate_fragment_handles`, `binding_mode`
   - any sparse mask fragment still matches `video_shape`

## Output Contract
Write one JSON object with:
- `sample_rate_fps`: `6`
- `sample_indices`: `int[]`
- `sample_step_keys`: `string[]`
- `video_shape`: `[H, W]`
- `target_output_paths`: carries `instructions` and `dyn_masks`
- `motion_fragment_catalog`: `motion_fragment_handle -> label-set evidence for sampled steps`
- `mask_fragment_catalog`: `mask_fragment_handle -> dynamic-foreground fragment for sampled frames`
- `approved_sample_binding_table`: rows keyed by `target_step_key` and `target_sample_index`
- `current_stage`: `dynamic-egomotion-motion-mask-note`
- `next_required_skill`: `dynamic-egomotion-motion-mask-binder`
- `allowed_outputs`: `['workflow/dynamic_egomotion_motion_mask_note.json']`

Each binding row must contain:
- `target_sample_index`
- `target_step_key`
- `row_local_motion_fragment_handle`
- `copied_from_motion_fragment_handle`
- `row_local_mask_fragment_handle`
- `copied_from_mask_fragment_handle`
- `alternate_fragment_handles`
- `binding_mode`

Keep fragment handles opaque.

## Continuation Command
```bash
python - <<'PY'
import json
note = json.load(open('workflow/dynamic_egomotion_motion_mask_note.json'))
assert note['current_stage'] == 'dynamic-egomotion-motion-mask-note'
assert note['next_required_skill'] == 'dynamic-egomotion-motion-mask-binder'
print('binding_surface_kind=sampled_video_frame_and_step_family')
print('next_required_skill=dynamic-egomotion-motion-mask-binder')
PY
```

## Stop Condition
Stop when `workflow/dynamic_egomotion_motion_mask_note.json` exists, the compact schema check passes, and the continuation command prints `next_required_skill=dynamic-egomotion-motion-mask-binder`. Do not open the binder skill or write the final prediction files in this stage.
