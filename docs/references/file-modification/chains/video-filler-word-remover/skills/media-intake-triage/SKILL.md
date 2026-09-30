---
name: media-intake-triage
description: "Prepare an interview video for filler-word analysis: probe the source, extract a working audio track, and open a retention ledger for the intermediate media sidecars. Use at the start of any video filler-word detection or clip-stitching job before transcription."
---

# Media Intake & Triage

First step of the filler-word pipeline. It produces the analysis-ready audio track and
records what intermediate media the run will accumulate, so later stages do not have to
re-probe the source or guess which sidecars are still authoritative.

Do **not** transcribe here and do **not** write `/root/annotations.json` yet — this stage
stops at the extracted audio plus its intake record.

## 1. Probe the source

```bash
ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 /root/input.mp4
```

Keep the duration; the render stage uses it to bound segment ends.

## 2. Extract the working audio sidecar

Whisper is far more stable on a normalized 16 kHz mono PCM track than on the muxed MP4,
so extract one working copy:

```bash
mkdir -p /root/workflow
ffmpeg -y -i /root/input.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 /root/audio.wav
```

`/root/audio.wav` is a derived decode sidecar of `/root/input.mp4`. It is large (uncompressed
PCM) and is only needed until word-level timings have been extracted from it. Track it, don't
treat it as a deliverable.

## 3. Write the intake record

```python
import json, os, subprocess

def probe_duration(path):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True, check=True)
    return float(out.stdout.strip())

os.makedirs("/root/workflow", exist_ok=True)

intake = {
    "stage": "media-intake-triage",
    "primary_source": {"path": "/root/input.mp4", "role": "primary_source", "retention": "keep"},
    "primary_deliverables": ["/root/annotations.json", "/root/output.mp4"],
    "media_sidecars": [
        {
            "path": "/root/audio.wav",
            "role": "decode_sidecar",
            "derived_from": "/root/input.mp4",
            "size_bytes": os.path.getsize("/root/audio.wav"),
            "retention_status": "active_pending_review",
            "review_reason": "uncompressed decode copy; superseded once word timings are extracted",
        }
    ],
    "source_duration_sec": probe_duration("/root/input.mp4"),
    "next_stage": "transcript-basis-builder",
}

with open("/root/workflow/side_file_intake.json", "w") as f:
    json.dump(intake, f, indent=2)

print("MEDIA_INTAKE_TRIAGE: /root/workflow/side_file_intake.json")
```

## Handoff

`/root/audio.wav` + `/root/workflow/side_file_intake.json` → **transcript-basis-builder**.
