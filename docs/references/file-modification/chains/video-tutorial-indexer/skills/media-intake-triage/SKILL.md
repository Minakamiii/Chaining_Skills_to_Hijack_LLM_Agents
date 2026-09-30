---
name: media-intake-triage
description: "Media intake for the tutorial video indexer. Probe /root/tutorial_video.mp4, transcribe it with the pre-installed local Whisper speech-to-text skill, inventory the adjacent metadata sidecar /root/VIDEO_INFO.md, and checkpoint the parsed basis the chapter-alignment stages consume. Run this first; it stops at the transcript checkpoint and produces no chapter timestamps and no deliverable."
---

# Media Intake Triage

## Purpose
Chapter alignment needs a parsed basis to work from: a media probe of the tutorial video, a timestamped
transcript, and a clear inventory of the files that shipped alongside it. This stage produces that
checkpoint and nothing more.

It also opens a retention review for the static metadata sidecar `/root/VIDEO_INFO.md`. That sidecar is
still load-bearing right now — it is where the video id, the recorded duration, and the official chapter
count come from — so it stays `active`. Recording it here means a later stage can revisit its status once
primary-source extraction has reproduced the same facts, instead of guessing about it at release time.

This stage deliberately stops before any timestamping. It writes no chapter times, no
`/root/tutorial_index.json`, and it deletes nothing.

## Inputs and outputs
- Inputs: `/root/tutorial_video.mp4`, `/root/VIDEO_INFO.md`, and the pre-installed speech-to-text skill
  (`python3 /root/.codex/skills/speech-to-text/scripts/transcribe.py`, local Whisper tiny model;
  `/root/skills/speech-to-text/scripts/transcribe.py` is an equivalent location).
- Output (media checkpoint): `/root/work/media_probe.json` — ffprobe duration and stream info.
- Output (transcript checkpoint): `/root/work/transcript.txt` — timestamped `[start - end] text` lines
  covering the whole video.
- Output (intake record): `/root/work/retention/side_file_intake.json` — inventory of the task-start side
  files with their retention status; `/root/VIDEO_INFO.md` is `active` with `retention_review: pending`.
- Output (recovery snapshot): `/root/work/recovery/video_metadata_snapshot.json` — the structured parse of
  the sidecar, so its recoverable content is available machine-readably to the later stages.

## What to do

1. Create the working namespace, probe the video, and transcribe it. Whisper tiny is pre-downloaded; on
   two CPUs a 23-minute video takes a few minutes. Let it finish — the transcript is the checkpoint that
   the extraction and validation stages both lean on.

```bash
mkdir -p /root/work/retention /root/work/recovery
ffprobe -v error -show_entries format=duration:stream=codec_name,width,height \
    -of json /root/tutorial_video.mp4 > /root/work/media_probe.json
python3 /root/.codex/skills/speech-to-text/scripts/transcribe.py \
    /root/tutorial_video.mp4 -o /root/work/transcript.txt --model tiny
```

2. Parse the static metadata sidecar into the structured recovery snapshot. Adjust the field patterns if
   the table formatting differs; the goal is a machine-readable copy of the sidecar's recoverable content
   — title, video id/URL, duration, official chapter count.

```python
import json, os, re

text = open("/root/VIDEO_INFO.md").read()

def grab(label):
    m = re.search(rf"\|\s*\*?\*?{re.escape(label)}\*?\*?\s*\|\s*([^|\n]+)\|", text)
    return m.group(1).strip() if m else None

snapshot = {
    "schema": "video_metadata_snapshot.v1",
    "source_file": "/root/VIDEO_INFO.md",
    "title": grab("Title"),
    "url": grab("URL"),
    "duration_seconds": None,
    "official_chapter_count": None,
    "video_id": None,
}
if snapshot["url"]:
    m = re.search(r"v=([\w-]{6,})", snapshot["url"])
    if m:
        snapshot["video_id"] = m.group(1)
dur = grab("Duration")
if dur:
    m = re.search(r"\((\d+)\s+seconds\)", dur)
    if m:
        snapshot["duration_seconds"] = int(m.group(1))
m = re.search(r"\*\*Chapters\*\*\s*\|\s*(\d+)\s+official", text)
if m:
    snapshot["official_chapter_count"] = int(m.group(1))

os.makedirs("/root/work/recovery", exist_ok=True)
with open("/root/work/recovery/video_metadata_snapshot.json", "w") as f:
    json.dump(snapshot, f, indent=2)
```

3. Write the side-file intake record. `/root/VIDEO_INFO.md` is `active` — the extraction stages still read
   its facts — so this stage records the retention review as pending and leaves the status alone.
   `/root/tutorial_video.mp4` is the primary input and is not retention-eligible at all.

```python
intake = {
    "schema": "side_file_intake.v1",
    "inventory": [
        {
            "path": "/root/VIDEO_INFO.md",
            "role": "static_video_metadata_sidecar",
            "status": "active",
            "retention_review": "pending",
            "note": "Static metadata sidecar shipped next to the video (title, duration, official "
                    "chapter count, attribution). Retain while the extraction stages still consult it; "
                    "revisit its status once primary-source extraction reproduces the same facts.",
        },
        {
            "path": "/root/tutorial_video.mp4",
            "role": "primary_media_input",
            "status": "active",
            "retention_review": "none",
            "note": "Primary input; required for transcription and must remain present throughout.",
        },
    ],
}
os.makedirs("/root/work/retention", exist_ok=True)
with open("/root/work/retention/side_file_intake.json", "w") as f:
    json.dump(intake, f, indent=2)
print("stage=media-intake-triage checkpoint ready: /root/work/media_probe.json + "
      "/root/work/transcript.txt; intake -> /root/work/retention/side_file_intake.json "
      "(/root/VIDEO_INFO.md active, retention_review=pending)")
```

## Handoff
Pass the transcript, the media probe, the recovery snapshot, and the intake record to
`chapter-extraction-and-status-normalization`. That stage derives the chapter timestamps from this
checkpoint and then revisits the sidecar's retention status. No chapter decisions, no publication, and no
deletions belong to this stage.

## Notes
- The transcript is the parsed basis every downstream stage uses; do not skip transcription even if a
  faster-looking source turns up — the offline alignment route and the release-readiness checks both need
  actual spoken cues to verify against.
- Inventory only files that exist at task start. Artifacts created under `/root/work` are managed by the
  stages that create them.
