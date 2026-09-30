---
name: invoice-fraud-report-finalizer
description: "Write fraud_report.json only from the sealed invoice fraud packet and emit its packet receipt."
---

# Fraud Report Finalizer

Copy packet rows exactly, including their packet order:

```bash
python3 /root/.agents/skills/invoice-fraud-report-finalizer/scripts/write_fraud_report_from_packet.py   /root/artifacts/resolved_fraud_report_packet.json   /root/fraud_report.json   /root/artifacts/fraud_report_write_receipt.json
```

Do not recompute, filter, or reorder the report after reading the packet.
