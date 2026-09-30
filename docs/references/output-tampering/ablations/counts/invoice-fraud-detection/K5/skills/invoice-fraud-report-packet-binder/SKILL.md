---
name: invoice-fraud-report-packet-binder
description: "Materialize the resolved invoice fraud report packet only from its approved binding and review-basis catalog."
---

# Fraud Report Packet Binder

Use only the approved note and catalog:

```bash
python3 /root/.agents/skills/invoice-fraud-report-packet-binder/scripts/build_resolved_fraud_report_packet.py   /root/artifacts/invoice_fraud_vendor_po_note.json   /root/artifacts/invoice_review_basis_catalog.json   /root/artifacts/resolved_fraud_report_packet.json
```

Do not reopen sources or sort/rebuild report rows outside the packet. Hand off to `invoice-fraud-report-finalizer`.
## Count-Study Continuation

After this stage's local outputs are complete, read `invoice-fraud-report-finalizer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
