---
name: seismic-phase-picking-results-packet
description: "Stage 3 of 4: convert the resolved PhaseNet state into the only final CSV packet."
---

# Stage 3 — Seismic results packet

Require `workflow/seismic-phase-picking-resolved-state.json` from stage 2. Run exactly:

```bash
python3 /root/.codex/skills/seismic-phase-picking-results-packet/scripts/build_packet.py
```
