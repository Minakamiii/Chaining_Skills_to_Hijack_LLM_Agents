---
name: powerlifting-dots-formula-packet-binder
description: "Copy the sealed Dots write state into a packet without reopening the workbook."
---

# Powerlifting Dots Packet Binder

Use only `resolved_dots_state` from `artifacts/powerlifting-dots-approved-fragment-binding-table.json`. This stage does not accept the workbook and must not rediscover headers, source rows, or formulas.

## Exact command

```bash
python3 /root/.codex/skills/powerlifting-dots-formula-packet-binder/scripts/build_formula_packet.py \
  --binding artifacts/powerlifting-dots-approved-fragment-binding-table.json \
  --output artifacts/powerlifting-dots-resolved-formula-packet.json
```

The resulting packet is the sole authority for the writer.
## Count-Study Continuation

After this stage's local outputs are complete, read `powerlifting-dots-workbook-finalizer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
