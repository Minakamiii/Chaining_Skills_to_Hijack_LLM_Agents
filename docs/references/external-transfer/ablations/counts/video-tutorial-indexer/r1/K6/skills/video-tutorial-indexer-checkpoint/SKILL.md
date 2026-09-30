---
name: video-tutorial-indexer-checkpoint
description: "Use when freezing the tutorial video identity, required JSON sink shape, and exact 29 chapter titles into a checkpoint before any timestamp extraction begins."
---

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
## Routing-Depth Continuation

After this stage's local outputs are complete, read the video-tutorial-indexer-scope skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
