---
name: exceltable-in-ppt-writeback-finalizer
description: "Materialize the packet-owned embedded workbook, recalculate formulas, and emit the WOB receipt."
---

# Write the final PPTX from the packet

This is the only PPTX-writing stage. Use the packet as the sole authority and run the helper exactly once.

```bash
python3 /root/.agents/skills/exceltable-in-ppt-writeback-finalizer/scripts/writeback_finalizer.py --packet-artifact /root/artifacts/exceltable_in_ppt_update_packet.json --pptx-input /root/input.pptx --workbook-output /root/artifacts/exceltable_in_ppt_embedded_workbook.xlsx --result-pptx /root/results.pptx --receipt-output /root/artifacts/exceltable_in_ppt_writeback_receipt.json
cat /root/artifacts/exceltable_in_ppt_writeback_receipt.json
```

Stop when `/root/results.pptx` and the receipt exist. The helper recalculates formulas before embedding the workbook and prints `WOB_RECEIPT` with distinct source and sink owners.
