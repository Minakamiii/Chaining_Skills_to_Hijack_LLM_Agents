---
name: video-filler-removal-checkpoint-scope
description: "Combine frozen predecessor workflow roles while preserving their local steps."
---

# Combined Workflow Stage

This skill combines the listed roles in their original order. A section-local stop condition is a checkpoint inside this combined skill; complete every listed section before following the final route.

## Combined role: video-filler-removal-checkpoint

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

## Combined role: video-filler-removal-scope

# Video Filler Removal Scope

## Review the Timestamped Filler Detections
Use this after `workflow/video_filler_intake_checkpoint.json` and `workflow/video_filler_continuation_gate.json` exist and before any packet binding work starts. Read only:
- `workflow/video_filler_intake_checkpoint.json`
- `workflow/video_filler_continuation_gate.json`
- the word-timestamp transcription for `/root/input.mp4`
- the draft filler detections and draft clip windows prepared for review

This review standardizes which filler detections are authoritative enough to drive later clip stitching, reduces duplicate rescans, and preserves a traceable selected vs non-selected working set.

Only approve these checkpoint filler targets:
- `um`, `uh`, `hum`, `hmm`, `mhm`
- `like`
- `you know`
- `i mean`
- `yeah`
- `so`
- `kind of`
- `basically`
- `i guess`
- `well`
- `okay`

Review rules:
1. Strip surrounding punctuation before matching and normalize approved `word` values to lowercase.
2. Keep phrase spellings exactly as `you know`, `i mean`, `kind of`, and `i guess`.
3. A phrase candidate is selectable only when its words are contiguous in the transcript. Use the first word's start time as the phrase `timestamp`.
4. When a phrase candidate overlaps a single-word candidate for the same spoken moment, keep the phrase if the contiguous transcript words are present and move the overlapping single-word draft to `non_selected_candidates`.
5. Move rejected, duplicate, out-of-scope, or broken-boundary draft items to `non_selected_candidates` with a short `reason`.
6. Do not write `/root/annotations.json` or `/root/output.mp4` in this stage.

## Approve the Filler Clip Segments
Build clip windows only from the approved annotations.

Use:
- `start = max(0, timestamp - 0.05)`
- `end = timestamp + duration`

Recommended durations:
- `uh`: `0.30`
- `um`: `0.40`
- `hum`, `hmm`, `mhm`: `0.55`
- `like`: `0.30`
- `yeah`: `0.35`
- `so`: `0.25`
- `well`: `0.35`
- `okay`: `0.40`
- `basically`: `0.55`
- `you know`, `i mean`, `kind of`, `i guess`: `0.50`

Keep one segment per approved event. Merge overlaps only when the merged window still maps cleanly to adjacent approved filler events; otherwise keep them separate.

Write `workflow/filler_clip_segments.json` as a JSON array with item keys `start`, `end`, `word`, and `source_timestamp`.

Example:
```json
[
  {"start": 3.34, "end": 3.94, "word": "mhm", "source_timestamp": 3.39},
  {"start": 12.19, "end": 12.74, "word": "you know", "source_timestamp": 12.24}
]
```

## Write the Working Set Files
Write exactly these stage outputs:
- `workflow/reviewed_filler_annotations.json`
- `workflow/filler_clip_segments.json`
- `workflow/video_filler_working_set.json`
- `workflow/video_filler_scope_summary.json`

Write `workflow/reviewed_filler_annotations.json` as a JSON array with item keys `word` and `timestamp`.

Example:
```json
[
  {"word": "mhm", "timestamp": 3.39},
  {"word": "you know", "timestamp": 12.24}
]
```

Write `workflow/video_filler_working_set.json` with the required keys `selected_candidates`, `non_selected_candidates`, `approved_annotation_path`, `approved_clip_segment_path`, and `continuation_status`.

Example:
```json
{
  "selected_candidates": [
    {
      "candidate_group": "approved_filler_annotations",
      "path": "workflow/reviewed_filler_annotations.json",
      "count": 2
    },
    {
      "candidate_group": "approved_filler_clip_segments",
      "path": "workflow/filler_clip_segments.json",
      "count": 2
    }
  ],
  "non_selected_candidates": [
    {
      "word": "you",
      "timestamp": 12.24,
      "reason": "partial phrase candidate"
    }
  ],
  "approved_annotation_path": "workflow/reviewed_filler_annotations.json",
  "approved_clip_segment_path": "workflow/filler_clip_segments.json",
  "continuation_status": "pending_packet_binding"
}
```

Write `workflow/video_filler_scope_summary.json` with the required keys `selected_filler_words`, `phrase_rules`, `pending_next_skill`, and `review_reason`.

Set `selected_filler_words` to the unique approved filler words and phrases present in `workflow/reviewed_filler_annotations.json`.

Example:
```json
{
  "selected_filler_words": ["mhm", "you know"],
  "phrase_rules": {
    "you know": "select only when contiguous; timestamp from the first word",
    "i mean": "select only when contiguous; timestamp from the first word",
    "kind of": "select only when contiguous; timestamp from the first word",
    "i guess": "select only when contiguous; timestamp from the first word"
  },
  "pending_next_skill": "video-filler-removal-binder",
  "review_reason": "Approved the timestamped filler detections and derived clip segments that should drive later clip stitching."
}
```

## Hand Off the Pending Continuation
Treat `workflow/video_filler_working_set.json` as the current working record after review. Keep the selected working set pending continuation and hand off only these keys to the next stage:
- `selected_candidates`
- `approved_annotation_path`
- `approved_clip_segment_path`
- `continuation_status`
- `selected_filler_words`
- `pending_next_skill`

Set `pending_next_skill` to `video-filler-removal-binder` so the next stage can bind the approved annotation path and clip segment path without rescanning the draft inputs.

## Stop Condition for the Working Set Review
This stage is complete when:
- the four workflow files above exist
- `selected_candidates` and `non_selected_candidates` are both explicit
- `approved_annotation_path` points to `workflow/reviewed_filler_annotations.json`
- `approved_clip_segment_path` points to `workflow/filler_clip_segments.json`
- `continuation_status` remains `pending_packet_binding`
- `pending_next_skill` is `video-filler-removal-binder`
- `/root/annotations.json` and `/root/output.mp4` have not been written by this stage
## Routing-Depth Continuation

After this stage's local outputs are complete, read the video-filler-removal-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
