---
name: lake-warming-attribution-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: lake-warming-output-packet

# Stage 3 — Lake delivery packet

Require `/root/output/lake_warming_resolved_state.json` from stage 2. Run this exact command:

```bash
python3 /root/.codex/skills/lake-warming-attribution-wob-k2-consumer-writer/scripts/build_packet.py
```

This stage may read only the resolved-state artifact. It must not reopen raw CSV data, recalculate results, or write the final output files. Do not hand-write a packet. On success, stop and proceed to `lake-warming-output-writer`.

## Combined role: lake-warming-output-writer

# Stage 4 — Lake writer

Require `/root/output/lake_warming_output_packet.json` from stage 3. Run this exact command:

```bash
python3 /root/.codex/skills/lake-warming-attribution-wob-k2-consumer-writer/scripts/write_outputs.py \
  /root/output/lake_warming_output_packet.json
```

This stage may consume only the packet. It must not reopen `/root/data`, recompute the trend or attribution, or alter the packet. The helper writes both CSVs plus `/root/output/lake_warming_write_receipt.json`; finish after it succeeds.
