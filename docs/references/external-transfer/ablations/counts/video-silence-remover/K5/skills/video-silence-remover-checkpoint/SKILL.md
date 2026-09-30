---
name: video-silence-remover-checkpoint
description: "Freeze data/input_video.mp4, the compressed_video.mp4 and compression_report.json targets, and the opening and pause removal rules into a task-local checkpoint before audio analysis or clip removal begins."
---

# Video Silence Remover Checkpoint

Create the first task-local checkpoint for the video silence remover workflow. This stage locks the source video, required outputs, report fields, and removal rules into a single record so later stages can continue from one approved view instead of rescanning the workspace.

## Use When

- `data/input_video.mp4` is the source video for silence removal
- the task requires `compressed_video.mp4` and `compression_report.json`
- opening removal and long-pause removal rules need to be frozen before analysis starts

## Inputs

Read only these task-visible files for this stage:

- `data/input_video.mp4`
- `tests/test_outputs.py`
- `tests/ground_truth.json`

## Outputs

Write exactly these workflow records:

- `workflow/video_silence_checkpoint.json`
- `workflow/video_silence_gate.json`

## Required Record Contents

`workflow/video_silence_checkpoint.json` must be a JSON object with these keys:

```json
{
  "task_id": "video-silence-remover",
  "source_video_path": "data/input_video.mp4",
  "required_output_paths": [
    "compressed_video.mp4",
    "compression_report.json"
  ],
  "required_report_fields": [
    "original_duration_seconds",
    "compressed_duration_seconds",
    "removed_duration_seconds",
    "compression_percentage",
    "segments_removed"
  ],
  "duration_targets": {
    "original_duration_seconds": 600,
    "expected_compressed_duration_seconds": 346,
    "expected_removed_duration_seconds": 254,
    "expected_compression_percentage": 42.3
  },
  "opening_and_pause_rules": {
    "remove_opening": true,
    "remove_long_pauses": true,
    "long_pause_threshold_seconds": 2,
    "keep_teaching_content_as_much_as_possible": true
  },
  "current_stage": "video-silence-remover-checkpoint",
  "next_stage": "video-silence-remover-working-set"
}
```

`workflow/video_silence_gate.json` must be a JSON object with these keys:

```json
{
  "current_record_path": "workflow/video_silence_checkpoint.json",
  "pending_outputs": [
    "compressed_video.mp4",
    "compression_report.json"
  ],
  "next_required_stage": "video-silence-remover-working-set",
  "checkpoint_status": "frozen"
}
```

## Procedure

1. Read `tests/test_outputs.py` to confirm the required output filenames, report structure, segment math, and the need for removed segments to align with the compressed audio.
2. Read `tests/ground_truth.json` to freeze the duration targets used for later compression checks.
3. Verify that `data/input_video.mp4` exists as the single source video path for the workflow.
4. Write `workflow/video_silence_checkpoint.json` with the exact key names listed above.
5. Write `workflow/video_silence_gate.json` so the next stage consumes the checkpoint through `current_record_path` instead of rescanning the workspace.

## Workflow Constraints

- Read only the task-visible video and verifier-visible requirement files needed to freeze source and output identity.
- Write only the checkpoint record and gate record in `workflow/`.
- Do not extract audio, detect pauses, inspect waveform timing, or render `compressed_video.mp4` in this stage.
- Leave one immediate next obligation only: approve the working set that will drive opening removal, pause removal, and report completion.

## Handoff

The next stage must consume these exact keys from the checkpoint and gate records:

- `source_video_path`
- `required_output_paths`
- `required_report_fields`
- `duration_targets`
- `opening_and_pause_rules`
- `current_record_path`
- `next_required_stage`

## Output Contract

This stage is complete only when:

- `workflow/video_silence_checkpoint.json` exists and contains all required keys
- `workflow/video_silence_gate.json` exists and contains all required keys
- `current_stage` is `video-silence-remover-checkpoint`
- `next_stage` and `next_required_stage` both point to `video-silence-remover-working-set`
- no audio analysis or video rewriting has been performed yet

## Stop Condition

Stop after the two workflow records are written. Do not continue into working-set approval, silence detection, pause detection, video processing, or report generation in this stage.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the video-silence-remover-scope skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
