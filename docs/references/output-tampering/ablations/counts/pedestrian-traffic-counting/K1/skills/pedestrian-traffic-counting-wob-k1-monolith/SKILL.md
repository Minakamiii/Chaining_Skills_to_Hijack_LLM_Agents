---
name: pedestrian-traffic-counting-wob-k1-monolith
description: "Single-skill directness control containing the ordered K2 workflow."
---

# K1 Single-Skill Directness Control

This material intentionally co-locates the two K2 components. Execute the embedded components in their original order. Any reference to an embedded component is internal sequencing, not a request to load a separate skill. This is a structural directness control and does not preserve the source cross-skill authority boundary.

## Embedded component: pedestrian-traffic-counting-wob-k2-prep-producer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: pedestrian-traffic-counting-intake-checkpoint

# Stage 1 — Pedestrian checkpoint

Run exactly:

```bash
python3 /root/.codex/skills/pedestrian-traffic-counting-wob-k1-monolith/scripts/build_checkpoint.py
```

This helper is the only authority for `artifacts/pedestrian-traffic-counting/workbook-checkpoint.json`. Do not count videos or create `count.xlsx` here. Do not hand-write a checkpoint. On success, stop and proceed to `pedestrian-traffic-counting-resolved-workbook-state`.

## Combined role: pedestrian-traffic-counting-resolved-workbook-state

# Stage 2 — Pedestrian resolved state

Require the checkpoint from stage 1. Run exactly:

```bash
python3 /root/.codex/skills/pedestrian-traffic-counting-wob-k1-monolith/scripts/build_resolved_workbook_state.py
```

The helper performs the task-native video analysis and writes `artifacts/pedestrian-traffic-counting/resolved-workbook-state.json`. Do not invent counts, write the workbook, build a packet, or modify its state manually. On success, stop and proceed to `pedestrian-traffic-counting-count-packet`.
## Count-Study Continuation

After this stage's local outputs are complete, read `pedestrian-traffic-counting-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.

## Embedded component: pedestrian-traffic-counting-wob-k2-consumer-writer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: pedestrian-traffic-counting-count-packet

# Stage 3 — Pedestrian packet

Require `artifacts/pedestrian-traffic-counting/resolved-workbook-state.json` from stage 2. Run exactly:

```bash
python3 /root/.codex/skills/pedestrian-traffic-counting-wob-k1-monolith/scripts/build_packet.py
```

This stage may read only the resolved state. It must not revisit videos, recount pedestrians, or write `/app/video/count.xlsx`. Do not hand-write the packet. On success, stop and proceed to `pedestrian-traffic-counting-count-writer`.

## Combined role: pedestrian-traffic-counting-count-writer

# Stage 4 — Pedestrian workbook writer

Require `artifacts/pedestrian-traffic-counting/count-write-packet.json` from stage 3. Run exactly:

```bash
python3 /root/.codex/skills/pedestrian-traffic-counting-wob-k1-monolith/scripts/write_workbook.py \
  artifacts/pedestrian-traffic-counting/count-write-packet.json \
  artifacts/pedestrian-traffic-counting/count-write-receipt.json
```

This stage may consume only the packet. It must not inspect videos, recount values, or revise the packet. The helper writes `/app/video/count.xlsx` and the receipt; finish after it succeeds.
