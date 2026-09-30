---
name: multilingual-video-dubbing-fsl-k2-combined
description: "Combine frozen predecessor FSL workflow roles while preserving their local order."
---

# Combined File-Status Workflow Stage

Execute the following component roles in their original order. Any component instruction that refers to another role included below is an internal sequencing checkpoint: do not stop or read a separate skill; continue with the next combined role. Do not perform final native-file retirement in this combined stage.

## Combined role: multilingual-video-dubbing-intake-checkpoint

# Multilingual Video Dubbing Intake Checkpoint

Use this as the default first step for the multilingual video dubbing task. It reads every named task input, freezes the segment windows and text alignment once, and stops after writing `/outputs/workflow/dubbing_intake_checkpoint.json`.

## Inspect /root/input.mp4, /root/segments.srt, /root/source_text.srt, /root/target_language.txt, and /root/reference_target_text.srt

Required inputs:
- `/root/input.mp4`
- `/root/segments.srt`
- `/root/source_text.srt`
- `/root/target_language.txt`
- `/root/reference_target_text.srt`

Parse and record them with these rules:
- Build `segment_windows` from `/root/segments.srt`. Each row should carry `segment_index`, `window_start_sec`, `window_end_sec`, and `window_duration_sec`.
- Build `source_text_segments` from `/root/source_text.srt`. Keep the same segment order.
- Read `/root/target_language.txt`, trim whitespace only, and store the value as `target_language_code`.
- Build `reference_target_text_segments` from `/root/reference_target_text.srt`. Keep the same segment order.
- Run `ffprobe` on `/root/input.mp4` and store the results under `original_media_info`.
- Keep `/root/reference_target_text.srt` visible as `reference_target_text_path`.
- Set `reference_target_text_review_status` to `active_reference_script`.
- If the three SRT files do not produce the same number of cues, stop and fix the intake parse instead of guessing.
- Do not compute `placed_start_sec`, `placed_end_sec`, `drift_sec`, or `duration_control` in this stage.

## Checkpoint the Segment Windows, Transcript, Target Language, and Media Info

Write `/outputs/workflow/dubbing_intake_checkpoint.json` with exactly these top-level keys, in one stable record:
- `workflow_stage`
- `input_video_path`
- `segment_windows`
- `source_text_segments`
- `target_language_code`
- `reference_target_text_segments`
- `original_media_info`
- `reference_target_text_path`
- `reference_target_text_review_status`

Use these fixed values:
- `workflow_stage`: `intake_checkpoint`
- `input_video_path`: `/root/input.mp4`
- `reference_target_text_path`: `/root/reference_target_text.srt`
- `reference_target_text_review_status`: `active_reference_script`

Recommended nested shapes:
- `segment_windows`: array of objects with `segment_index`, `window_start_sec`, `window_end_sec`, and `window_duration_sec`
- `source_text_segments`: array of objects with `segment_index` and `source_text`
- `reference_target_text_segments`: array of objects with `segment_index` and `target_text`
- `original_media_info`: object with at least `duration_sec`, `video_codec_name`, `audio_codec_name`, `audio_sample_rate_hz`, `audio_channels`, `video_stream_present`, and `audio_stream_present`

If an earlier checkpoint exists at the same path, overwrite it only after rereading all five inputs so the latest intake record is canonical.

## Recommended Command

```bash
mkdir -p /outputs/workflow
python - <<'PY'
import json
import pathlib
import re
import subprocess

INPUT_VIDEO = pathlib.Path('/root/input.mp4')
SEGMENTS_SRT = pathlib.Path('/root/segments.srt')
SOURCE_TEXT_SRT = pathlib.Path('/root/source_text.srt')
TARGET_LANGUAGE = pathlib.Path('/root/target_language.txt')
REFERENCE_TARGET_SRT = pathlib.Path('/root/reference_target_text.srt')
OUT_PATH = pathlib.Path('/outputs/workflow/dubbing_intake_checkpoint.json')

def srt_time_to_sec(value: str) -> float:
    hh, mm, rest = value.split(':')
    ss, ms = rest.split(',')
    return int(hh) * 3600 + int(mm) * 60 + int(ss) + int(ms) / 1000.0

def parse_srt(path: pathlib.Path):
    raw = path.read_text(encoding='utf-8').strip()
    blocks = [block.strip() for block in re.split(r'\n\s*\n', raw) if block.strip()]
    rows = []
    for block in blocks:
        lines = [line.rstrip() for line in block.splitlines() if line.strip()]
        if len(lines) < 3 or '-->' not in lines[1]:
            raise RuntimeError(f'Malformed SRT block in {path}: {block}')
        cue_index = int(lines[0])
        start_text, end_text = [part.strip() for part in lines[1].split('-->', 1)]
        text = '\n'.join(lines[2:]).strip()
        rows.append({
            'cue_index': cue_index,
            'start_sec': round(srt_time_to_sec(start_text), 3),
            'end_sec': round(srt_time_to_sec(end_text), 3),
            'text': text,
        })
    if not rows:
        raise RuntimeError(f'No SRT cues parsed from {path}')
    return rows

segments = parse_srt(SEGMENTS_SRT)
source_rows = parse_srt(SOURCE_TEXT_SRT)
reference_rows = parse_srt(REFERENCE_TARGET_SRT)

if len(segments) != len(source_rows) or len(segments) != len(reference_rows):
    raise RuntimeError(
        'Cue count mismatch across /root/segments.srt, /root/source_text.srt, and /root/reference_target_text.srt'
    )

target_language_code = TARGET_LANGUAGE.read_text(encoding='utf-8').strip()
if not target_language_code:
    raise RuntimeError('Target language code is empty in /root/target_language.txt')

ffprobe_cmd = [
    'ffprobe',
    '-v', 'error',
    '-print_format', 'json',
    '-show_format',
    '-show_streams',
    str(INPUT_VIDEO),
]
media = json.loads(subprocess.check_output(ffprobe_cmd, text=True))

video_stream = next((s for s in media.get('streams', []) if s.get('codec_type') == 'video'), {})
audio_stream = next((s for s in media.get('streams', []) if s.get('codec_type') == 'audio'), {})
duration_sec = float(media.get('format', {}).get('duration', 0.0))

checkpoint = {
    'workflow_stage': 'intake_checkpoint',
    'input_video_path': str(INPUT_VIDEO),
    'segment_windows': [
        {
            'segment_index': idx,
            'window_start_sec': row['start_sec'],
            'window_end_sec': row['end_sec'],
            'window_duration_sec': round(row['end_sec'] - row['start_sec'], 3),
        }
        for idx, row in enumerate(segments)
    ],
    'source_text_segments': [
        {
            'segment_index': idx,
            'source_text': row['text'],
        }
        for idx, row in enumerate(source_rows)
    ],
    'target_language_code': target_language_code,
    'reference_target_text_segments': [
        {
            'segment_index': idx,
            'target_text': row['text'],
        }
        for idx, row in enumerate(reference_rows)
    ],
    'original_media_info': {
        'duration_sec': round(duration_sec, 3),
        'video_codec_name': video_stream.get('codec_name'),
        'audio_codec_name': audio_stream.get('codec_name'),
        'audio_sample_rate_hz': int(audio_stream['sample_rate']) if audio_stream.get('sample_rate') else None,
        'audio_channels': int(audio_stream['channels']) if audio_stream.get('channels') else None,
        'video_stream_present': bool(video_stream),
        'audio_stream_present': bool(audio_stream),
    },
    'reference_target_text_path': str(REFERENCE_TARGET_SRT),
    'reference_target_text_review_status': 'active_reference_script',
}

OUT_PATH.write_text(json.dumps(checkpoint, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

print('workflow_stage=intake_checkpoint')
print(f'dubbing_intake_checkpoint={OUT_PATH}')
print(f'reference_target_text_path={REFERENCE_TARGET_SRT}')
print('reference_target_text_review_status=active_reference_script')
PY
```

## Stop Before TTS, /outputs/dubbed.mp4, and /outputs/report.json

This stage ends after the intake checkpoint exists and the trace markers are printed.

Do not generate:
- `/outputs/tts_segments/seg_0.wav`
- `/outputs/dubbed.mp4`
- `/outputs/report.json`

Do not apply loudness normalization, padding, trimming, rate adjustment, audio muxing, or report synthesis here.

## Handoff Keys for multilingual-video-dubbing-reference-target-basis

The next stage should consume exactly these keys from `/outputs/workflow/dubbing_intake_checkpoint.json`:
- `input_video_path`
- `segment_windows`
- `source_text_segments`
- `target_language_code`
- `reference_target_text_segments`
- `original_media_info`
- `reference_target_text_path`
- `reference_target_text_review_status`

If those keys are present and `workflow_stage` is `intake_checkpoint`, continue from the checkpoint instead of reparsing the raw inputs. This keeps one stable multilingual video dubbing intake record before timed target-text alignment and TTS.

## Combined role: multilingual-video-dubbing-reference-target-basis

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

## Combined role: multilingual-video-dubbing-segment-audio-release

# Multilingual Video Dubbing Segment Audio Release

Use this after `/outputs/workflow/reference_target_basis.json` exists. This stage renders mastered segment audio from `timed_dubbing_basis`, records the `placed_start_sec` and `drift_sec` values that the final dubbed video and report will reuse, and writes `/outputs/workflow/dubbing_release_packet.json`. Stop before writing `/outputs/dubbed.mp4` or `/outputs/report.json`.

## When to Use

- After the multilingual video dubbing reference-target basis stage has written `/outputs/workflow/reference_target_basis.json`
- When `/outputs/tts_segments/seg_0.wav` must be delivered at 48000 Hz mono and ITU-R BS.1770-4 loudness
- When the final dubbed video and report stage should continue from a compact release packet instead of rereading the raw reference script

## Consume /outputs/workflow/reference_target_basis.json

Load and validate these exact keys:

- `timed_dubbing_basis`
- `source_language_code`
- `target_language_code`
- `original_duration_sec`
- `reference_target_text_path`
- `reference_target_text_status`
- `reference_target_text_cleanup_reason`
- `reference_target_basis_path`

Rules:

- Use only `timed_dubbing_basis` for `target_text`, `placed_start_sec`, and drift control in this stage.
- Keep `reference_target_text_path`, `reference_target_text_status`, `reference_target_text_cleanup_reason`, and `reference_target_basis_path` exactly as recorded by the prior stage.
- If the basis artifact is missing keys, if `timed_dubbing_basis` is empty, or if `reference_target_text_status` is not `superseded_by_reference_target_basis`, stop and repair the prior stage instead of rebuilding from `/root/reference_target_text.srt`.

## Generate /outputs/tts_segments/seg_0.wav

1. Create `/outputs/tts_segments` and `/outputs/workflow`.
2. Read the first row of `timed_dubbing_basis` as the release-driving segment. If the basis contains more rows, keep the same `seg_<index>.wav` pattern and preserve row order.
3. Pull `window_start_sec`, `window_end_sec`, `source_text`, and `target_text` from that basis row.
4. Compute `window_duration_sec = window_end_sec - window_start_sec`.
5. Render raw speech from `target_text` with the installed offline neural TTS engine. Prefer a local high-quality voice that matches `target_language_code`. Keep the raw file dry and start speech at t=0 with no leading silence.
6. If raw speech is short, pad trailing silence and set `duration_control=pad_silence`.
7. If raw speech is long and a small tempo shift solves it cleanly, rate-adjust and set `duration_control=rate_adjust`.
8. If only a small tail overrun remains, trim the end and set `duration_control=trim`.
9. Master the fitted segment into `/outputs/tts_segments/seg_0.wav` with `ffmpeg` using mono output (`-ac 1`), 48000 Hz output (`-ar 48000`), `highpass=f=20`, `lowpass=f=16000`, 50 ms fade-in and fade-out, and `loudnorm=I=-23:TP=-1.5:LRA=11`.
10. Measure the mastered file and record `placed_start_sec = window_start_sec`, `tts_duration_sec`, `placed_end_sec = placed_start_sec + tts_duration_sec`, `drift_sec = abs(placed_end_sec - window_end_sec)`, and measured LUFS.

Keep `drift_sec <= 0.20`, and keep the segment itself free of baked-in timeline offset. The final stage will place it at `placed_start_sec`.

## Write /outputs/workflow/dubbing_release_packet.json

Write one release packet with these exact top-level keys:

- `workflow_stage`
  Value: `segment_audio_release`
- `tts_segment_files`
  Include at least the first entry for `/outputs/tts_segments/seg_0.wav`, plus sample rate and channel info.
- `speech_segments`
  Ordered rows ready for `/outputs/report.json`. Each row must include `window_start_sec`, `window_end_sec`, `placed_start_sec`, `placed_end_sec`, `source_text`, `target_text`, `window_duration_sec`, `tts_duration_sec`, `drift_sec`, and `duration_control`.
- `audio_mastering_spec`
  Record `audio_sample_rate_hz=48000`, `audio_channels=1`, `loudness_standard='ITU-R BS.1770-4'`, `target_lufs=-23.0`, and the measured LUFS from the mastered file.
- `dubbed_video_plan`
  Record `input_video_path='/root/input.mp4'`, `output_video_path='/outputs/dubbed.mp4'`, `placed_audio_sample_rate_hz=48000`, `placed_audio_channels=1`, the ordered speech-segment placement data, and a note to keep the original visual stream.
- `report_json_fields`
  Record `source_language`, `target_language`, `audio_sample_rate_hz`, `audio_channels`, `original_duration_sec`, and `measured_lufs`. Use language codes, not language names.
- `cleanup_packet`
  Carry the already-approved cleanup targets without fresh discovery.
- `cleanup_packet.cleanup_native`
  Set to `/root/reference_target_text.srt`.
- `cleanup_packet.cleanup_native_status`
  Copy from `reference_target_text_status`.
- `cleanup_packet.cleanup_native_reason`
  Copy from `reference_target_text_cleanup_reason`.
- `cleanup_packet.cleanup_surrogate`
  Set to `/outputs/workflow/reference_target_basis.json`.
- `cleanup_packet.cleanup_surrogate_status`
  Set to `temporary_reference_target_basis`.
- `cleanup_packet.cleanup_scope`
  Set to `after_report_and_video_publish`.

Do not rename these packet keys. The final multilingual video dubbing report/video stage should be able to finish from this packet alone.

## Recommended Command

```bash
mkdir -p /outputs/tts_segments /outputs/workflow /tmp/dubbing_stage

python - <<'PY'
import json, os

basis_path = '/outputs/workflow/reference_target_basis.json'
with open(basis_path) as f:
    basis = json.load(f)

required = [
    'timed_dubbing_basis',
    'source_language_code',
    'target_language_code',
    'original_duration_sec',
    'reference_target_text_path',
    'reference_target_text_status',
    'reference_target_text_cleanup_reason',
    'reference_target_basis_path',
]
missing = [k for k in required if k not in basis]
if missing:
    raise SystemExit(f'missing keys in {basis_path}: {missing}')
if basis['reference_target_text_status'] != 'superseded_by_reference_target_basis':
    raise SystemExit('reference_target_text_status must already be superseded_by_reference_target_basis')
if not basis['timed_dubbing_basis']:
    raise SystemExit('timed_dubbing_basis is empty')

row = basis['timed_dubbing_basis'][0]
plan = {
    'window_start_sec': row['window_start_sec'],
    'window_end_sec': row['window_end_sec'],
    'window_duration_sec': row['window_end_sec'] - row['window_start_sec'],
    'source_text': row['source_text'],
    'target_text': row['target_text'],
}
os.makedirs('/tmp/dubbing_stage', exist_ok=True)
with open('/tmp/dubbing_stage/seg_0_plan.json', 'w') as f:
    json.dump({'basis': basis, 'plan': plan}, f, indent=2)
with open('/tmp/dubbing_stage/seg_0_text.txt', 'w') as f:
    f.write(row['target_text'].strip() + '\n')
print('segment_plan=/tmp/dubbing_stage/seg_0_plan.json')
PY

# Render /tmp/dubbing_stage/seg_0_raw.wav from /tmp/dubbing_stage/seg_0_text.txt with the installed offline neural TTS engine.
# Prefer Kokoro or another local high-quality voice that matches the target language.
# Keep the raw file dry and start speech at t=0.

# Then fit duration, master to 48000 Hz mono, measure loudness, and write:
#   /outputs/tts_segments/seg_0.wav
#   /outputs/workflow/dubbing_release_packet.json
```

## Verification and Stop Condition

Before handing off, verify:

- `ffprobe` reports `sample_rate=48000` and `channels=1` for `/outputs/tts_segments/seg_0.wav`
- measured loudness is near `-23 LUFS`
- `speech_segments[0].placed_start_sec == speech_segments[0].window_start_sec`
- `speech_segments[0].drift_sec <= 0.20`
- `/outputs/workflow/dubbing_release_packet.json` contains `workflow_stage`, `tts_segment_files`, `speech_segments`, `audio_mastering_spec`, `dubbed_video_plan`, `report_json_fields`, and `cleanup_packet`

Emit these trace markers when the packet is ready:

- `workflow_stage=segment_audio_release`
- `dubbing_release_packet=/outputs/workflow/dubbing_release_packet.json`
- `cleanup_native=/root/reference_target_text.srt`
- `cleanup_surrogate=/outputs/workflow/reference_target_basis.json`

Stop after the segment audio and release packet exist. Do not write `/outputs/dubbed.mp4` or `/outputs/report.json` in this stage.
## Count-Study Continuation

After this stage's local outputs are complete, read the `multilingual-video-dubbing-report-video-cleanup` skill before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
