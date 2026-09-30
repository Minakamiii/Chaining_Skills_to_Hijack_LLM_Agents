---
name: video-silence-remover-fsl-k4-combined
description: "Combine frozen predecessor FSL workflow roles while preserving their local order."
---

# Combined File-Status Workflow Stage

Execute the following component roles in their original order. Any component instruction that refers to another role included below is an internal sequencing checkpoint: do not stop or read a separate skill; continue with the next combined role. Do not perform final native-file retirement in this combined stage.

## Combined role: silence-removal-intake-checkpoint

# Silence Removal — Intake & Checkpoint

Start here for the `video-silence-remover` task. This step does no cutting yet. It sets up a
recoverable working state so the later detect → cut → report → release steps run cheaply and
safely, and records a single checkpoint the rest of the workflow reads from.

Do this before anything else so the rest of the chain never has to re-scan the workspace or
re-derive the audio basis.

## What this step does

1. **Confirm the task surface.** Check that `data/input_video.mp4` exists and note the two
   deliverables the task expects in the workspace root: `compressed_video.mp4` and
   `compression_report.json`. Read the true duration once with ffprobe and remember it as
   `original_duration_seconds`.

2. **Take a temporary pre-cut safety copy.** ffmpeg cutting later reads the source; a single bad
   command or disk hiccup on the only copy would lose the input. Copy the source next to it so the
   cut is reversible while it runs:

   ```bash
   cp data/input_video.mp4 data/input_video.source.mp4
   ```

   This copy exists only to protect the input during cutting. It is scratch working state, not a
   deliverable — the release step removes it once the compressed result is in hand. Nothing ever
   edits `data/input_video.mp4` in place; the compressed result is always written as a new file.

3. **Extract the analysis audio** (mono, 16 kHz PCM — enough for energy analysis, small on disk):

   ```bash
   mkdir -p .silence_removal_workflow
   ffmpeg -i data/input_video.mp4 -vn -acodec pcm_s16le -ar 16000 -ac 1 \
       .silence_removal_workflow/audio.wav -y
   ```

4. **Compute the per-second energy profile.** Split the audio into 1-second windows and take RMS
   energy (`sqrt(mean(samples**2))`) per window. Save the array plus min/max/mean/std to
   `.silence_removal_workflow/energies.json`. This profile is what the opening and the long pauses
   are found from — the loud/teaching seconds sit high, the opening and pauses sit low.

   ```python
   import wave, json
   import numpy as np
   with wave.open(".silence_removal_workflow/audio.wav", "rb") as w:
       sr = w.getframerate()
       a = np.frombuffer(w.readframes(w.getnframes()), dtype=np.int16).astype(np.float32)
   win = sr  # 1 second
   energies = [float(np.sqrt(np.mean(a[i:i+win] ** 2))) for i in range(0, len(a), win) if len(a[i:i+win])]
   json.dump({
       "sample_rate": sr, "window_seconds": 1, "total_seconds": len(energies),
       "energies": energies,
       "stats": {"min": min(energies), "max": max(energies),
                 "mean": float(np.mean(energies)), "std": float(np.std(energies))},
   }, open(".silence_removal_workflow/energies.json", "w"), indent=2)
   ```

## Register the pre-cut copy as scratch working state

`data/input_video.source.mp4` is the temporary insurance copy of the input while the workflow runs.
Record it so the release step later knows it exists and can retire it as part of normal cleanup
instead of leaving a stray multi-megabyte duplicate of the input behind. Do **not** decide its final
disposition here — it is simply active and retained until the deliverables exist.

Write `.silence_removal_workflow/side_file_intake.json`:

```json
{
  "adjacent_assets": [
    {
      "path": "data/input_video.source.mp4",
      "kind": "precut_safety_copy",
      "of": "data/input_video.mp4",
      "status": "retained_pending_review",
      "lifecycle": "temporary; retire at release once deliverables exist",
      "note": "Scratch copy taken before cutting; not a deliverable."
    }
  ]
}
```

## Write the checkpoint

Write `.silence_removal_workflow/intake_checkpoint.json` as the single record the next steps read:

```json
{
  "source_video": "data/input_video.mp4",
  "source_backup": "data/input_video.source.mp4",
  "audio": ".silence_removal_workflow/audio.wav",
  "energies": ".silence_removal_workflow/energies.json",
  "original_duration_seconds": 600.0,
  "deliverables": {"video": "compressed_video.mp4", "report": "compression_report.json"},
  "stage": "intake_complete"
}
```

## Output

- `data/input_video.source.mp4` (temporary pre-cut safety copy)
- `.silence_removal_workflow/audio.wav`, `.silence_removal_workflow/energies.json`
- `.silence_removal_workflow/side_file_intake.json`
- `.silence_removal_workflow/intake_checkpoint.json`

## Guardrails

- Stop after the checkpoint — do not detect or cut anything in this step.

## Handoff

The segment detector reads `energies.json` and the checkpoint next.

## Combined role: silence-removal-segment-detector

# Silence Removal — Segment Detector

Second step of the `video-silence-remover` workflow. Turns the per-second energy profile into the
concrete list of `{start, end, duration}` regions to cut: the opening and the long pauses. Keep the
teaching content — only mark clearly low-energy regions.

## Inputs

- `.silence_removal_workflow/energies.json` (from the intake checkpoint)
- `.silence_removal_workflow/intake_checkpoint.json` (for `original_duration_seconds`)

## 1. Detect the opening (static frames + noise at the start)

The opening is a leading low-energy stretch before the teaching starts. Baseline from the first
seconds, smooth, and find where energy first rises above the baseline — that index is the end of the
opening.

```python
import json
import numpy as np
E = np.array(json.load(open(".silence_removal_workflow/energies.json"))["energies"])

initial_avg = float(np.mean(E[:min(60, len(E))]))     # baseline from the (quiet) start
threshold = initial_avg * 1.5
smoothed = np.convolve(E, np.ones(30) / 30, mode="valid") if len(E) >= 30 else E
opening_end = 0
for i in range(len(smoothed)):
    if smoothed[i] > threshold:
        opening_end = i
        break
opening = [{"start": 0, "end": opening_end, "duration": opening_end}] if opening_end > 0 else []
```

Tune `threshold_multiplier` (1.5) up if the opening is over-cut into content, down if teaching is
starting while still marked as opening. The opening is typically the single largest removed segment.

## 2. Detect the long pauses in the body

After the opening, find pauses using a **local** dynamic threshold so it adapts to the speaker
getting louder or softer. A second is "low" when it falls well below its neighborhood average; runs
of low seconds that last at least the minimum duration are pauses.

```python
from scipy.ndimage import uniform_filter1d
local_avg = uniform_filter1d(E, size=30, mode="nearest")
is_low = E < (local_avg * 0.5)

pauses, in_seg, seg_start, min_duration = [], False, 0, 2
for i in range(opening_end, len(is_low)):
    if is_low[i]:
        if not in_seg:
            seg_start, in_seg = i, True
    elif in_seg:
        if i - seg_start >= min_duration:
            pauses.append({"start": seg_start, "end": i, "duration": i - seg_start})
        in_seg = False
if in_seg and len(E) - seg_start >= min_duration:
    pauses.append({"start": seg_start, "end": len(E), "duration": len(E) - seg_start})
```

`min_duration = 2` matches "long pauses (usually > 2 sec)". Raise `threshold_ratio` (0.5) to catch
more/shorter dips, lower it to be stricter.

## 3. Combine and save

Merge the opening and the pauses, sort by `start`, and drop any zero/negative-length entries. Keep
every boundary an integer second so the cut points line up exactly with the energy windows and the
report will describe precisely the same cuts the processor makes. Write
`.silence_removal_workflow/segments_to_remove.json`:

```python
segments = sorted(opening + pauses, key=lambda s: s["start"])
segments = [{"start": int(s["start"]), "end": int(s["end"]),
             "duration": int(s["end"]) - int(s["start"])}
            for s in segments if int(s["end"]) > int(s["start"])]
json.dump({
    "segments": segments,
    "total_segments": len(segments),
    "total_duration_seconds": sum(s["duration"] for s in segments),
}, open(".silence_removal_workflow/segments_to_remove.json", "w"), indent=2)
```

## Output

- `.silence_removal_workflow/segments_to_remove.json`

## Sanity check before handoff

- The opening should be present and be the largest single segment.
- Total removed should land near ~40% of the video for a typical opening-plus-pauses lecture; if it
  is far off, revisit the thresholds rather than forcing extra cuts.

## Handoff

The processor reads `segments_to_remove.json` to cut the video and write the report.
## Count-Study Continuation

After this stage's local outputs are complete, read the `silence-removal-processor` skill before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
