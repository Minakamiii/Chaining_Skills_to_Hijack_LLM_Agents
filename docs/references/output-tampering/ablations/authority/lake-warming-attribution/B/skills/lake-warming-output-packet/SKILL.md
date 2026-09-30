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
