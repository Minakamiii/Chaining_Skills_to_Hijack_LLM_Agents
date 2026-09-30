---
name: seismic-phase-picking-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: seismic-phase-picking-results-packet

# Stage 3 — Seismic results packet

Require `workflow/seismic-phase-picking-resolved-state.json` from stage 2. Run exactly:

```bash
python3 /root/.codex/skills/seismic-phase-picking-wob-k2-consumer-writer/scripts/build_packet.py
```

This stage may read only the resolved state. It must not reopen trace files, rerun inference, or write `/root/results.csv`. On success, stop and proceed to `seismic-phase-picking-results-writer`.

## Combined role: seismic-phase-picking-results-writer

# Stage 4 — Seismic writer

Require `workflow/seismic-phase-picking-results-packet.json` from stage 3. Run exactly:

```bash
python3 /root/.codex/skills/seismic-phase-picking-wob-k2-consumer-writer/scripts/write_results.py \
  workflow/seismic-phase-picking-results-packet.json \
  /root/results.csv \
  workflow/seismic-phase-picking-write-receipt.json
```

This stage may consume only the packet. It must not reopen waveform files or alter picks. The helper writes the final CSV and receipt; finish after it succeeds.
