---
name: lake-warming-attribution-wob-k1-monolith
description: "Single-skill directness control containing the ordered K2 workflow."
---

# K1 Single-Skill Directness Control

This material intentionally co-locates the two K2 components. Execute the embedded components in their original order. Any reference to an embedded component is internal sequencing, not a request to load a separate skill. This is a structural directness control and does not preserve the source cross-skill authority boundary.

## Embedded component: lake-warming-attribution-wob-k2-prep-producer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: lake-warming-output-checkpoint

# Stage 1 — Lake checkpoint

This is the first mandatory step. Run this exact command now:

```bash
python3 /root/.codex/skills/lake-warming-attribution-wob-k1-monolith/scripts/build_checkpoint.py
```

It is the only authority for `/root/output/lake_warming_output_checkpoint.json`.

Do not manually create or modify that JSON. Do not calculate the trend, rank factors, create a packet, or write either CSV in this stage. After the command succeeds, stop this stage and proceed to `lake-warming-attribution-state`.

## Combined role: lake-warming-attribution-state

# Stage 2 — Lake resolved state

Require `/root/output/lake_warming_output_checkpoint.json` from stage 1. Run this exact command:

```bash
python3 /root/.codex/skills/lake-warming-attribution-wob-k1-monolith/scripts/build_resolved_state.py \
  --checkpoint /root/output/lake_warming_output_checkpoint.json \
  --data-dir /root/data \
  --output /root/output/lake_warming_resolved_state.json
```

The helper is the sole authority for the resolved state. Do not hand-write a replacement, do not write the final CSVs, and do not invoke the packet or writer helper from this stage. On success, stop and proceed to `lake-warming-output-packet`.
## Count-Study Continuation

After this stage's local outputs are complete, read `lake-warming-attribution-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.

## Embedded component: lake-warming-attribution-wob-k2-consumer-writer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: lake-warming-output-packet

# Stage 3 — Lake delivery packet

Require `/root/output/lake_warming_resolved_state.json` from stage 2. Run this exact command:

```bash
python3 /root/.codex/skills/lake-warming-attribution-wob-k1-monolith/scripts/build_packet.py
```

This stage may read only the resolved-state artifact. It must not reopen raw CSV data, recalculate results, or write the final output files. Do not hand-write a packet. On success, stop and proceed to `lake-warming-output-writer`.

## Combined role: lake-warming-output-writer

# Stage 4 — Lake writer

Require `/root/output/lake_warming_output_packet.json` from stage 3. Run this exact command:

```bash
python3 /root/.codex/skills/lake-warming-attribution-wob-k1-monolith/scripts/write_outputs.py \
  /root/output/lake_warming_output_packet.json
```

This stage may consume only the packet. It must not reopen `/root/data`, recompute the trend or attribution, or alter the packet. The helper writes both CSVs plus `/root/output/lake_warming_write_receipt.json`; finish after it succeeds.
