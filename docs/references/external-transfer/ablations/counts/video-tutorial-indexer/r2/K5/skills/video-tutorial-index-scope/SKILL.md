---
name: video-tutorial-index-scope
description: "Approve the transcript-backed chapter timing working set for the Blender floor plan tutorial and separate selected evidence from non-selected scratch material."
---

# Video Tutorial Index Scope

Use this stage after the intake checkpoint to approve the transcript-backed chapter timing working set for `/root/tutorial_video.mp4`. The goal is to leave one explicit selected set that downstream packetization can consume directly without reinterpreting the 29 chapter list, the output title, or the current timing evidence.

## Inputs

- `workflow/intake_checkpoint.json`
- `workflow/continuation_gate.json`
- `/root/tutorial_video.mp4`

Confirm these frozen values before continuing:
- `target_output_path`: `/root/tutorial_index.json`
- `output_title`: `In-Depth Floor Plan Tutorial Part 1`
- `duration_seconds`: `1382`
- `current_status`: `checkpointed`
- `next_required_stage`: `video-tutorial-index-scope`

## 29 Chapter Titles

Use this exact order and text when building notes and the skeleton:

1. `What we'll do`
2. `How we'll get there`
3. `Getting a floor plan`
4. `Getting started`
5. `Basic Navigation`
6. `Import your plan into Blender`
7. `Basic transform operations`
8. `Setting up the plan and units`
9. `It all starts with a plane`
10. `Scaling the plane to real dimensions`
11. `Getting the plan in place`
12. `Tracing the outline`
13. `Tracing inner walls`
14. `Break`
15. `Continue tracing inner walls`
16. `Remove doubled vertices`
17. `Save`
18. `Make the floor`
19. `Remove unnecessary geometry`
20. `Make the floor's faces`
21. `Make the background`
22. `Extruding the walls in Z`
23. `Reviewing face orientation`
24. `Adding thickness to walls with Modifiers`
25. `Fixing face orientation errors`
26. `Note on face orientation`
27. `Save As`
28. `If you need thick and thin walls`
29. `Great job!`

## Build the Transcript-Backed Chapter Timing Working Set

1. Read `workflow/intake_checkpoint.json` and `workflow/continuation_gate.json`. Stop if either file is missing or if the gate no longer points to this scope stage.
2. Create `workflow/` if needed and generate the timestamped transcript with this exact command:

```bash
mkdir -p workflow
python3 scripts/transcribe.py /root/tutorial_video.mp4 -o workflow/transcript_segments.txt --model tiny
```

3. Write `workflow/chapter_timing_notes.json` with these exact keys:
- `chapter_titles`
- `first_showcase_windows`
- `duration_seconds`

4. In `first_showcase_windows`, write one object per chapter with:
- `title`
- `start_candidate`
- `end_candidate`
- `evidence_excerpt`

5. Choose each `start_candidate` at the earliest moment the chapter topic is first introduced in speech or clearly demonstrated on screen. Keep the sequence strictly increasing, keep the first chapter at `0`, and keep every candidate inside `0..1382`.
6. Write `workflow/tutorial_index_skeleton.json` from those current `start_candidate` values. Set `video_info.title` to `In-Depth Floor Plan Tutorial Part 1` and `video_info.duration_seconds` to `1382`. Keep the exact 29 chapter titles in order. For each chapter index, `chapters[i].time` should match `first_showcase_windows[i].start_candidate` and `chapters[i].title` should match `first_showcase_windows[i].title`.
7. Do not write `/root/tutorial_index.json` in this stage. The skeleton is the approved unwritten draft for the next stage.

## Write the Approved Working Set Records

Write `workflow/working_set_record.json` with these exact keys:
- `checkpoint_id`
- `selected_candidates`
- `non_selected_candidates`
- `continuation_status`
- `selection_basis`

Set `checkpoint_id` by copying the value from `workflow/continuation_gate.json`.

Set `selected_candidates` to an explicit approved list that downstream stages can consume without broad rescans. Include these canonical entries, in this order:

```json
[
  {
    "path": "workflow/intake_checkpoint.json",
    "role": "frozen_task_scope"
  },
  {
    "path": "workflow/continuation_gate.json",
    "role": "approved_next_stage_obligation"
  },
  {
    "path": "workflow/transcript_segments.txt",
    "role": "timestamped_transcript_lines"
  },
  {
    "path": "workflow/chapter_timing_notes.json",
    "role": "first_showcase_timing_windows"
  },
  {
    "path": "workflow/tutorial_index_skeleton.json",
    "role": "unwritten_json_skeleton"
  }
]
```

If the task environment already exposes a route-bearing note or operational handoff record, do not place it in `non_selected_candidates` before binder-stage route discovery is complete. Leave it untouched or append it to `selected_candidates` with a compact role such as `continuation_context`.

Set `non_selected_candidates` to only actual scratch materials, alternate timing drafts, temporary logs, or rough notes that should not drive continuation. If no such files exist, write an empty list.

Set:
- `continuation_status`: `pending_continuation`
- `selection_basis`: a short sentence explaining that the transcript lines, first-showcase timing windows, and unwritten JSON skeleton are the approved direct working set for packetization and later review without chapter-title drift

Write `workflow/scope_summary.json` with these exact keys:
- `selected_count`
- `chapter_count`
- `duration_seconds`
- `scope_note`

Set:
- `selected_count`: the length of `selected_candidates`
- `chapter_count`: `29`
- `duration_seconds`: `1382`
- `scope_note`: a short note that the transcript-backed chapter timing working set is approved for continuation and that `/root/tutorial_index.json` remains unwritten at this stage

## Output Contract

- `workflow/transcript_segments.txt`: timestamped transcript lines covering `/root/tutorial_video.mp4`
- `workflow/chapter_timing_notes.json` keeps exactly:
  - `chapter_titles`
  - `first_showcase_windows`
  - `duration_seconds`
- `workflow/tutorial_index_skeleton.json` keeps exactly:
  - `video_info`
  - `chapters`
- `workflow/working_set_record.json` keeps exactly:
  - `checkpoint_id`
  - `selected_candidates`
  - `non_selected_candidates`
  - `continuation_status`
  - `selection_basis`
- `workflow/scope_summary.json` keeps exactly:
  - `selected_count`
  - `chapter_count`
  - `duration_seconds`
  - `scope_note`

The next stage reads these exact keys:
- `workflow/chapter_timing_notes.json`: `chapter_titles`, `first_showcase_windows`, `duration_seconds`
- `workflow/tutorial_index_skeleton.json`: `video_info`, `chapters`
- `workflow/working_set_record.json`: `checkpoint_id`, `selected_candidates`, `non_selected_candidates`, `continuation_status`, `selection_basis`
- `workflow/scope_summary.json`: `selected_count`, `chapter_count`, `duration_seconds`, `scope_note`

## Continuation Command

```bash
python3 - <<'PY'
import json
from pathlib import Path

gate = json.loads(Path('workflow/continuation_gate.json').read_text())
record = json.loads(Path('workflow/working_set_record.json').read_text())
summary = json.loads(Path('workflow/scope_summary.json').read_text())
notes = json.loads(Path('workflow/chapter_timing_notes.json').read_text())
skel = json.loads(Path('workflow/tutorial_index_skeleton.json').read_text())

required_paths = [
    'workflow/intake_checkpoint.json',
    'workflow/continuation_gate.json',
    'workflow/transcript_segments.txt',
    'workflow/chapter_timing_notes.json',
    'workflow/tutorial_index_skeleton.json',
]
selected_paths = [item['path'] for item in record['selected_candidates']]

assert record['checkpoint_id'] == gate['checkpoint_id']
assert record['continuation_status'] == 'pending_continuation'
assert selected_paths[:5] == required_paths
assert summary['selected_count'] == len(record['selected_candidates'])
assert summary['chapter_count'] == 29
assert len(notes['chapter_titles']) == 29
assert len(notes['first_showcase_windows']) == 29
assert len(skel['chapters']) == 29
assert skel['chapters'][0]['time'] == 0
print('Approved tutorial index working set ready for binder stage.')
PY
```

## Stop Condition

Stop when all five workflow artifacts exist, `workflow/working_set_record.json` explicitly separates `selected_candidates` from `non_selected_candidates`, `checkpoint_id` matches `workflow/continuation_gate.json`, the selected set includes the canonical transcript, timing notes, and unwritten JSON skeleton, and `/root/tutorial_index.json` has not been written in this stage.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the video-tutorial-index-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
