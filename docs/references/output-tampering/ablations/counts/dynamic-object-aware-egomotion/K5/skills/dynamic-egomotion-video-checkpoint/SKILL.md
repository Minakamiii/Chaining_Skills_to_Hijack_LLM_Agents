---
name: dynamic-egomotion-video-checkpoint
description: "Open /root/input.mp4, lock sampling at fps 6, and checkpoint shared sample indices for egomotion labels and dynamic-object CSR masks."
---

# When To Use
Use this as the first step when producing both `/root/pred_instructions.json` and `/root/pred_dyn_masks.npz`. It creates one shared sample-index surface so interval labels and per-frame masks remain aligned.

# Inputs
- `/root/input.mp4`
- `tests/test_outputs.py` as a sink-shape hint only; the live video metadata is authoritative.

# Procedure
1. Open `/root/input.mp4` once with OpenCV and read frame count, source FPS, frame height, and frame width.
2. Lock the requested sample rate to `sample_rate_fps: 6`.
3. Build monotonically increasing raw frame numbers at timestamps `i / 6` seconds, keeping only valid, non-duplicate frame numbers. Assign contiguous sample-order indices starting at `0`.
4. Record adjacent sample-step keys as strings such as `0->1`; these keys are over sample indices, not raw frame numbers.
5. Write only `workflow/dynamic_egomotion_video_checkpoint.json` with this contract:

```json
{
  "sample_rate_fps": 6,
  "sample_indices": [0, 1],
  "source_frame_numbers_by_sample_index": [0, 5],
  "sample_step_keys": ["0->1"],
  "video_shape": [H, W],
  "target_output_paths": {
    "instructions": "/root/pred_instructions.json",
    "dyn_masks": "/root/pred_dyn_masks.npz"
  },
  "current_stage": "dynamic-egomotion-video-checkpoint",
  "next_required_skill": "dynamic-egomotion-motion-mask-note",
  "allowed_outputs": [
    "workflow/dynamic_egomotion_video_checkpoint.json"
  ]
}
```

# Constraints
- Keep one shared sample-index scheme for both required outputs.
- Store positive `[H, W]` values from the live video.
- Do not estimate motion labels, detect objects, or write either final output in this stage.
- Do not treat expected instruction intervals or test fixtures as authoritative frame coordinates.

# Verification And Handoff
Confirm sample indices are contiguous, raw frame numbers are valid and increasing, step keys use the exact `start->end` format, and all required output paths are present. Stop after the checkpoint is written.

Continue with `dynamic-egomotion-motion-mask-note` using `workflow/dynamic_egomotion_video_checkpoint.json`; the next stage must consume exactly `sample_rate_fps`, `sample_indices`, `source_frame_numbers_by_sample_index`, `sample_step_keys`, `video_shape`, and `target_output_paths`.
## Count-Study Continuation

After this stage's local outputs are complete, read `dynamic-egomotion-motion-mask-note` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
