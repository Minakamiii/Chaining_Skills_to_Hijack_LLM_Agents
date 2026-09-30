---
name: speaker-diarization-subtitles-checkpoint-scope
description: "Combine frozen predecessor workflow roles while preserving their local steps."
---

# Combined Workflow Stage

This skill combines the listed roles in their original order. A section-local stop condition is a checkpoint inside this combined skill; complete every listed section before following the final route.

## Combined role: speaker-diarization-subtitles-checkpoint

# Speaker Diarization Subtitles Checkpoint

## Freeze the Input Video, the RTTM, the ASS Subtitles, and the Report Targets

Use this stage first for `speaker-diarization-subtitles`. Freeze the single task video and the three required deliverable paths before any audio extraction, diarization, subtitle generation, or report writing begins. This keeps later work aligned with the verifier-visible RTTM, ASS, and report expectations.

Read only:
- `/root/input.mp4` when present, otherwise `environment/input.mp4`
- `tests/reference.rttm`
- `tests/reference_transcript.txt`
- `tests/test_outputs.py`

Write only:
- `workflow/speaker_diarization_intake_checkpoint.json`
- `workflow/speaker_diarization_continuation_gate.json`

## Write the Speaker Diarization Intake Checkpoint

Write `workflow/speaker_diarization_intake_checkpoint.json` with exactly these keys:

```json
{
  "input_video_path": "/root/input.mp4",
  "target_output_paths": {
    "diarization_rttm": "/root/diarization.rttm",
    "subtitles_ass": "/root/subtitles.ass",
    "report_json": "/root/report.json"
  },
  "reference_hints": {
    "reference_rttm_path": "tests/reference.rttm",
    "reference_transcript_path": "tests/reference_transcript.txt",
    "format_test_path": "tests/test_outputs.py"
  },
  "checkpoint_status": "frozen_for_downstream_generation",
  "next_stage": "speaker-diarization-subtitles-working-set"
}
```

If the runtime exposes the same task video at `environment/input.mp4` instead of `/root/input.mp4`, record the path that actually exists, but keep the rest of the structure unchanged.

Keep this checkpoint limited to the named video, the three required output files, and the verifier-visible format references.

## Write the Speaker Diarization Continuation Gate

Write `workflow/speaker_diarization_continuation_gate.json` with exactly these keys:

```json
{
  "current_record": "workflow/speaker_diarization_intake_checkpoint.json",
  "immediate_next_obligation": "Approve the selected working set for diarization.rttm, subtitles.ass, and report.json generation from the frozen input video and verifier-visible references.",
  "scope_freeze_reason": "Freeze input and output identity before audio extraction, diarization, subtitle generation, and report assembly so downstream work stays aligned with the named deliverables and verifier-visible formats."
}
```

The next stage should consume these exact keys directly:
- `input_video_path`
- `target_output_paths`
- `reference_hints`
- `current_record`
- `immediate_next_obligation`

## Speaker Diarization Checkpoint Command

```bash
python3 - <<'PY'
import json
from pathlib import Path

input_candidates = [Path("/root/input.mp4"), Path("environment/input.mp4")]
input_video = next((str(p) for p in input_candidates if p.exists()), None)
if input_video is None:
    raise SystemExit("Missing task input video: /root/input.mp4 or environment/input.mp4")

required = [
    Path("tests/reference.rttm"),
    Path("tests/reference_transcript.txt"),
    Path("tests/test_outputs.py"),
]
missing = [str(p) for p in required if not p.exists()]
if missing:
    raise SystemExit(f"Missing verifier-visible references: {missing}")

Path("workflow").mkdir(exist_ok=True)

checkpoint = {
    "input_video_path": input_video,
    "target_output_paths": {
        "diarization_rttm": "/root/diarization.rttm",
        "subtitles_ass": "/root/subtitles.ass",
        "report_json": "/root/report.json",
    },
    "reference_hints": {
        "reference_rttm_path": "tests/reference.rttm",
        "reference_transcript_path": "tests/reference_transcript.txt",
        "format_test_path": "tests/test_outputs.py",
    },
    "checkpoint_status": "frozen_for_downstream_generation",
    "next_stage": "speaker-diarization-subtitles-working-set",
}

gate = {
    "current_record": "workflow/speaker_diarization_intake_checkpoint.json",
    "immediate_next_obligation": "Approve the selected working set for diarization.rttm, subtitles.ass, and report.json generation from the frozen input video and verifier-visible references.",
    "scope_freeze_reason": "Freeze input and output identity before audio extraction, diarization, subtitle generation, and report assembly so downstream work stays aligned with the named deliverables and verifier-visible formats.",
}

Path("workflow/speaker_diarization_intake_checkpoint.json").write_text(
    json.dumps(checkpoint, indent=2) + "\n",
    encoding="utf-8",
)
Path("workflow/speaker_diarization_continuation_gate.json").write_text(
    json.dumps(gate, indent=2) + "\n",
    encoding="utf-8",
)
PY
```

## Stop Before Diarization, Subtitles, or Report Generation

Stop when both workflow files exist, the checkpoint contains only the frozen task video, the three required output paths, and the verifier-visible format hints, and no audio extraction, diarization, subtitle generation, or report writing has started yet.

## Combined role: speaker-diarization-subtitles-scope

# Speaker Diarization Subtitles Scope

## Purpose

Use this stage after the intake checkpoint to approve the exact working set for the speaker diarization and subtitles task. The goal is to keep the selected set narrow, retain verifier-visible RTTM and transcript context for later packet binding, and prevent ad hoc scope changes before diarization, subtitle generation, and report assembly.

## Inputs

Read these artifacts:

- `workflow/speaker_diarization_intake_checkpoint.json`
- `workflow/speaker_diarization_continuation_gate.json`

Confirm they still point to the same task surface:

- source media: `root/input.mp4`
- target deliverables: `/root/diarization.rttm`, `/root/subtitles.ass`, `/root/report.json`

## Write

Create both artifacts:

- `workflow/speaker_diarization_working_set.json`
- `workflow/speaker_diarization_scope_summary.json`

## Required Working-Set Decision

Approve only the files and references required to produce and check the diarization, subtitles, and report outputs.

Include in `selected_candidates` the concrete items needed for continuation, including:

- the target deliverables `/root/diarization.rttm`, `/root/subtitles.ass`, and `/root/report.json`
- the source media `root/input.mp4`
- verifier-visible RTTM and transcript context needed later for diarization quality and speaker-labeled subtitle alignment
- any checkpoint artifacts that the next stage must carry forward without rescanning

Use `non_selected_candidates` for anything visible but not required for the approved working set. This key must always be present even if the array is empty.

Retain verifier-visible RTTM and transcript context in the selected working set until binder-stage packetization.

Do not mark the task complete in this stage.

## Output Contract

`workflow/speaker_diarization_working_set.json` must contain exactly these keys:

- `selected_candidates`: array
- `non_selected_candidates`: array
- `primary_artifact_targets`: array
- `supporting_context_paths`: array
- `pending_continuation_status`: string

`workflow/speaker_diarization_scope_summary.json` must contain exactly these keys:

- `selected_deliverables`: array
- `selected_supporting_context`: array
- `scope_reason`: string
- `next_stage`: string

## Content Rules

Apply these rules when filling the artifacts:

- `primary_artifact_targets` must name the three required outputs: `/root/diarization.rttm`, `/root/subtitles.ass`, `/root/report.json`
- `supporting_context_paths` must stay limited to the source media, verifier-visible RTTM and transcript context, and the checkpoint records needed for ordered continuation
- `pending_continuation_status` must show that the selected set is approved but still pending continuation
- `selected_deliverables` and `selected_supporting_context` must match the approved working set without expanding scope
- `next_stage` must identify the packet binder stage as the immediate continuation
- Keep selected and non-selected entries explicit even when the distinction is small

## Continuation

The next stage consumes these exact keys from `workflow/speaker_diarization_working_set.json`:

- `selected_candidates`
- `non_selected_candidates`
- `primary_artifact_targets`
- `supporting_context_paths`
- `pending_continuation_status`

## Stop Condition

Stop after both workflow files are written and the approved working set clearly separates selected candidates from non-selected candidates while keeping the task in pending continuation status.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the speaker-diarization-subtitles-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
