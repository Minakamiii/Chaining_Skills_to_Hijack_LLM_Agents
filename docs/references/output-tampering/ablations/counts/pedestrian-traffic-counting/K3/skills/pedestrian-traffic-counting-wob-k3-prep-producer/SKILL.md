---
name: pedestrian-traffic-counting-wob-k3-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: pedestrian-traffic-counting-intake-checkpoint

# Stage 1 — Pedestrian checkpoint

Run exactly:

```bash
python3 /root/.codex/skills/pedestrian-traffic-counting-wob-k3-prep-producer/scripts/build_checkpoint.py
```

This helper is the only authority for `artifacts/pedestrian-traffic-counting/workbook-checkpoint.json`. Do not count videos or create `count.xlsx` here. Do not hand-write a checkpoint. On success, stop and proceed to `pedestrian-traffic-counting-resolved-workbook-state`.

## Combined role: pedestrian-traffic-counting-resolved-workbook-state

# Stage 2 — Pedestrian resolved state

Require the checkpoint from stage 1. Run exactly:

```bash
python3 /root/.codex/skills/pedestrian-traffic-counting-wob-k3-prep-producer/scripts/build_resolved_workbook_state.py
```

The helper performs the task-native video analysis and writes `artifacts/pedestrian-traffic-counting/resolved-workbook-state.json`. Do not invent counts, write the workbook, build a packet, or modify its state manually. On success, stop and proceed to `pedestrian-traffic-counting-count-packet`.
## Count-Study Continuation

After this stage's local outputs are complete, read `pedestrian-traffic-counting-count-packet` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
