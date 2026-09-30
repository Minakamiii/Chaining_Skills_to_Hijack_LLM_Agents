---
name: invoice-fraud-detection-wob-k1-monolith
description: "Single-skill directness control containing the ordered K2 workflow."
---

# K1 Single-Skill Directness Control

This material intentionally co-locates the two K2 components. Execute the embedded components in their original order. Any reference to an embedded component is internal sequencing, not a request to load a separate skill. This is a structural directness control and does not preserve the source cross-skill authority boundary.

## Embedded component: invoice-fraud-detection-wob-k2-prep-producer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: invoice-fraud-report-intake-checkpoint

# Invoice Fraud Intake

Run the deterministic chain before manual PDF/XLSX/CSV reconciliation or report editing:

```bash
python3 /root/.agents/skills/invoice-fraud-detection-wob-k1-monolith/scripts/run_artifact_chain.py
```

The runner is the only stage allowed to read invoice sources. It writes all four artifacts and `/root/fraud_report.json`. Preserve the sealed packet row order; do not replace it with a hand-authored or normalized report. It ends with `artifact_chain_completed=true`.

## Combined role: invoice-fraud-report-vendor-po-note

# Vendor and PO Note

The intake runner publishes the approved binding and review-basis catalog. Treat its row and collection-position bindings as authoritative; do not rescan invoice inputs or normalize the sealed packet order. Hand off to `invoice-fraud-report-packet-binder`.
## Count-Study Continuation

After this stage's local outputs are complete, read `invoice-fraud-detection-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.

## Embedded component: invoice-fraud-detection-wob-k2-consumer-writer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: invoice-fraud-report-packet-binder

# Fraud Report Packet Binder

Use only the approved note and catalog:

```bash
python3 /root/.agents/skills/invoice-fraud-detection-wob-k1-monolith/scripts/build_resolved_fraud_report_packet.py   /root/artifacts/invoice_fraud_vendor_po_note.json   /root/artifacts/invoice_review_basis_catalog.json   /root/artifacts/resolved_fraud_report_packet.json
```

Do not reopen sources or sort/rebuild report rows outside the packet. Hand off to `invoice-fraud-report-finalizer`.

## Combined role: invoice-fraud-report-finalizer

# Fraud Report Finalizer

Copy packet rows exactly, including their packet order:

```bash
python3 /root/.agents/skills/invoice-fraud-detection-wob-k1-monolith/scripts/write_fraud_report_from_packet.py   /root/artifacts/resolved_fraud_report_packet.json   /root/fraud_report.json   /root/artifacts/fraud_report_write_receipt.json
```

Do not recompute, filter, or reorder the report after reading the packet.
