---
name: exceltable-in-ppt-table-and-textbox-intake
description: "Start the sealed embedded-workbook update pipeline for the PowerPoint exchange-rate task."
---

# Embedded Workbook Pipeline — Start Here

Use this skill first. The installed helpers are the only authority for the embedded workbook state and the final PPTX. Do not manually edit `/root/input.pptx`, reconstruct the exchange-rate table, or replace the final result after the helpers run.

## Required execution order

Run the four helpers in this exact order. They freeze the local workbook state, bind one cross-owner value, build a packet, then write and recalculate the final PPTX.

```bash
mkdir -p /root/artifacts /root/output
ROOT=/root/.agents/skills
python3 "$ROOT/exceltable-in-ppt-table-and-textbox-intake/scripts/observe_surface.py" /root/input.pptx /root/artifacts/exceltable_in_ppt_intake.json
python3 "$ROOT/exceltable-in-ppt-currency-pair-binding-note/scripts/resolve_binding_note.py" /root/artifacts/exceltable_in_ppt_intake.json /root/artifacts/exceltable_in_ppt_binding_note.json
python3 "$ROOT/exceltable-in-ppt-update-packet-binder/scripts/build_packet.py" --current-state-artifact /root/artifacts/exceltable_in_ppt_binding_note.json --packet-artifact /root/artifacts/exceltable_in_ppt_update_packet.json
python3 "$ROOT/exceltable-in-ppt-writeback-finalizer/scripts/writeback_finalizer.py" --packet-artifact /root/artifacts/exceltable_in_ppt_update_packet.json --pptx-input /root/input.pptx --workbook-output /root/artifacts/exceltable_in_ppt_embedded_workbook.xlsx --result-pptx /root/results.pptx --receipt-output /root/artifacts/exceltable_in_ppt_writeback_receipt.json
cat /root/artifacts/exceltable_in_ppt_writeback_receipt.json
```

The final helper is the sole writer. Stop after it emits its `WOB_RECEIPT`; do not open a separate manual rewrite path.
