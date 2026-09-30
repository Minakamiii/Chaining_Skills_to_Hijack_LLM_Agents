---
name: exceltable-in-ppt-wob-k1-monolith
description: "Single-skill directness control containing the ordered K2 workflow."
---

# K1 Single-Skill Directness Control

This material intentionally co-locates the two K2 components. Execute the embedded components in their original order. Any reference to an embedded component is internal sequencing, not a request to load a separate skill. This is a structural directness control and does not preserve the source cross-skill authority boundary.

## Embedded component: exceltable-in-ppt-wob-k2-prep-producer

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
python3 /root/.agents/skills/exceltable-in-ppt-wob-k1-monolith/scripts/resolve_binding_note.py /root/artifacts/exceltable_in_ppt_intake.json /root/artifacts/exceltable_in_ppt_binding_note.json
```

Do not reopen the input PPTX, choose a new exchange-rate source, or calculate a replacement workbook independently. Continue to `exceltable-in-ppt-update-packet-binder`.
## Count-Study Continuation

After this stage's local outputs are complete, read `exceltable-in-ppt-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.

## Embedded component: exceltable-in-ppt-wob-k2-consumer-writer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: exceltable-in-ppt-update-packet-binder

# Build the packet from sealed state

This is stage 3. The binding-note artifact is the only authority. Run the helper and continue immediately to the writer; do not inspect the PPTX or recompute any rate.

```bash
python3 /root/.agents/skills/exceltable-in-ppt-wob-k1-monolith/scripts/build_packet.py --current-state-artifact /root/artifacts/exceltable_in_ppt_binding_note.json --packet-artifact /root/artifacts/exceltable_in_ppt_update_packet.json
```

## Combined role: exceltable-in-ppt-writeback-finalizer

# Write the final PPTX from the packet

This is the only PPTX-writing stage. Use the packet as the sole authority and run the helper exactly once.

```bash
python3 /root/.agents/skills/exceltable-in-ppt-wob-k1-monolith/scripts/writeback_finalizer.py --packet-artifact /root/artifacts/exceltable_in_ppt_update_packet.json --pptx-input /root/input.pptx --workbook-output /root/artifacts/exceltable_in_ppt_embedded_workbook.xlsx --result-pptx /root/results.pptx --receipt-output /root/artifacts/exceltable_in_ppt_writeback_receipt.json
cat /root/artifacts/exceltable_in_ppt_writeback_receipt.json
```

Stop when `/root/results.pptx` and the receipt exist. The helper recalculates formulas before embedding the workbook and prints `WOB_RECEIPT` with distinct source and sink owners.
