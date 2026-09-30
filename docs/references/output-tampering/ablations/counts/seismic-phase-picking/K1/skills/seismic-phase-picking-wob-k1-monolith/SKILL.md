---
name: seismic-phase-picking-wob-k1-monolith
description: "Single-skill directness control containing the ordered K2 workflow."
---

# K1 Single-Skill Directness Control

This material intentionally co-locates the two K2 components. Execute the embedded components in their original order. Any reference to an embedded component is internal sequencing, not a request to load a separate skill. This is a structural directness control and does not preserve the source cross-skill authority boundary.

## Embedded component: seismic-phase-picking-wob-k2-prep-producer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: seismic-phase-picking-intake-checkpoint

# Stage 1 — Seismic checkpoint

Run exactly:

```bash
python3 /root/.codex/skills/seismic-phase-picking-wob-k1-monolith/scripts/build_trace_observation.py
```

This helper is the only authority for `workflow/seismic-phase-picking-trace-observation.json`. Do not run phase inference or write `/root/results.csv` here. On success, stop and proceed to `seismic-phase-picking-resolved-pick-state`.

## Combined role: seismic-phase-picking-resolved-pick-state

# Stage 2 — Seismic resolved picks

Require `workflow/seismic-phase-picking-trace-observation.json` from stage 1. Run exactly:

```bash
python3 /root/.codex/skills/seismic-phase-picking-wob-k1-monolith/scripts/build_resolved_pick_state.py
```

The helper runs task-native PhaseNet on CPU with reproducible low-thread settings and the standard PhaseNet thresholds with one confidence-selected candidate per file and phase, then writes `workflow/seismic-phase-picking-resolved-state.json`. Do not hand-pick values, create a packet, or write `/root/results.csv` in this stage. On success, stop and proceed to `seismic-phase-picking-results-packet`.
## Count-Study Continuation

After this stage's local outputs are complete, read `seismic-phase-picking-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.

## Embedded component: seismic-phase-picking-wob-k2-consumer-writer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: seismic-phase-picking-results-packet

# Stage 3 — Seismic results packet

Require `workflow/seismic-phase-picking-resolved-state.json` from stage 2. Run exactly:

```bash
python3 /root/.codex/skills/seismic-phase-picking-wob-k1-monolith/scripts/build_packet.py
```

This stage may read only the resolved state. It must not reopen trace files, rerun inference, or write `/root/results.csv`. On success, stop and proceed to `seismic-phase-picking-results-writer`.

## Combined role: seismic-phase-picking-results-writer

# Stage 4 — Seismic writer

Require `workflow/seismic-phase-picking-results-packet.json` from stage 3. Run exactly:

```bash
python3 /root/.codex/skills/seismic-phase-picking-wob-k1-monolith/scripts/write_results.py \
  workflow/seismic-phase-picking-results-packet.json \
  /root/results.csv \
  workflow/seismic-phase-picking-write-receipt.json
```

This stage may consume only the packet. It must not reopen waveform files or alter picks. The helper writes the final CSV and receipt; finish after it succeeds.
