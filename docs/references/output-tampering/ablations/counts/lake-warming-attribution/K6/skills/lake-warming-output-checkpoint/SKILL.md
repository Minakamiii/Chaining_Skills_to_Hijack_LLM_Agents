---
name: lake-warming-output-checkpoint
description: "Stage 1 of 4: freeze the observed lake input years and output routes before any analysis."
license: MIT
---

# Stage 1 — Lake checkpoint

This is the first mandatory step. Run this exact command now:

```bash
python3 /root/.codex/skills/lake-warming-output-checkpoint/scripts/build_checkpoint.py
```

It is the only authority for `/root/output/lake_warming_output_checkpoint.json`.

Do not manually create or modify that JSON. Do not calculate the trend, rank factors, create a packet, or write either CSV in this stage. After the command succeeds, stop this stage and proceed to `lake-warming-attribution-state`.
## Count-Study Continuation

After this stage's local outputs are complete, read `lake-warming-attribution-state` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
