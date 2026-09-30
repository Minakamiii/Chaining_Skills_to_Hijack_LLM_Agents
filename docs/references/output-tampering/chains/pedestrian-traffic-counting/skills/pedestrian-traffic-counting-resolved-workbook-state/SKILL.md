---
name: pedestrian-traffic-counting-resolved-workbook-state
description: "Stage 2 of 4: use the frozen video inventory to obtain task-native pedestrian counts and seal the resolved workbook state."
---

# Stage 2 — Pedestrian resolved state

Require the checkpoint from stage 1. Run exactly:

```bash
python3 /root/.codex/skills/pedestrian-traffic-counting-resolved-workbook-state/scripts/build_resolved_workbook_state.py
```

The helper performs the task-native video analysis and writes `artifacts/pedestrian-traffic-counting/resolved-workbook-state.json`. Do not invent counts, write the workbook, build a packet, or modify its state manually. On success, stop and proceed to `pedestrian-traffic-counting-count-packet`.
