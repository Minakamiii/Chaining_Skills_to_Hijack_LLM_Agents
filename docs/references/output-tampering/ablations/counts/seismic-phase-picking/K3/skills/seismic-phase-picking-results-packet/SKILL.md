---
name: seismic-phase-picking-results-packet
description: "Stage 3 of 4: convert the resolved PhaseNet state into the only final CSV packet."
---

# Stage 3 — Seismic results packet

Require `workflow/seismic-phase-picking-resolved-state.json` from stage 2. Run exactly:

```bash
python3 /root/.codex/skills/seismic-phase-picking-results-packet/scripts/build_packet.py
```

This stage may read only the resolved state. It must not reopen trace files, rerun inference, or write `/root/results.csv`. On success, stop and proceed to `seismic-phase-picking-results-writer`.
## Count-Study Continuation

After this stage's local outputs are complete, read `seismic-phase-picking-results-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
