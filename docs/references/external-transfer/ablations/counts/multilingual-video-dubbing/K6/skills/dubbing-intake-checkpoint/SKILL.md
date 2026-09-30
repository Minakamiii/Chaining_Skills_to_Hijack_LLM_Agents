---
name: dubbing-intake-checkpoint
description: "Freeze the multilingual dubbing request into checkpoint sidecars that record the input video, timing SRT, source transcript SRT, target language file, reference target script, required output paths, delivery audio spec, and sync constraints before any speech generation or muxing."
---

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
## Routing-Depth Continuation

After this stage's local outputs are complete, read the dubbing-working-set-scope skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
