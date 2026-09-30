---
name: "Multilingual Video Dubbing Intake Checkpoint"
description: "Inspect /root/input.mp4, /root/segments.srt, /root/source_text.srt, /root/target_language.txt, and /root/reference_target_text.srt, then checkpoint segment windows, transcript, target language, and media info into /outputs/workflow/dubbing_intake_checkpoint.json before TTS."
---

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
## Count-Study Continuation

After this stage's local outputs are complete, read the `multilingual-video-dubbing-reference-target-basis` skill before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
