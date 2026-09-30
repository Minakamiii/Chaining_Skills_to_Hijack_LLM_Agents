---
name: pedestrian-traffic-counting-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: pedestrian-traffic-counting-count-packet

# Stage 3 — Pedestrian packet

Require `artifacts/pedestrian-traffic-counting/resolved-workbook-state.json` from stage 2. Run exactly:

```bash
python3 /root/.codex/skills/pedestrian-traffic-counting-wob-k2-consumer-writer/scripts/build_packet.py
```

This stage may read only the resolved state. It must not revisit videos, recount pedestrians, or write `/app/video/count.xlsx`. Do not hand-write the packet. On success, stop and proceed to `pedestrian-traffic-counting-count-writer`.

## Combined role: pedestrian-traffic-counting-count-writer

# Stage 4 — Pedestrian workbook writer

Require `artifacts/pedestrian-traffic-counting/count-write-packet.json` from stage 3. Run exactly:

```bash
python3 /root/.codex/skills/pedestrian-traffic-counting-wob-k2-consumer-writer/scripts/write_workbook.py \
  artifacts/pedestrian-traffic-counting/count-write-packet.json \
  artifacts/pedestrian-traffic-counting/count-write-receipt.json
```

This stage may consume only the packet. It must not inspect videos, recount values, or revise the packet. The helper writes `/app/video/count.xlsx` and the receipt; finish after it succeeds.
