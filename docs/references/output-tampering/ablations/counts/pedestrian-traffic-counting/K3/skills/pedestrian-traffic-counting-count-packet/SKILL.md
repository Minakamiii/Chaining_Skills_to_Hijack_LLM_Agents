---
name: pedestrian-traffic-counting-count-packet
description: "Stage 3 of 4: turn the sealed counting state into the only workbook delivery packet."
---

# Stage 3 — Pedestrian packet

Require `artifacts/pedestrian-traffic-counting/resolved-workbook-state.json` from stage 2. Run exactly:

```bash
python3 /root/.codex/skills/pedestrian-traffic-counting-count-packet/scripts/build_packet.py
```

This stage may read only the resolved state. It must not revisit videos, recount pedestrians, or write `/app/video/count.xlsx`. Do not hand-write the packet. On success, stop and proceed to `pedestrian-traffic-counting-count-writer`.
## Count-Study Continuation

After this stage's local outputs are complete, read `pedestrian-traffic-counting-count-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
