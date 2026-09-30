---
name: silence-removal-segment-detector
description: "Find the removable regions of the teaching video from the energy profile: the static/noise opening at the start and the long (>2s) pauses in the body. Reads .silence_removal_workflow/energies.json from the intake checkpoint and writes .silence_removal_workflow/segments_to_remove.json for the cutting step."
license: "Proprietary. LICENSE.txt has complete terms"
---

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
