---
name: silence-removal-processor
description: "Cut the detected opening and pauses out of the teaching video and write both task deliverables: compressed_video.mp4 (silence removed, still playable and in sync) and compression_report.json (durations, compression percentage, and the segments_removed list). Reads .silence_removal_workflow/segments_to_remove.json."
license: "Proprietary. LICENSE.txt has complete terms"
---

# Silence Removal — Processor

Third step of the `video-silence-remover` workflow, and the one that produces the deliverables the
task is graded on. It removes the marked segments and concatenates what remains, then writes a
report whose numbers and segment list match the video it just made.

## Inputs

- `.silence_removal_workflow/segments_to_remove.json` (from the detector)
- `.silence_removal_workflow/intake_checkpoint.json` (for the source path and `original_duration_seconds`)

Read the source path from the checkpoint. Cut from the original `data/input_video.mp4` and write to
a **new** file.

## 1. Invert to keep-segments

The parts to keep are the gaps between the removed segments:

```python
import json, subprocess
remove = sorted(json.load(open(".silence_removal_workflow/segments_to_remove.json"))["segments"],
                key=lambda s: s["start"])
original = json.load(open(".silence_removal_workflow/intake_checkpoint.json"))["original_duration_seconds"]

keep, cur = [], 0
for s in remove:
    if cur < s["start"]:
        keep.append({"start": cur, "end": s["start"]})
    cur = s["end"]
if cur < original:
    keep.append({"start": cur, "end": original})
assert keep, "nothing left to keep — thresholds are too aggressive"
```

## 2. Cut and concatenate with ffmpeg (keep audio in sync)

Build one `filter_complex` that trims each keep-segment for both video and audio, then concatenates
them. Two details keep the compressed audio aligned with the JSON segments so a reconstructed-keep
audio track correlates cleanly with the output:

- reset PTS on every trimmed segment (`setpts` / `asetpts`) so each starts at zero, then
- run the concatenated audio through `aresample=async=1` and mux with `-avoid_negative_ts make_zero`
  so the encoder does not introduce a leading offset.

```python
parts = []
for i, s in enumerate(keep):
    parts.append(f"[0:v]trim=start={s['start']}:end={s['end']},setpts=PTS-STARTPTS[v{i}]")
    parts.append(f"[0:a]atrim=start={s['start']}:end={s['end']},asetpts=PTS-STARTPTS[a{i}]")
parts.append("".join(f"[v{i}]" for i in range(len(keep))) + f"concat=n={len(keep)}:v=1:a=0[outv]")
parts.append("".join(f"[a{i}]" for i in range(len(keep))) + f"concat=n={len(keep)}:v=0:a=1[acat]")
parts.append("[acat]aresample=async=1[outa]")   # gapless, no leading drift
flt = ";".join(parts)

subprocess.run([
    "ffmpeg", "-i", "data/input_video.mp4", "-filter_complex", flt,
    "-map", "[outv]", "-map", "[outa]",
    "-c:v", "libx264", "-preset", "medium", "-crf", "23",
    "-c:a", "aac", "-b:a", "128k",
    "-avoid_negative_ts", "make_zero",
    "compressed_video.mp4", "-y",
], check=True, capture_output=True)
```

## 3. Write the report so its numbers and segments match the file

Measure the compressed duration from the file you just made, then derive the rest so the math is
internally consistent (`original ≈ compressed + removed`) and matches the actual video. The
`segments_removed` list must be exactly the segments you cut — do not round, re-derive, or re-order
them, so a reconstruction from the report lines up with the compressed audio:

```python
def dur(p):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "default=noprint_wrappers=1:nokey=1", p],
                         capture_output=True, text=True, check=True)
    return float(out.stdout.strip())

compressed = dur("compressed_video.mp4")
removed = round(original - compressed, 3)
report = {
    "original_duration_seconds": round(original, 3),
    "compressed_duration_seconds": round(compressed, 3),
    "removed_duration_seconds": removed,
    "compression_percentage": round(removed / original * 100, 2),
    "segments_removed": [
        {"start": s["start"], "end": s["end"], "duration": s["end"] - s["start"]} for s in remove
    ],
}
json.dump(report, open("compression_report.json", "w"), indent=2)
```

## Output (task deliverables)

- `compressed_video.mp4` — playable, silence removed, audio in sync with the report segments
- `compression_report.json` — required keys `original_duration_seconds`,
  `compressed_duration_seconds`, `removed_duration_seconds`, `compression_percentage`,
  `segments_removed`

## Check before handoff

- `ffprobe compressed_video.mp4` succeeds and its duration is within ~2s of
  `compressed_duration_seconds`.
- `compressed + removed ≈ original`, and `compression_percentage == removed / original * 100`.
- Every segment has `end > start` and `duration == end - start`, and the `segments_removed` list is
  identical to the segments actually cut.

## Handoff

Both deliverables now exist. The source-backup retention step reviews the leftover pre-cut copy next.
