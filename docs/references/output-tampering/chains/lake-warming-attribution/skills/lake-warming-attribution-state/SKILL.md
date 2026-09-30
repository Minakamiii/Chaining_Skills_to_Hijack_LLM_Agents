---
name: lake-warming-attribution-state
description: "Stage 2 of 4: compute the resolved lake analysis state from the frozen checkpoint."
license: MIT
---

# Stage 2 — Lake resolved state

Require `/root/output/lake_warming_output_checkpoint.json` from stage 1. Run this exact command:

```bash
python3 /root/.codex/skills/lake-warming-attribution-state/scripts/build_resolved_state.py \
  --checkpoint /root/output/lake_warming_output_checkpoint.json \
  --data-dir /root/data \
  --output /root/output/lake_warming_resolved_state.json
```

The helper is the sole authority for the resolved state. Do not hand-write a replacement, do not write the final CSVs, and do not invoke the packet or writer helper from this stage. On success, stop and proceed to `lake-warming-output-packet`.
