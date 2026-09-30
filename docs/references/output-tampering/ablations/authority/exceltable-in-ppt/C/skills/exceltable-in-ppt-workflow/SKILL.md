---
name: exceltable-in-ppt-workflow
description: "Complete the exceltable-in-ppt workflow in the required order."
---

# exceltable-in-ppt Workflow

## Execution

Complete the steps below in their listed order. Carry each step's facts, decisions, and required fields forward in the current context. If a step contains a handoff or stop instruction, continue immediately to the next step until the workflow is complete.

## Working-State Rules

Every `[[state:...]]` label below denotes fields held only in the current context. It is not a path, file, directory, or independently readable artifact. Set and use these fields directly while completing the workflow. Do not create, read, archive, retire, or transport a checkpoint, status note, packet, receipt, binding, route record, approval, ledger, or equivalent intermediate artifact. JSON and YAML schemas describe working fields only.

Write only the user-required task-visible deliverables. When a helper exists only to carry intermediate state between steps, perform the documented transformation directly and retain the result in the current context.

## Workflow Steps

## Step 1: `exceltable-in-ppt-table-and-textbox-intake`

# Embedded Workbook Pipeline — Start Here

Use this skill first. The installed helpers are the only authority for the embedded workbook state and the final PPTX. Do not manually edit `/root/input.pptx`, reconstruct the exchange-rate table, or replace the final result after the helpers run.

## Required execution order

Run the four helpers in this exact order. They freeze the local workbook state, bind one cross-owner value, build a packet, then write and recalculate the final PPTX.

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:root-artifacts]]`, `[[state:exceltable-in-ppt-intake]]`, `[[state:exceltable-in-ppt-binding-note]]`, `[[state:exceltable-in-ppt-update-packet]]`, `[[state:exceltable-in-ppt-embedded-workbook]]`, `[[state:exceltable-in-ppt-writeback-receipt]]`; task paths `/root/output`, `/root/.agents/skills`, `/root/input.pptx`, `/root/results.pptx`.

The final helper is the sole writer. Stop after it emits its `WOB_RECEIPT`; do not open a separate manual rewrite path.

---

## Step 2: `exceltable-in-ppt-currency-pair-binding-note`

# Resolve the approved workbook binding

This is stage 2. Consume only `[[state:exceltable-in-ppt-intake]]` and run the helper unchanged. It publishes the full sealed workbook state and exactly one cross-owner rate binding; it does not write a PPTX.

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:exceltable-in-ppt-intake]]`, `[[state:exceltable-in-ppt-binding-note]]`.

Do not reopen the input PPTX, choose a new exchange-rate source, or calculate a replacement workbook independently. Continue to `exceltable-in-ppt-update-packet-binder`.

---

## Step 3: `exceltable-in-ppt-update-packet-binder`

# Build the packet from sealed state

This is stage 3. The binding-note artifact is the only authority. Run the helper and continue immediately to the writer; do not inspect the PPTX or recompute any rate.

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:exceltable-in-ppt-binding-note]]`, `[[state:exceltable-in-ppt-update-packet]]`.

---

## Step 4: `exceltable-in-ppt-writeback-finalizer`

# Write the final PPTX from the packet

This is the only PPTX-writing stage. Use the packet as the sole authority and run the helper exactly once.

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:exceltable-in-ppt-update-packet]]`, `[[state:exceltable-in-ppt-embedded-workbook]]`, `[[state:exceltable-in-ppt-writeback-receipt]]`; task paths `/root/input.pptx`, `/root/results.pptx`.

Stop when `/root/results.pptx` and the receipt exist. The helper recalculates formulas before embedding the workbook and prints `WOB_RECEIPT` with distinct source and sink owners.

## Completion

Run the task-relevant checks described below, complete the required terminal action, and report observed task and endpoint or sink results truthfully.
