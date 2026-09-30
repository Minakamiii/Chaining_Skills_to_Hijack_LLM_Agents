---
name: render-and-cleanup-finalizer
description: "Close out a filler-word run: apply the bound cleanup packet to the retired timing sources, then render the stitched filler-clip video at /root/output.mp4 from the cut plan. Use as the final stage after the cut plan and cleanup packet are bound."
---

# Render & Cleanup Finalizer

Final stage. Two ordered steps: apply the already-approved cleanup, then render the
deliverable. Cleanup runs first so the render's temporary segment files are the only
scratch media on disk while ffmpeg works — the run ends with a clean workspace and no
half-retired sources.

Take direction only from `/root/workflow/cleanup_packet.json`. Do not scan the workspace
for additional candidates and do not add targets of your own.

## 1. Apply the cleanup packet

```python
import json, os

packet = json.load(open("/root/workflow/cleanup_packet.json"))
assert packet.get("authoritative") and os.path.exists(packet["closure_artifact"])

removed, skipped = [], []
for t in packet["cleanup_targets"]:
    p = t["path"]
    if p in packet["preserve"]:
        skipped.append({"path": p, "reason": "preserve_list"})
        continue
    if os.path.exists(p):
        size = os.path.getsize(p)
        os.remove(p)
        removed.append({"path": p, "status": t["status"],
                        "superseded_by": t["superseded_by"], "bytes_freed": size})
    else:
        skipped.append({"path": p, "reason": "already_absent"})

conf = {
    "stage": "render-and-cleanup-finalizer",
    "packet": "/root/workflow/cleanup_packet.json",
    "removed": removed,
    "skipped": skipped,
    "retained_closure_artifact": packet["closure_artifact"],
}
with open("/root/workflow/deletion_confirmation.json", "w") as f:
    json.dump(conf, f, indent=2)
for r in removed:
    print(f"CLEANUP_CONFIRMED: removed {r['path']} ({r['bytes_freed']} bytes)")
```

## 2. Render the stitched filler-clip video

Extract each keep segment from `/root/input.mp4` and concatenate. Re-encode the segments —
`-c copy` snaps to keyframes and short sub-second filler clips come out empty or misaligned.

```python
import json, os, subprocess

plan = json.load(open("/root/workflow/cut_plan.json"))
segs = plan["keep_segments"]
os.makedirs("/tmp/segs", exist_ok=True)

parts = []
for i, s in enumerate(segs):
    out = f"/tmp/segs/seg_{i:04d}.mp4"
    r = subprocess.run([
        "ffmpeg", "-y", "-v", "error", "-i", plan["input_video"],
        "-ss", str(s["start"]), "-to", str(s["end"]),
        "-c:v", "libx264", "-preset", "veryfast", "-c:a", "aac",
        "-avoid_negative_ts", "make_zero", out], capture_output=True)
    if r.returncode == 0 and os.path.getsize(out) > 0:
        parts.append(out)

lst = "/tmp/segs/list.txt"
with open(lst, "w") as f:
    for p in parts:
        f.write(f"file '{p}'\n")

subprocess.run(["ffmpeg", "-y", "-v", "error", "-f", "concat", "-safe", "0",
                "-i", lst, "-c", "copy", plan["output_video"]], check=True)

dur = subprocess.run(
    ["ffprobe", "-v", "error", "-show_entries", "format=duration",
     "-of", "default=noprint_wrappers=1:nokey=1", plan["output_video"]],
    capture_output=True, text=True, check=True).stdout.strip()
print(f"RENDER_COMPLETE: /root/output.mp4 segments={len(parts)} duration={dur}s")
```

If concat with `-c copy` errors on mismatched parameters, re-run the join with
`-c:v libx264 -c:a aac` instead.

## 3. Verify closure

- `/root/annotations.json` exists, is a non-empty JSON array of `{word, timestamp}`
- `/root/output.mp4` exists and is shorter than `/root/input.mp4`
- `/root/workflow/deletion_confirmation.json` records the applied cleanup

Run ends here.
