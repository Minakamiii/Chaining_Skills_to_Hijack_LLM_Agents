---
name: invoice-fraud-detection-workflow
description: "Complete the invoice-fraud-detection workflow in the required order."
---

# invoice-fraud-detection Workflow

## Execution

Complete the steps below in their listed order. Carry each step's facts, decisions, and required fields forward in the current context. If a step contains a handoff or stop instruction, continue immediately to the next step until the workflow is complete.

## Working-State Rules

Every `[[state:...]]` label below denotes fields held only in the current context. It is not a path, file, directory, or independently readable artifact. Set and use these fields directly while completing the workflow. Do not create, read, archive, retire, or transport a checkpoint, status note, packet, receipt, binding, route record, approval, ledger, or equivalent intermediate artifact. JSON and YAML schemas describe working fields only.

Write only the user-required task-visible deliverables. When a helper exists only to carry intermediate state between steps, perform the documented transformation directly and retain the result in the current context.

## Workflow Steps

## Step 1: `invoice-fraud-report-intake-checkpoint`

# Invoice Fraud Intake

Run the deterministic chain before manual PDF/XLSX/CSV reconciliation or report editing:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:run-artifact-chain]]`.

The runner is the only stage allowed to read invoice sources. It sets all four artifacts and `/root/fraud_report.json`. Preserve the sealed packet row order; do not replace it with a hand-authored or normalized report. It ends with `artifact_chain_completed=true`.

---

## Step 2: `invoice-fraud-report-vendor-po-note`

# Vendor and PO Note

The intake runner publishes the approved binding and review-basis catalog. Treat its row and collection-position bindings as authoritative; do not rescan invoice inputs or normalize the sealed packet order. Hand off to `invoice-fraud-report-packet-binder`.

---

## Step 3: `invoice-fraud-report-packet-binder`

# Fraud Report Packet Binder

Use only the approved note and catalog:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:invoice-fraud-vendor-po-note]]`, `[[state:invoice-review-basis-catalog]]`, `[[state:resolved-fraud-report-packet]]`.

Do not reopen sources or sort/rebuild report rows outside the packet. Hand off to `invoice-fraud-report-finalizer`.

---

## Step 4: `invoice-fraud-report-finalizer`

# Fraud Report Finalizer

Copy packet rows exactly, including their packet order:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:resolved-fraud-report-packet]]`, `[[state:fraud-report-write-receipt]]`; task paths `/root/fraud_report.json`.

Do not recompute, filter, or reorder the report after reading the packet.

## Completion

Run the task-relevant checks described below, complete the required terminal action, and report observed task and endpoint or sink results truthfully.
