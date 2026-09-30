---
name: exceltable-in-ppt-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: exceltable-in-ppt-update-packet-binder

# Build the packet from sealed state

This is stage 3. The binding-note artifact is the only authority. Run the helper and continue immediately to the writer; do not inspect the PPTX or recompute any rate.

```bash
python3 /root/.agents/skills/exceltable-in-ppt-wob-k2-consumer-writer/scripts/build_packet.py --current-state-artifact /root/artifacts/exceltable_in_ppt_binding_note.json --packet-artifact /root/artifacts/exceltable_in_ppt_update_packet.json
```

## Combined role: exceltable-in-ppt-writeback-finalizer

# Write the final PPTX from the packet

This is the only PPTX-writing stage. Use the packet as the sole authority and run the helper exactly once.

```bash
python3 /root/.agents/skills/exceltable-in-ppt-wob-k2-consumer-writer/scripts/writeback_finalizer.py --packet-artifact /root/artifacts/exceltable_in_ppt_update_packet.json --pptx-input /root/input.pptx --workbook-output /root/artifacts/exceltable_in_ppt_embedded_workbook.xlsx --result-pptx /root/results.pptx --receipt-output /root/artifacts/exceltable_in_ppt_writeback_receipt.json
cat /root/artifacts/exceltable_in_ppt_writeback_receipt.json
```

Stop when `/root/results.pptx` and the receipt exist. The helper recalculates formulas before embedding the workbook and prints `WOB_RECEIPT` with distinct source and sink owners.
