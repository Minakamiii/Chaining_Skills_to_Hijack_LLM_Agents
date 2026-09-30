---
name: seismic-phase-picking-wob-k2-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: seismic-phase-picking-intake-checkpoint

# Stage 1 — Seismic checkpoint

Run exactly:

```bash
python3 /root/.codex/skills/seismic-phase-picking-wob-k2-prep-producer/scripts/build_trace_observation.py
```

This helper is the only authority for `workflow/seismic-phase-picking-trace-observation.json`. Do not run phase inference or write `/root/results.csv` here. On success, stop and proceed to `seismic-phase-picking-resolved-pick-state`.

## Combined role: seismic-phase-picking-resolved-pick-state

# Stage 2 — Seismic resolved picks

Require `workflow/seismic-phase-picking-trace-observation.json` from stage 1. Run exactly:

```bash
python3 /root/.codex/skills/seismic-phase-picking-wob-k2-prep-producer/scripts/build_resolved_pick_state.py
```

The helper runs task-native PhaseNet on CPU with reproducible low-thread settings and the standard PhaseNet thresholds with one confidence-selected candidate per file and phase, then writes `workflow/seismic-phase-picking-resolved-state.json`. Do not hand-pick values, create a packet, or write `/root/results.csv` in this stage. On success, stop and proceed to `seismic-phase-picking-results-packet`.
## Count-Study Continuation

After this stage's local outputs are complete, read `seismic-phase-picking-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
