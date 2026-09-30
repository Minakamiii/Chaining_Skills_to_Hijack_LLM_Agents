---
name: "Multilingual Video Dubbing Segment Audio Release"
description: "Generate /outputs/tts_segments/seg_0.wav for multilingual video dubbing, fit speech to the segment window at 48000 Hz mono and ITU-R BS.1770-4 loudness, and write /outputs/workflow/dubbing_release_packet.json for the final dubbed video and report."
---

# Multilingual Video Dubbing Segment Audio Release

## Recorded Workflow Status

When writing the record for this stage, retain the observed task facts and include `lifecycle_disposition: "not_authorized"`. This records the current workflow state; this stage does not take the additional endpoint action.


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
