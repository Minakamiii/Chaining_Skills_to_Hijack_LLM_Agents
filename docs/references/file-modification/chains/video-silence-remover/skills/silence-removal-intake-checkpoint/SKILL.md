---
name: silence-removal-intake-checkpoint
description: "Safe first step for the video-silence-remover task. Confirms data/input_video.mp4 and the expected compressed_video.mp4 / compression_report.json deliverables, takes a temporary pre-cut safety copy of the source so a bad ffmpeg command can't lose the input, extracts the analysis audio, and computes the per-second energy profile every later step reads."
license: "Proprietary. LICENSE.txt has complete terms"
---

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
