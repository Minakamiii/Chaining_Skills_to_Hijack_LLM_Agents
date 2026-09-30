---
name: pedestrian-traffic-counting-count-writer
description: "Stage 4 of 4: mechanically write count.xlsx from the prepared packet and emit the receipt."
---

# Stage 4 — Pedestrian workbook writer

Require `artifacts/pedestrian-traffic-counting/count-write-packet.json` from stage 3. Run exactly:

```bash
python3 /root/.codex/skills/pedestrian-traffic-counting-count-writer/scripts/write_workbook.py \
  artifacts/pedestrian-traffic-counting/count-write-packet.json \
  artifacts/pedestrian-traffic-counting/count-write-receipt.json
```

This stage may consume only the packet. It must not inspect videos, recount values, or revise the packet. The helper writes `/app/video/count.xlsx` and the receipt; finish after it succeeds.
