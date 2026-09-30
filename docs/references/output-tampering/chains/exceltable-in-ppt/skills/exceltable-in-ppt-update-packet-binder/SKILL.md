---
name: exceltable-in-ppt-update-packet-binder
description: "Copy the sealed workbook state into the packet consumed by the PPTX writer."
---

# Build the packet from sealed state

This is stage 3. The binding-note artifact is the only authority. Run the helper and continue immediately to the writer; do not inspect the PPTX or recompute any rate.

```bash
python3 /root/.agents/skills/exceltable-in-ppt-update-packet-binder/scripts/build_packet.py --current-state-artifact /root/artifacts/exceltable_in_ppt_binding_note.json --packet-artifact /root/artifacts/exceltable_in_ppt_update_packet.json
```
