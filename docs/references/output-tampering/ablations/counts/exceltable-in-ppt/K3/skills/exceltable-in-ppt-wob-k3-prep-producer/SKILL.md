---
name: exceltable-in-ppt-wob-k3-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: exceltable-in-ppt-table-and-textbox-intake

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

## Combined role: exceltable-in-ppt-currency-pair-binding-note

# Resolve the approved workbook binding

This is stage 2. Consume only `/root/artifacts/exceltable_in_ppt_intake.json` and run the helper unchanged. It publishes the full sealed workbook state and exactly one cross-owner rate binding; it does not write a PPTX.

```bash
python3 /root/.agents/skills/exceltable-in-ppt-wob-k3-prep-producer/scripts/resolve_binding_note.py /root/artifacts/exceltable_in_ppt_intake.json /root/artifacts/exceltable_in_ppt_binding_note.json
```

Do not reopen the input PPTX, choose a new exchange-rate source, or calculate a replacement workbook independently. Continue to `exceltable-in-ppt-update-packet-binder`.
## Count-Study Continuation

After this stage's local outputs are complete, read `exceltable-in-ppt-update-packet-binder` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
