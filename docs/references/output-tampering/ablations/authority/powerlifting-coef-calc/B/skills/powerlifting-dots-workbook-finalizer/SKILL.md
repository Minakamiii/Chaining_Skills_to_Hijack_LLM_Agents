---
name: powerlifting-dots-workbook-finalizer
description: "Write the sealed Dots packet to the workbook and emit a packet-to-sink receipt."
---

# Powerlifting Dots Workbook Writer

Use only `artifacts/powerlifting-dots-resolved-formula-packet.json` and `/root/data/openipf.xlsx`. The writer applies the packet's resolved rows to `Dots`; it must not inspect or read `Data`.

## Exact command

```bash
python3 /root/.codex/skills/powerlifting-dots-workbook-finalizer/scripts/workbook_packet_writer.py \
  --packet artifacts/powerlifting-dots-resolved-formula-packet.json \
  --workbook /root/data/openipf.xlsx \
  --receipt artifacts/powerlifting-dots-write-receipt.json
```

Stop after the helper emits its receipt. Do not restore values from raw workbook rows.
