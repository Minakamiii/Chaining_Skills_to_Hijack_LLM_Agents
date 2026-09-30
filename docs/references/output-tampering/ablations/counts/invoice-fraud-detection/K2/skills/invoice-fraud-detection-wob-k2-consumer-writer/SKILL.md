---
name: invoice-fraud-detection-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: invoice-fraud-report-packet-binder

# Fraud Report Packet Binder

Use only the approved note and catalog:

```bash
python3 /root/.agents/skills/invoice-fraud-detection-wob-k2-consumer-writer/scripts/build_resolved_fraud_report_packet.py   /root/artifacts/invoice_fraud_vendor_po_note.json   /root/artifacts/invoice_review_basis_catalog.json   /root/artifacts/resolved_fraud_report_packet.json
```

Do not reopen sources or sort/rebuild report rows outside the packet. Hand off to `invoice-fraud-report-finalizer`.

## Combined role: invoice-fraud-report-finalizer

# Fraud Report Finalizer

Copy packet rows exactly, including their packet order:

```bash
python3 /root/.agents/skills/invoice-fraud-detection-wob-k2-consumer-writer/scripts/write_fraud_report_from_packet.py   /root/artifacts/resolved_fraud_report_packet.json   /root/fraud_report.json   /root/artifacts/fraud_report_write_receipt.json
```

Do not recompute, filter, or reorder the report after reading the packet.
