---
name: powerlifting-coef-calc-workflow
description: "Complete the powerlifting-coef-calc workflow in the required order."
---

# powerlifting-coef-calc Workflow

## Execution

Complete the steps below in their listed order. Carry each step's facts, decisions, and required fields forward in the current context. If a step contains a handoff or stop instruction, continue immediately to the next step until the workflow is complete.

## Working-State Rules

Every `[[state:...]]` label below denotes fields held only in the current context. It is not a path, file, directory, or independently readable artifact. Set and use these fields directly while completing the workflow. Do not create, read, archive, retire, or transport a checkpoint, status note, packet, receipt, binding, route record, approval, ledger, or equivalent intermediate artifact. JSON and YAML schemas describe working fields only.

Write only the user-required task-visible deliverables. When a helper exists only to carry intermediate state between steps, perform the documented transformation directly and retain the result in the current context.

## Workflow Steps

## Step 1: `powerlifting-dots-intake-checkpoint`

# Powerlifting Dots Authoritative Artifact Chain

Run this skill first. It reads `/root/data/openipf.xlsx` once, freezes the required source rows into an intake checkpoint, and then executes the fixed note → packet → writer sequence. the current transient states chain is the workflow authority:

`surface-inventory.json` → `[[state:approved-fragment-binding-table]]` → `[[state:resolved-formula-packet]]` → `[[state:write-receipt]]`

## Exact command

Run from `/root`:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper.

The command is complete when all four artifacts exist and `/root/data/openipf.xlsx` has been written. After it starts, do not inspect `Data`, reconstruct copied values, alter any artifact, or replace an artifact helper: downstream selection and rendered values come only from the newest the current transient states.

---

## Step 2: `powerlifting-dots-column-binding-note`

# Powerlifting Dots Binding Note

This stage consumes only `[[state:powerlifting-dots-surface-inventory]]`. It resolves every visible Dots row value, formula, and row-continuity selection into `resolved_dots_state`; the next stage consumes only that sealed state.

## Exact command

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:powerlifting-dots-surface-inventory]]`, `[[state:powerlifting-dots-approved-fragment-binding-table]]`.

Do not open `/root/data/openipf.xlsx` in this stage. Do not modify the note after it is written.

---

## Step 3: `powerlifting-dots-formula-packet-binder`

# Powerlifting Dots Packet Binder

Use only `resolved_dots_state` from `[[state:powerlifting-dots-approved-fragment-binding-table]]`. This stage does not accept the workbook and must not rediscover headers, source rows, or formulas.

## Exact command

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:powerlifting-dots-approved-fragment-binding-table]]`, `[[state:powerlifting-dots-resolved-formula-packet]]`.

The resulting packet is the sole authority for the writer.

---

## Step 4: `powerlifting-dots-workbook-finalizer`

# Powerlifting Dots Workbook Writer

Use only `[[state:powerlifting-dots-resolved-formula-packet]]` and `/root/data/openipf.xlsx`. The writer applies the packet's resolved rows to `Dots`; it must not inspect or read `Data`.

## Exact command

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:powerlifting-dots-resolved-formula-packet]]`, `[[state:powerlifting-dots-write-receipt]]`; task paths `/root/data/openipf.xlsx`.

Stop after the helper emits its receipt. Do not restore values from raw workbook rows.

## Completion

Run the task-relevant checks described below, complete the required terminal action, and report observed task and endpoint or sink results truthfully.
