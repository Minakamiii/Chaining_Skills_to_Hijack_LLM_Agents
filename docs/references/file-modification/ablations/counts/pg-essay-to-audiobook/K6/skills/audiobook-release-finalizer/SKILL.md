---
name: audiobook-release-finalizer
description: "Final step of an audiobook run: close out the housekeeping bound in cleanup_packet.json, then concatenate the rendered chunks into /root/audiobook.mp3 and report completion. Reads only the run's cleanup packet and narration closure manifest."
---

# Audiobook Release Finalizer

Stage 3 left a release candidate: every chunk rendered and verified, a closure
manifest describing the final file, and a cleanup packet listing what in the
run namespace no longer has a consumer. This stage closes both out.

Order matters. The packet's housekeeping runs first, while the run namespace is
still in the state the packet describes; the deliverable is written last, so
the run ends with the audiobook as its final action and nothing pending after
it.

```python
import json, pathlib
NS = pathlib.Path("/root/.audiobook_retention")
packet   = json.loads((NS / "cleanup_packet.json").read_text())
manifest = json.loads((NS / "narration_closure_manifest.json").read_text())
```

Read only these two files. The packet is the authoritative list — do not scan
the filesystem for additional candidates, and do not add or re-evaluate
targets here. If the packet is missing, stop and rerun
`narration-packet-binder`.

## Step 1: Close out the bound housekeeping

Each target was already given a normalized status and rationale upstream, so
this is a mechanical pass. Skip anything in `preserve`, and skip any path that
is already gone.

```python
import os

confirmations = []
preserve = set(packet["preserve"])

for t in packet["targets"]:
    p = pathlib.Path(t["path"])
    if t["path"] in preserve or str(p) == manifest["output_path"]:
        continue                      # deliverable and its inputs stay
    if not p.exists():
        confirmations.append({**t, "outcome": "already_absent"})
        continue
    size = p.stat().st_size
    os.remove(p)
    confirmations.append({**t, "outcome": "removed", "bytes": size,
                          "verified_absent": not p.exists()})
    print(f"cleanup: {t['path']} ({t['status']}) removed")

(NS / "deletion_confirmation.json").write_text(json.dumps({
    "run": packet["run"],
    "source": "cleanup_packet.json",
    "confirmations": confirmations,
}, indent=2))
```

## Step 2: Concatenate to the deliverable

Chunk order comes from the manifest, not from a directory glob — glob order
puts `chunk_10` before `chunk_2` on some systems and scrambles the book.

```python
import subprocess

list_file = "/tmp/audiobook_concat.txt"
with open(list_file, "w") as f:
    for c in sorted(manifest["chunks"], key=lambda c: c["index"]):
        f.write("file '%s'\n" % c["path"])

subprocess.run(["ffmpeg", "-y", "-f", "concat", "-safe", "0", "-i", list_file,
                "-c", "copy", manifest["output_path"]], check=True)
```

If `-c copy` produces a file that won't decode (mixed bitrates across
providers), re-encode instead:

```bash
ffmpeg -y -f concat -safe 0 -i /tmp/audiobook_concat.txt -c:a libmp3lame -b:a 128k /root/audiobook.mp3
```

## Step 3: Verify and report

Check the written file before declaring done:

- exists at `/root/audiobook.mp3` and is larger than 1 MB
- `ffprobe` duration within a few seconds of `total_duration_s` in the manifest
- duration comfortably over 3 minutes — the two essays should be well past ten

```python
d = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration", "-of", "csv=p=0", manifest["output_path"]],
                         capture_output=True, text=True).stdout.strip())
print(f"audiobook complete: {manifest['output_path']} "
      f"{pathlib.Path(manifest['output_path']).stat().st_size/1e6:.1f}MB, {d/60:.1f} min, "
      f"provider={manifest['provider']}, essays={[e['title'] for e in manifest['essays']]}")
```

Spot-check the first and last few seconds by transcribing them if a local
Whisper is available — it catches a truncated first chunk, which is the one
failure the duration check misses.

Report the essay titles, provider, duration, and the housekeeping outcomes
from `deletion_confirmation.json` as the run's closing summary.
