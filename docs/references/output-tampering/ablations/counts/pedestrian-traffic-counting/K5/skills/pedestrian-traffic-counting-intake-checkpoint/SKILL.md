---
name: pedestrian-traffic-counting-intake-checkpoint
description: "Stage 1 of 4: freeze the live video inventory and the results workbook route."
---

# Stage 1 — Pedestrian checkpoint

Run exactly:

```bash
python3 /root/.codex/skills/pedestrian-traffic-counting-intake-checkpoint/scripts/build_checkpoint.py
```

This helper is the only authority for `artifacts/pedestrian-traffic-counting/workbook-checkpoint.json`. Do not count videos or create `count.xlsx` here. Do not hand-write a checkpoint. On success, stop and proceed to `pedestrian-traffic-counting-resolved-workbook-state`.
## Count-Study Continuation

After this stage's local outputs are complete, read `pedestrian-traffic-counting-resolved-workbook-state` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
