---
name: seismic-phase-picking-resolved-pick-state
description: "Stage 2 of 4: use PhaseNet on the frozen trace inventory and seal the resolved pick state."
---

# Stage 2 — Seismic resolved picks

Require `workflow/seismic-phase-picking-trace-observation.json` from stage 1. Run exactly:

```bash
python3 /root/.codex/skills/seismic-phase-picking-resolved-pick-state/scripts/build_resolved_pick_state.py
```

The helper runs task-native PhaseNet on CPU with reproducible low-thread settings and the standard PhaseNet thresholds with one confidence-selected candidate per file and phase, then writes `workflow/seismic-phase-picking-resolved-state.json`. Do not hand-pick values, create a packet, or write `/root/results.csv` in this stage. On success, stop and proceed to `seismic-phase-picking-results-packet`.
