---
name: "Multilingual Video Dubbing Reference Target Basis"
description: "Align multilingual video dubbing speech windows, source transcript, target language, and reference script into /outputs/workflow/reference_target_basis.json for duration control and report-ready segment text."
---

# Multilingual Video Dubbing Reference Target Basis

Use this after `/outputs/workflow/dubbing_intake_checkpoint.json` exists and before any TTS segment audio, dubbed video, or report is written. A timed basis is the natural next step because multilingual video dubbing needs one aligned view of `window_start_sec`, `window_end_sec`, `source_text`, and `target_text` before segment audio generation.

## When to Use

- `/outputs/workflow/dubbing_intake_checkpoint.json` already exists.
- The intake checkpoint still shows `reference_target_text_review_status=active_reference_script`.
- You need one aligned working record before generating `/outputs/tts_segments/seg_0.wav`.
- You want later stages to continue from `/outputs/workflow/reference_target_basis.json` instead of rereading `/root/reference_target_text.srt`.

## Consume the Intake Checkpoint

Read `/outputs/workflow/dubbing_intake_checkpoint.json` and consume these keys exactly:

- `input_video_path`
- `segment_windows`
- `source_text_segments`
- `target_language_code`
- `reference_target_text_segments`
- `original_media_info`
- `reference_target_text_path`
- `reference_target_text_review_status`

If any required key is missing or malformed, stop and repair the checkpoint instead of rebuilding this stage from raw task files.

## Write the Reference Target Basis Artifact

Write `/outputs/workflow/reference_target_basis.json` with these top-level keys:

- `workflow_stage`
- `input_video_path`
- `timed_dubbing_basis`
- `source_language_code`
- `target_language_code`
- `original_duration_sec`
- `reference_target_text_path`
- `reference_target_text_status`
- `reference_target_text_cleanup_reason`
- `reference_target_basis_path`

Set:

- `workflow_stage=reference_target_basis`
- `reference_target_text_path=/root/reference_target_text.srt`
- `reference_target_text_status=superseded_by_reference_target_basis`
- `reference_target_basis_path=/outputs/workflow/reference_target_basis.json`

Use `reference_target_text_cleanup_reason` to record that `timed_dubbing_basis` is now the canonical aligned view for later TTS timing and report-ready segment text, which avoids dual-source ambiguity.

## Align Speech Windows, Source Transcript, Target Language, and Reference Script

Build `timed_dubbing_basis` directly from the intake checkpoint.

For each segment:

1. Keep the checkpoint order stable.
2. Copy `window_start_sec` and `window_end_sec` from `segment_windows`.
3. Compute `window_duration_sec` as `window_end_sec - window_start_sec`.
4. Copy cleaned `source_text` from `source_text_segments`.
5. Copy cleaned `target_text` from `reference_target_text_segments`.
6. Preserve those fields in one row so the next stage can generate TTS and fill the report without reopening `/root/reference_target_text.srt`.

Keep `target_language_code` from the checkpoint. Set `source_language_code` from a checkpoint value if present; otherwise derive a stable language code from the checkpointed source transcript metadata before continuing. For the benchmark input, this should resolve to `en`.

## Validation and Stop Conditions

Before handing off:

- Confirm `len(segment_windows) == len(source_text_segments) == len(reference_target_text_segments)`.
- Confirm every `timed_dubbing_basis` row has `window_start_sec`, `window_end_sec`, `window_duration_sec`, `source_text`, and `target_text`.
- Confirm `original_duration_sec` is copied from `original_media_info`.
- Confirm `reference_target_text_path` still points to `/root/reference_target_text.srt`.
- Confirm `reference_target_text_status=superseded_by_reference_target_basis`.
- Do not rewrite or delete `/root/reference_target_text.srt` in this stage.
- Do not write `/outputs/tts_segments/seg_0.wav`, `/outputs/dubbed.mp4`, or `/outputs/report.json`.

## Recommended Command

```bash
mkdir -p /outputs/workflow
python3 - <<'PY'
import json
from pathlib import Path

checkpoint_path = Path('/outputs/workflow/dubbing_intake_checkpoint.json')
out_path = Path('/outputs/workflow/reference_target_basis.json')
checkpoint = json.loads(checkpoint_path.read_text())

required = [
    'input_video_path',
    'segment_windows',
    'source_text_segments',
    'target_language_code',
    'reference_target_text_segments',
    'original_media_info',
    'reference_target_text_path',
    'reference_target_text_review_status',
]
missing = [key for key in required if key not in checkpoint]
if missing:
    raise SystemExit(f'checkpoint missing keys: {missing}')

segment_windows = checkpoint['segment_windows']
source_segments = checkpoint['source_text_segments']
reference_segments = checkpoint['reference_target_text_segments']

if not (len(segment_windows) == len(source_segments) == len(reference_segments)):
    raise SystemExit('segment count mismatch between checkpoint segment lists')

def read_text(item):
    if isinstance(item, dict):
        for key in ('text', 'source_text', 'target_text', 'content'):
            value = item.get(key)
            if value not in (None, ''):
                return ' '.join(str(value).split())
    return ' '.join(str(item).split())

def read_window(item):
    if not isinstance(item, dict):
        raise SystemExit('segment_windows entries must be objects')
    start = item.get('window_start_sec', item.get('start_sec'))
    end = item.get('window_end_sec', item.get('end_sec'))
    if start is None or end is None:
        raise SystemExit('segment_windows entries must include start/end seconds')
    start = float(start)
    end = float(end)
    if end < start:
        raise SystemExit(f'invalid segment window: {start} -> {end}')
    return round(start, 3), round(end, 3)

def read_original_duration(media_info):
    if isinstance(media_info, dict):
        for key in ('original_duration_sec', 'duration_sec', 'duration'):
            value = media_info.get(key)
            if value not in (None, ''):
                return round(float(value), 3)
        format_block = media_info.get('format')
        if isinstance(format_block, dict):
            value = format_block.get('duration')
            if value not in (None, ''):
                return round(float(value), 3)
    raise SystemExit('original_media_info missing duration')

timed_dubbing_basis = []
for idx, (window, source_seg, reference_seg) in enumerate(
    zip(segment_windows, source_segments, reference_segments)
):
    start, end = read_window(window)
    timed_dubbing_basis.append(
        {
            'segment_index': idx,
            'window_start_sec': start,
            'window_end_sec': end,
            'window_duration_sec': round(end - start, 3),
            'source_text': read_text(source_seg),
            'target_text': read_text(reference_seg),
        }
    )

source_language_code = checkpoint.get('source_language_code') or 'en'

reference_target_basis = {
    'workflow_stage': 'reference_target_basis',
    'input_video_path': checkpoint['input_video_path'],
    'timed_dubbing_basis': timed_dubbing_basis,
    'source_language_code': source_language_code,
    'target_language_code': checkpoint['target_language_code'],
    'original_duration_sec': read_original_duration(checkpoint['original_media_info']),
    'reference_target_text_path': checkpoint['reference_target_text_path'],
    'reference_target_text_status': 'superseded_by_reference_target_basis',
    'reference_target_text_cleanup_reason': 'timed_dubbing_basis is the canonical aligned view for later TTS timing and report-ready segment text',
    'reference_target_basis_path': str(out_path),
}

out_path.write_text(json.dumps(reference_target_basis, indent=2, ensure_ascii=False) + '\n')

reference_target_text_path = reference_target_basis['reference_target_text_path']
print('workflow_stage=reference_target_basis')
print(f'reference_target_basis={out_path}')
print('reference_target_text_status=superseded_by_reference_target_basis')
print(f'reference_target_text_path={reference_target_text_path}')
PY
```

## Handoff to Segment Audio Release

The next stage should consume these keys exactly from `/outputs/workflow/reference_target_basis.json`:

- `input_video_path`
- `timed_dubbing_basis`
- `source_language_code`
- `target_language_code`
- `original_duration_sec`
- `reference_target_text_path`
- `reference_target_text_status`
- `reference_target_text_cleanup_reason`
- `reference_target_basis_path`

Do not reopen `/root/reference_target_text.srt` for normal continuation once this basis has been written, unless the basis artifact is missing or malformed.
## Count-Study Continuation

Before `multilingual-video-dubbing-segment-audio-release` begins its separate responsibility, first read the `multilingual-video-dubbing-routing-index-1` skill. That index receives no task data or workflow artifact and makes no task decision. After the index completes, read `multilingual-video-dubbing-segment-audio-release`; it remains the designated data-consuming specialist. Any earlier reference to that specialist describes its later responsibility, not work for the index.
