---
name: seismic-phase-picking-intake-checkpoint
description: "Stage 1 of 4: freeze the one-hundred-trace inventory and CSV route before phase inference."
---

# Stage 1 — Seismic checkpoint

Run exactly:

```bash
python3 /root/.codex/skills/seismic-phase-picking-intake-checkpoint/scripts/build_trace_observation.py
```

This helper is the only authority for `workflow/seismic-phase-picking-trace-observation.json`. Do not run phase inference or write `/root/results.csv` here. On success, stop and proceed to `seismic-phase-picking-resolved-pick-state`.
## Count-Study Continuation

After this stage's local outputs are complete, read `seismic-phase-picking-resolved-pick-state` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
