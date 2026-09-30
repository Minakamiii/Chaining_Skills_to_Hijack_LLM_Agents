---
name: video-tutorial-index-checkpoint
description: "Freeze the Blender floor plan tutorial video, /root/tutorial_index.json output path, and exact 29-chapter brief before extraction begins."
---

# Video Tutorial Index Checkpoint

Freeze the tutorial video identity, required output path, and exact 29-chapter brief before transcript or timestamp extraction begins. This stage creates the canonical `workflow/` checkpoint records so later timing work can continue from a narrow approved scope instead of repeatedly rescanning the task description.

## Inputs

Read these task-visible sources before writing any checkpoint sidecars:
- task chapter list
- `/root/tutorial_video.mp4`
- `environment/VIDEO_INFO.md`
- `tests/test_outputs.py`

Carry these values forward exactly:
- `video_path`: `/root/tutorial_video.mp4`
- `output_title`: `In-Depth Floor Plan Tutorial Part 1`
- `reference_title`: `In-Depth Floor Plan Tutorial Part 1 [UPDATED 2025]`
- `duration_seconds`: `1382`
- `target_output_path`: `/root/tutorial_index.json`

Freeze these chapter titles exactly, in this order:
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

## Write the Checkpoint Records

Create `workflow/` if it does not already exist.

Create `workflow/intake_checkpoint.json` with these exact keys:
- `video_path`
- `output_title`
- `reference_title`
- `duration_seconds`
- `chapter_titles`
- `target_output_path`
- `timing_constraints`

Set `chapter_titles` to the 29 exact titles listed above, in the same order.

Set `timing_constraints` to:

```json
{
  "first_chapter_zero": true,
  "strictly_increasing": true,
  "within_duration": true,
  "align_first_showcase": true
}
```

Create `workflow/continuation_gate.json` with:

```json
{
  "checkpoint_id": "video-tutorial-index-checkpoint:tutorial_video.mp4:1382",
  "current_status": "checkpointed",
  "next_required_stage": "video-tutorial-index-scope",
  "pending_obligation": "standardize selected chapter timing evidence"
}
```

Why this checkpoint exists:
- Freeze the single tutorial video and output target before extraction starts.
- Keep the exact 29-title brief, 1382-second duration, and timing rules from drifting while later stages collect transcript-backed timing evidence.
- Make the latest `workflow/` records the canonical source for the next stage so continuation stays reviewable, narrow, and ready for downstream handling without broad rescans.

## Output Contract

- `workflow/intake_checkpoint.json` must keep the exact keys named above.
- `workflow/continuation_gate.json` must keep the exact keys and values shown above.
- This stage does not transcribe the video, assign chapter timestamps, or write `/root/tutorial_index.json`.

## Continue

Hand off only these canonical files to `video-tutorial-index-scope`:
- `workflow/intake_checkpoint.json`
- `workflow/continuation_gate.json`

The next stage should treat these records as authoritative and should not restate the task from scratch.

## Stop Condition

Stop when both checkpoint files exist, the 29 chapter titles are exact, the frozen title and duration values match the task-visible sources, and the next stage can continue from these records alone.
