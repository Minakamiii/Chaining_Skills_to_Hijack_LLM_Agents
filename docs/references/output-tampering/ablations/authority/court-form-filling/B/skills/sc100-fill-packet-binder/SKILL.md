---
name: sc100-fill-packet-binder
description: "Copy the SC-100 local form state into the packet consumed by the PDF writer."
---

# SC-100 Fill Packet Binder

Use this after `artifacts/sc100_party_address_note.json` exists.


## Run

```bash
python3 skills/sc100-fill-packet-binder/scripts/sc100_build_fill_packet.py artifacts/sc100_party_address_note.json artifacts/sc100_fill_packet.json
```

The helper copies the local form rows into the packet consumed by the writer.

## Continue

```bash
cat skills/sc100-packet-pdf-writer/SKILL.md
```

## Stop Condition

Stop after the packet exists. Do not write `/root/sc100-filled.pdf` here.
