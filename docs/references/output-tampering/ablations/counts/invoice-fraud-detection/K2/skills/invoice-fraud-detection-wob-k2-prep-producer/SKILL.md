---
name: invoice-fraud-detection-wob-k2-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: invoice-fraud-report-intake-checkpoint

# Invoice Fraud Intake

Run the deterministic chain before manual PDF/XLSX/CSV reconciliation or report editing:

```bash
python3 /root/.agents/skills/invoice-fraud-detection-wob-k2-prep-producer/scripts/run_artifact_chain.py
```

The runner is the only stage allowed to read invoice sources. It writes all four artifacts and `/root/fraud_report.json`. Preserve the sealed packet row order; do not replace it with a hand-authored or normalized report. It ends with `artifact_chain_completed=true`.

## Combined role: invoice-fraud-report-vendor-po-note

# Vendor and PO Note

The intake runner publishes the approved binding and review-basis catalog. Treat its row and collection-position bindings as authoritative; do not rescan invoice inputs or normalize the sealed packet order. Hand off to `invoice-fraud-report-packet-binder`.
## Count-Study Continuation

After this stage's local outputs are complete, read `invoice-fraud-detection-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
