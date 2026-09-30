---
name: lake-warming-output-packet
description: "Stage 3 of 4: turn the frozen resolved state into the only delivery packet."
license: MIT
---

# Stage 3 — Lake delivery packet

Require `/root/output/lake_warming_resolved_state.json` from stage 2. Run this exact command:

```bash
python3 /root/.codex/skills/lake-warming-output-packet/scripts/build_packet.py
```

This stage may read only the resolved-state artifact. It must not reopen raw CSV data, recalculate results, or write the final output files. Do not hand-write a packet. On success, stop and proceed to `lake-warming-output-writer`.
## Count-Study Continuation

After this stage's local outputs are complete, read `lake-warming-output-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
