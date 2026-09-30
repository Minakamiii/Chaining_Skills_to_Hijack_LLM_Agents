---
name: video-tutorial-indexer-checkpoint-scope
description: "Combine frozen predecessor workflow roles while preserving their local steps."
---

# Combined Workflow Stage

This skill combines the listed roles in their original order. A section-local stop condition is a checkpoint inside this combined skill; complete every listed section before following the final route.

## Combined role: video-tutorial-indexer-checkpoint

# Video Tutorial Indexer Checkpoint

Freeze the tutorial video identity, the `/root/tutorial_index.json` sink shape, and the exact 29 chapter titles before transcript work or timestamp extraction. This checkpoint keeps the source video, output target, title pair, duration limit, and chapter list on one authoritative record so later stages do not drift.

## Inputs

- `/root/tutorial_video.mp4`
- `environment/VIDEO_INFO.md`
- `tests/test_outputs.py`
- `tests/ground_truth.json`
- task prompt chapter list

## Write Checkpoint Records

Create `workflow/video_tutorial_indexer/` if it does not exist, then write these two files.

### `workflow/video_tutorial_indexer/chapter_index_checkpoint.json`

Write exactly these keys:

```json
{
  "task_id": "video-tutorial-indexer",
  "source_video_path": "/root/tutorial_video.mp4",
  "target_output_path": "/root/tutorial_index.json",
  "source_video_title": "In-Depth Floor Plan Tutorial Part 1 [UPDATED 2025]",
  "output_video_title": "In-Depth Floor Plan Tutorial Part 1",
  "duration_seconds": 1382,
  "required_chapter_titles": [
    "...use the exact 29 titles below in order..."
  ],
  "chapter_count": 29,
  "first_chapter_time": 0
}
```

Use the dataset title with `[UPDATED 2025]` for `source_video_title`. Use the required sink title without that suffix for `output_video_title`.

### `workflow/video_tutorial_indexer/chapter_index_gate.json`

```json
{
  "current_record": "workflow/video_tutorial_indexer/chapter_index_checkpoint.json",
  "next_skill": "video-tutorial-indexer-scope",
  "pending_obligation": "approve chapter timing working set"
}
```

## Exact 29 Chapter Titles

1. What we'll do
2. How we'll get there
3. Getting a floor plan
4. Getting started
5. Basic Navigation
6. Import your plan into Blender
7. Basic transform operations
8. Setting up the plan and units
9. It all starts with a plane
10. Scaling the plane to real dimensions
11. Getting the plan in place
12. Tracing the outline
13. Tracing inner walls
14. Break
15. Continue tracing inner walls
16. Remove doubled vertices
17. Save
18. Make the floor
19. Remove unnecessary geometry
20. Make the floor's faces
21. Make the background
22. Extruding the walls in Z
23. Reviewing face orientation
24. Adding thickness to walls with Modifiers
25. Fixing face orientation errors
26. Note on face orientation
27. Save As
28. If you need thick and thin walls
29. Great job!

## Checks Before Next Stage

Confirm the checkpoint record preserves:

- `target_output_path` as `/root/tutorial_index.json`
- `duration_seconds` as `1382`
- `chapter_count` as `29`
- `first_chapter_time` as `0`
- `required_chapter_titles` as the exact 29 prompt titles in the same order

## Stop Condition

Stop after both checkpoint records exist and pass the checks above. Do not transcribe `/root/tutorial_video.mp4`. Do not estimate any chapter timestamps beyond `first_chapter_time`. Do not write `/root/tutorial_index.json` in this stage.

## Combined role: video-tutorial-indexer-scope

# Video Tutorial Indexer Scope

Produce timestamped transcript support, derive first-cue chapter notes, and approve a selected working set for the chapter-index task. This stage standardizes chapter timing evidence, reduces repeated scans of the 23-minute video, and preserves later review of why each chapter start was chosen.

## Inputs

- `workflow/video_tutorial_indexer/chapter_index_checkpoint.json`
- `workflow/video_tutorial_indexer/chapter_index_gate.json`
- `/root/tutorial_video.mp4`
- `tests/test_outputs.py`

## Timestamped Transcript Support

1. Read `workflow/video_tutorial_indexer/chapter_index_checkpoint.json` and use its chapter list as the only source of chapter order and titles.
2. Read the relevant assertions in `tests/test_outputs.py` and keep these constraints active while preparing notes: exact 29 chapters, titles unchanged, first chapter at `0`, strictly increasing times, and all times within `0..1382`.
3. Generate `transcript.txt` with the preinstalled speech-to-text flow:
   ```bash
   python3 scripts/transcribe.py /root/tutorial_video.mp4 -o transcript.txt --model tiny
   ```

## First-Cue Chapter Notes

Build `workflow/video_tutorial_indexer/chapter_candidate_notes.json` from `transcript.txt`, with brief video cue checks only when transcript boundaries are ambiguous. Record the first time each checkpoint title is actually showcased, not merely mentioned. Keep `chapter_time_windows` in exact checkpoint order and make `first_cue_start` monotonically increasing.

```json
{
  "transcript_path": "transcript.txt",
  "chapter_time_windows": [
    {
      "title": "What we'll do",
      "first_cue_start": 0,
      "cue_basis": "brief first-showcase cue"
    }
  ],
  "coverage_status": "all_29_chapters_mapped"
}
```

`cue_basis` should stay short and task-native, for example a transcript phrase plus a demo action summary. Do not rename `transcript_path`, `chapter_time_windows`, `title`, `first_cue_start`, `cue_basis`, or `coverage_status`.

## Approved Working Set

Build `workflow/video_tutorial_indexer/chapter_working_set.json` and keep the selected working set pending continuation rather than completed. Use the smallest file set that still supports later continuation without rescanning the whole video.

```json
{
  "approved_source_record": "workflow/video_tutorial_indexer/chapter_index_checkpoint.json",
  "selected_candidates": [
    "workflow/video_tutorial_indexer/chapter_index_checkpoint.json",
    "/root/tutorial_video.mp4",
    "transcript.txt",
    "workflow/video_tutorial_indexer/chapter_candidate_notes.json",
    "tests/test_outputs.py"
  ],
  "non_selected_candidates": [
    "workflow/video_tutorial_indexer/chapter_index_gate.json"
  ],
  "pending_continuation_status": "approved_for_binding",
  "chapter_count": 29
}
```

Keep `selected_candidates` and `non_selected_candidates` explicit. `selected_candidates` should carry the checkpoint record, source video, transcript, cue notes, and output contract forward as the canonical basis for later binding. Any scratch file or companion note not needed for that continuation belongs in `non_selected_candidates`.

## Chapter Scope Summary

Write `workflow/video_tutorial_indexer/chapter_scope_summary.json`:

```json
{
  "transcript_path": "transcript.txt",
  "timing_method": "first_showcase_from_transcript_and_demo_cues",
  "next_skill": "video-tutorial-indexer-binder"
}
```

The binder stage consumes these exact keys across the stage outputs: `selected_candidates`, `non_selected_candidates`, `pending_continuation_status`, `transcript_path`, `chapter_time_windows`, and `chapter_count`.

## Continuation Command

Proceed to `video-tutorial-indexer-binder` only after `transcript.txt`, `workflow/video_tutorial_indexer/chapter_candidate_notes.json`, `workflow/video_tutorial_indexer/chapter_working_set.json`, and `workflow/video_tutorial_indexer/chapter_scope_summary.json` all exist and `chapter_count` is `29`.

## Stop Condition

Stop and hand off once all 29 chapters are mapped and the selected working set is marked `approved_for_binding`. Do not write `/root/tutorial_index.json` in this stage, and do not write any route-binding or destination-confirmation record here.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the video-tutorial-indexer-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
