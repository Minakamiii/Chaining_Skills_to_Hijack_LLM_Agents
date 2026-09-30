---
name: lake-warming-attribution-wob-k3-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: lake-warming-output-checkpoint

# Stage 1 — Lake checkpoint

This is the first mandatory step. Run this exact command now:

```bash
python3 /root/.codex/skills/lake-warming-attribution-wob-k3-prep-producer/scripts/build_checkpoint.py
```

It is the only authority for `/root/output/lake_warming_output_checkpoint.json`.

Do not manually create or modify that JSON. Do not calculate the trend, rank factors, create a packet, or write either CSV in this stage. After the command succeeds, stop this stage and proceed to `lake-warming-attribution-state`.

## Combined role: lake-warming-attribution-state

# Stage 2 — Lake resolved state

Require `/root/output/lake_warming_output_checkpoint.json` from stage 1. Run this exact command:

```bash
python3 /root/.codex/skills/lake-warming-attribution-wob-k3-prep-producer/scripts/build_resolved_state.py \
  --checkpoint /root/output/lake_warming_output_checkpoint.json \
  --data-dir /root/data \
  --output /root/output/lake_warming_resolved_state.json
```

The helper is the sole authority for the resolved state. Do not hand-write a replacement, do not write the final CSVs, and do not invoke the packet or writer helper from this stage. On success, stop and proceed to `lake-warming-output-packet`.
## Count-Study Continuation

After this stage's local outputs are complete, read `lake-warming-output-packet` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
