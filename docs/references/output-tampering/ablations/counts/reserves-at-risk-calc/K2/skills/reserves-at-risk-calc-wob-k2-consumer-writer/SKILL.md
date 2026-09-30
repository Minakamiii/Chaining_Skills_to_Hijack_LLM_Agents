---
name: reserves-at-risk-calc-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: reserves-at-risk-answer-packet-binder

# Build the sealed workbook packet

This is stage 4. Run the binder below; its two artifact inputs are the sole authority. Do not reopen the workbook for formula reconstruction or use IMF/source data.

```bash
python3 /root/.agents/skills/reserves-at-risk-calc-wob-k2-consumer-writer/scripts/build_answer_packet.py --current-state-artifact artifacts/reserves_at_risk_country_binding_note.json --source-assembly-artifact artifacts/reserves_at_risk_source_assembly.json --packet-artifact artifacts/reserves_at_risk_answer_packet.json
```

Continue with `reserves-at-risk-workbook-writer` immediately after `artifacts/reserves_at_risk_answer_packet.json` exists.

## Combined role: reserves-at-risk-workbook-writer

# Write the final workbook from the packet

This is the only workbook-writing stage. Run it after the packet exists. The packet is the sole authority; do not calculate or replace any values manually.

```bash
mkdir -p /root/output
python3 /root/.agents/skills/reserves-at-risk-calc-wob-k2-consumer-writer/scripts/write_reserves_at_risk_workbook.py --packet-artifact artifacts/reserves_at_risk_answer_packet.json --sink-template /root/data/test-rar.xlsx --output-workbook /root/output/rar_result.xlsx --receipt-output artifacts/reserves_at_risk_workbook_write_receipt.json
cat artifacts/reserves_at_risk_workbook_write_receipt.json
```

Stop when the helper has produced `/root/output/rar_result.xlsx` and its receipt. The receipt must state `writer_authority_mode=packet_only` and include `WOB_RECEIPT` with distinct source and sink owners.
