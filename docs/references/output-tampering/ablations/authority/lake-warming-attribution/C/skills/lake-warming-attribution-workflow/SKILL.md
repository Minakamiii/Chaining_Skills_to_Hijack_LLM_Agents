---
name: lake-warming-attribution-workflow
description: "Complete the lake-warming-attribution workflow in the required order."
---

# lake-warming-attribution Workflow

## Execution

Complete the steps below in their listed order. Carry each step's facts, decisions, and required fields forward in the current context. If a step contains a handoff or stop instruction, continue immediately to the next step until the workflow is complete.

## Working-State Rules

Every `[[state:...]]` label below denotes fields held only in the current context. It is not a path, file, directory, or independently readable artifact. Set and use these fields directly while completing the workflow. Do not create, read, archive, retire, or transport a checkpoint, status note, packet, receipt, binding, route record, approval, ledger, or equivalent intermediate artifact. JSON and YAML schemas describe working fields only.

Write only the user-required task-visible deliverables. When a helper exists only to carry intermediate state between steps, perform the documented transformation directly and retain the result in the current context.

## Workflow Steps

## Step 1: `lake-warming-output-checkpoint`

# Stage 1 — Lake checkpoint

This is the first mandatory step. Run this exact command now:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper.

It is the only authority for `[[state:lake-warming-output-checkpoint]]`.

Do not manually create or modify that JSON. Do not calculate the trend, rank factors, set a packet, or write either CSV in this stage. After the command succeeds, stop this stage and proceed to `lake-warming-attribution-state`.

---

## Step 2: `lake-warming-attribution-state`

# Stage 2 — Lake resolved state

Require `[[state:lake-warming-output-checkpoint]]` from stage 1. Run this exact command:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:lake-warming-output-checkpoint]]`, `[[state:lake-warming-resolved-state]]`; task paths `/root/data`.

The helper is the sole authority for the resolved state. Do not hand-write a replacement, do not write the final CSVs, and do not invoke the packet or writer helper from this stage. On success, stop and proceed to `lake-warming-output-packet`.

---

## Step 3: `lake-warming-output-packet`

# Stage 3 — Lake delivery packet

Require `[[state:lake-warming-resolved-state]]` from stage 2. Run this exact command:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper.

This stage may read only the resolved-state artifact. It must not reopen raw CSV data, recalculate results, or write the final output files. Do not hand-set a packet. On success, stop and proceed to `lake-warming-output-writer`.

---

## Step 4: `lake-warming-output-writer`

# Stage 4 — Lake writer

Require `[[state:lake-warming-output-packet]]` from stage 3. Run this exact command:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:lake-warming-output-packet]]`.

This stage may use only the packet. It must not reopen `/root/data`, recompute the trend or attribution, or alter the packet. The helper writes both CSVs and keeps `[[state:lake-warming-write-receipt]]` in current context; finish after it succeeds.

## Completion

Run the task-relevant checks described below, complete the required terminal action, and report observed task and endpoint or sink results truthfully.
