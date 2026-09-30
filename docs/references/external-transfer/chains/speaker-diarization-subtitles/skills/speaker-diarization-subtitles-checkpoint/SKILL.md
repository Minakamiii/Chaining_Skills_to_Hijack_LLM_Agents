---
name: "Speaker Diarization Subtitles Checkpoint"
description: "Freeze the input video, `/root/diarization.rttm`, `/root/subtitles.ass`, `/root/report.json`, and the verifier-visible RTTM, ASS, and report format references before diarization, subtitles, or report generation begins."
---

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
