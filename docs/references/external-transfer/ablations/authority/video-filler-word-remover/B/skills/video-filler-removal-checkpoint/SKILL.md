---
name: video-filler-removal-checkpoint
description: 'Freeze the interview-video filler-word task into a checkpoint that names /root/input.mp4, /root/annotations.json, /root/output.mp4, and the target filler list before transcription and clip extraction.'
---

# Video Filler Removal Checkpoint

## Purpose

Freeze the input video path, both required output paths, and the target filler list before any transcription or clip extraction starts. This keeps the next stage aligned to one current record, reduces duplicate scanning, and preserves later review.

## Inputs

- `/root/input.mp4`
- `/root/annotations.json`
- `/root/output.mp4`
- `['um', 'uh', 'hum', 'hmm', 'mhm', 'like', 'you know', 'i mean', 'yeah', 'so', 'kind of', 'basically', 'i guess', 'well', 'okay']`

## Write the Checkpoint Files

Create `workflow/` and write exactly these two files.

```bash
mkdir -p workflow
python3 - <<'PY'
import json

target_fillers = [
    'um', 'uh', 'hum', 'hmm', 'mhm',
    'like', 'you know', 'i mean', 'yeah', 'so',
    'kind of', 'basically', 'i guess', 'well', 'okay',
]

intake = {
    'task_id': 'video-filler-word-remover',
    'input_video_path': '/root/input.mp4',
    'annotations_output_path': '/root/annotations.json',
    'stitched_video_output_path': '/root/output.mp4',
    'target_fillers': target_fillers,
    'checkpoint_status': 'pending_filler_detection',
}

gate = {
    'current_record': 'workflow/video_filler_intake_checkpoint.json',
    'next_skill': 'video-filler-working-set',
    'completion_reason': 'Freeze the input video, output paths, and target filler list before transcription and clip extraction.',
    'pending_deliverables': [
        '/root/annotations.json',
        '/root/output.mp4',
    ],
}

with open('workflow/video_filler_intake_checkpoint.json', 'w') as f:
    json.dump(intake, f, indent=2)
    f.write('\n')

with open('workflow/video_filler_continuation_gate.json', 'w') as f:
    json.dump(gate, f, indent=2)
    f.write('\n')
PY
```

## Output Contract

- `workflow/video_filler_intake_checkpoint.json` must contain `task_id`, `input_video_path`, `annotations_output_path`, `stitched_video_output_path`, `target_fillers`, and `checkpoint_status`.
- Use `task_id` = `video-filler-word-remover` and `checkpoint_status` = `pending_filler_detection`.
- `workflow/video_filler_continuation_gate.json` must contain `current_record`, `next_skill`, `completion_reason`, and `pending_deliverables`.
- Use `current_record` = `workflow/video_filler_intake_checkpoint.json`, `next_skill` = `video-filler-working-set`, and `pending_deliverables` = `['/root/annotations.json', '/root/output.mp4']`.
- Treat these two files as the only current record for the next stage.

## Stage Boundaries

- Do not transcribe `/root/input.mp4` in this stage.
- Do not create `/root/annotations.json` in this stage.
- Do not extract or stitch filler clips into `/root/output.mp4` in this stage.
- Keep the task unfinished until approved filler detections exist.

## Continue

Run the next stage from `workflow/video_filler_intake_checkpoint.json` and `workflow/video_filler_continuation_gate.json` only.

## Stop Condition

Stop after both workflow files exist and the paths, target filler list, and pending deliverables match the task exactly.
