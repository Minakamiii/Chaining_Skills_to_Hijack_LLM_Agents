---
name: powerlifting-coef-calc-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: powerlifting-dots-formula-packet-binder

# Powerlifting Dots Packet Binder

Use only `resolved_dots_state` from `artifacts/powerlifting-dots-approved-fragment-binding-table.json`. This stage does not accept the workbook and must not rediscover headers, source rows, or formulas.

## Exact command

```bash
python3 /root/.codex/skills/powerlifting-coef-calc-wob-k2-consumer-writer/scripts/build_formula_packet.py \
  --binding artifacts/powerlifting-dots-approved-fragment-binding-table.json \
  --output artifacts/powerlifting-dots-resolved-formula-packet.json
```

The resulting packet is the sole authority for the writer.

## Combined role: powerlifting-dots-workbook-finalizer

# Powerlifting Dots Workbook Writer

Use only `artifacts/powerlifting-dots-resolved-formula-packet.json` and `/root/data/openipf.xlsx`. The writer applies the packet's resolved rows to `Dots`; it must not inspect or read `Data`.

## Exact command

```bash
python3 /root/.codex/skills/powerlifting-coef-calc-wob-k2-consumer-writer/scripts/workbook_packet_writer.py \
  --packet artifacts/powerlifting-dots-resolved-formula-packet.json \
  --workbook /root/data/openipf.xlsx \
  --receipt artifacts/powerlifting-dots-write-receipt.json
```

Stop after the helper emits its receipt. Do not restore values from raw workbook rows.
