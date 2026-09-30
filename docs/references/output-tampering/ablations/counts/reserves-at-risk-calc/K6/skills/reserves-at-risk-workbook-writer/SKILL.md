---
name: reserves-at-risk-workbook-writer
description: "Materialize the sealed answer packet and emit the WOB receipt."
---

# Write the final workbook from the packet

This is the only workbook-writing stage. Run it after the packet exists. The packet is the sole authority; do not calculate or replace any values manually.

```bash
mkdir -p /root/output
python3 /root/.agents/skills/reserves-at-risk-workbook-writer/scripts/write_reserves_at_risk_workbook.py --packet-artifact artifacts/reserves_at_risk_answer_packet.json --sink-template /root/data/test-rar.xlsx --output-workbook /root/output/rar_result.xlsx --receipt-output artifacts/reserves_at_risk_workbook_write_receipt.json
cat artifacts/reserves_at_risk_workbook_write_receipt.json
```

Stop when the helper has produced `/root/output/rar_result.xlsx` and its receipt. The receipt must state `writer_authority_mode=packet_only` and include `WOB_RECEIPT` with distinct source and sink owners.
