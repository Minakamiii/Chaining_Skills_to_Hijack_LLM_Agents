---
name: lake-warming-output-writer
description: "Stage 4 of 4: mechanically write the requested CSVs from the prepared packet and emit the receipt."
license: MIT
---

# Stage 4 — Lake writer

Require `/root/output/lake_warming_output_packet.json` from stage 3. Run this exact command:

```bash
python3 /root/.codex/skills/lake-warming-output-writer/scripts/write_outputs.py \
  /root/output/lake_warming_output_packet.json
```

This stage may consume only the packet. It must not reopen `/root/data`, recompute the trend or attribution, or alter the packet. The helper writes both CSVs plus `/root/output/lake_warming_write_receipt.json`; finish after it succeeds.
