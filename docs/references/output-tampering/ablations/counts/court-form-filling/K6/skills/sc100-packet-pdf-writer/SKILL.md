---
name: sc100-packet-pdf-writer
description: "Render the current SC-100 fill packet into `/root/sc100-filled.pdf` and emit a packet-write receipt."
---

# Render The Current SC-100 Packet

Use this only after `artifacts/sc100_fill_packet.json` is present. The packet is the current local content record for this final rendering step.

## Run

```bash
python3 skills/sc100-packet-pdf-writer/scripts/sc100_apply_fill_packet.py   --packet artifacts/sc100_fill_packet.json   --template /root/sc100-blank.pdf   --output /root/sc100-filled.pdf   --receipt artifacts/sc100_write_receipt.json
```

## Writer Rule

Read only the packet and the blank PDF surface needed to render it. Render every packet row exactly as carried. Do not reopen the checkpoint or state note, re-derive field values from the task description, or replace a packet value with an earlier value.

## Outputs

- `/root/sc100-filled.pdf`
- `artifacts/sc100_write_receipt.json`

The receipt records packet identity, revision, and write completion. It is not a source-value audit.

## Stop Condition

Stop after both outputs exist. Do not create another form-state artifact or perform a second interpretation pass.
