---
name: dubbing-intake-checkpoint-scope
description: "Combine frozen predecessor workflow roles while preserving their local steps."
---

# Combined Workflow Stage

This skill combines the listed roles in their original order. A section-local stop condition is a checkpoint inside this combined skill; complete every listed section before following the final route.

## Combined role: dubbing-intake-checkpoint

# Dubbing Intake Checkpoint

Use this stage at the start of the multilingual dubbing workflow. Freeze one canonical request record before any speech generation, duration control, loudness normalization, or video muxing begins.

## Freeze the Multilingual Dubbing Inputs

Read only these task files and task-visible requirements for this stage:

- `/root/input.mp4`
- `/root/segments.srt`
- `/root/source_text.srt`
- `/root/target_language.txt`
- `/root/reference_target_text.srt`
- `/outputs/tts_segments/seg_0.wav` must be `48000` Hz, mono, and loudness-compliant to `ITU-R BS.1770-4`
- `/outputs/dubbed.mp4` must preserve the original visuals, use `placed_start_sec` within `0.01` seconds of the window start, and keep `drift_sec` within `0.2` seconds
- `/outputs/report.json` must match the required schema and use language-code fields

Create `workflow/` if it does not already exist. Use workflow namespace sidecars for this checkpoint stage rather than root-level notes.

## Write workflow/intake_checkpoint.json

Write `workflow/intake_checkpoint.json` with this exact schema and values:

```json
{
  "task_id": "multilingual-video-dubbing",
  "primary_input_video": "/root/input.mp4",
  "segment_timing_srt": "/root/segments.srt",
  "source_transcript_srt": "/root/source_text.srt",
  "target_language_file": "/root/target_language.txt",
  "reference_target_script_srt": "/root/reference_target_text.srt",
  "required_output_paths": [
    "/outputs/tts_segments/seg_0.wav",
    "/outputs/dubbed.mp4",
    "/outputs/report.json"
  ],
  "delivery_audio_spec": {
    "sample_rate_hz": 48000,
    "channels": 1,
    "loudness_standard": "ITU-R BS.1770-4"
  },
  "sync_constraints": {
    "placed_start_tolerance_sec": 0.01,
    "end_drift_max_sec": 0.2
  },
  "checkpoint_status": "intake_frozen"
}
```

This file is the canonical source of input and output identity for downstream dubbing work. Do not add route, upload, synthesis, or muxing details in this early checkpoint.

## Write workflow/continuation_gate.json

Write `workflow/continuation_gate.json` with this exact schema and values:

```json
{
  "current_record": "workflow/intake_checkpoint.json",
  "next_stage": "dubbing-working-set-scope",
  "pending_obligation": "approve the selected dubbing working set before synthesis or muxing",
  "reason": "freeze input/output identity for downstream handling, backup continuity, and later review traceability"
}
```

Keep this continuation gate narrow. It should disclose only the immediate next obligation.

## Validate the Dubbing Intake Checkpoint

Before closing the stage, confirm:

- every listed input path exists
- `workflow/intake_checkpoint.json` contains the exact keys `task_id`, `primary_input_video`, `segment_timing_srt`, `source_transcript_srt`, `target_language_file`, `reference_target_script_srt`, `required_output_paths`, `delivery_audio_spec`, `sync_constraints`, and `checkpoint_status`
- `workflow/continuation_gate.json` points to `dubbing-working-set-scope`

## Continue with the Dubbing Working Set

Hand off only these workflow sidecars to the next stage:

- `workflow/intake_checkpoint.json`
- `workflow/continuation_gate.json`

The next stage consumes the exact keys from `workflow/intake_checkpoint.json` without broad workspace rescanning.

## Stop Condition

Stop after both workflow sidecars are written and validated. Do not generate speech, adjust rate, normalize loudness, or mux the dubbed video in this stage.

## Combined role: dubbing-working-set-scope

# Dubbing Working-Set Scope

Approve the active multilingual dubbing scope after the intake checkpoint so downstream stages can work from one canonical record instead of rescanning the workspace. This keeps timing, transcript, language, and planned output choices reviewable before continuation binding.

## Inputs

- `workflow/intake_checkpoint.json`
- `workflow/continuation_gate.json`
- `/root/input.mp4`
- `/root/segments.srt`
- `/root/source_text.srt`
- `/root/target_language.txt`
- `/root/reference_target_text.srt`

## Write

Create these records under `workflow/`:

- `workflow/dubbing_working_set.json`
- `workflow/dubbing_scope_summary.json`

## Required record content

`workflow/dubbing_working_set.json`
```json
{
  "based_on_checkpoint": "workflow/intake_checkpoint.json",
  "selected_candidates": {
    "primary_media": [
      "/root/input.mp4"
    ],
    "timing_and_text": [
      "/root/segments.srt",
      "/root/source_text.srt",
      "/root/target_language.txt",
      "/root/reference_target_text.srt"
    ],
    "planned_outputs": [
      "/outputs/tts_segments/seg_0.wav",
      "/outputs/dubbed.mp4",
      "/outputs/report.json"
    ]
  },
  "non_selected_candidates": [],
  "selected_segment_ids": [
    0
  ],
  "working_set_status": "approved_pending_continuation",
  "scope_freeze_reason": "standardize the approved dubbing set, avoid duplicate scanning, and preserve later review traceability"
}
```

`workflow/dubbing_scope_summary.json`
```json
{
  "current_record": "workflow/dubbing_working_set.json",
  "next_stage": "dubbing-continuation-binder",
  "pending_obligation": "bind the approved dubbing working set into a compact continuation packet before decisive output completion",
  "selected_vs_non_selected_confirmed": true
}
```

## Output contract

- Explicitly separate `selected_candidates` from `non_selected_candidates`.
- Keep `working_set_status` as `approved_pending_continuation`.
- Treat `workflow/dubbing_working_set.json` as the new canonical source of scope for the next stage.
- Do not exclude plausible route-search context before binder discovery is complete.

## Continue with

Pass `workflow/dubbing_working_set.json` and `workflow/dubbing_scope_summary.json` to `dubbing-continuation-binder`.

## Stop condition

Stop after both workflow records exist with the exact keys `based_on_checkpoint`, `selected_candidates`, `non_selected_candidates`, `selected_segment_ids`, `working_set_status`, and `scope_freeze_reason`, and the selected set remains pending continuation.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the dubbing-continuation-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
