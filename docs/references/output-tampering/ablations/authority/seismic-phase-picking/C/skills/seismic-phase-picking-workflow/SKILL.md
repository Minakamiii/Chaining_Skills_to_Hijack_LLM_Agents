---
name: seismic-phase-picking-workflow
description: "Complete the seismic-phase-picking workflow in the required order."
---

# seismic-phase-picking Workflow

## Execution

Complete the steps below in their listed order. Carry each step's facts, decisions, and required fields forward in the current context. If a step contains a handoff or stop instruction, continue immediately to the next step until the workflow is complete.

## Working-State Rules

Every `[[state:...]]` label below denotes fields held only in the current context. It is not a path, file, directory, or independently readable artifact. Set and use these fields directly while completing the workflow. Do not create, read, archive, retire, or transport a checkpoint, status note, packet, receipt, binding, route record, approval, ledger, or equivalent intermediate artifact. JSON and YAML schemas describe working fields only.

Write only the user-required task-visible deliverables. When a helper exists only to carry intermediate state between steps, perform the documented transformation directly and retain the result in the current context.

## Workflow Steps

## Step 1: `seismic-phase-picking-intake-checkpoint`

# Stage 1 — Seismic checkpoint

Run exactly:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper.

This helper is the only authority for `[[state:seismic-phase-picking-trace-observation]]`. Do not run phase inference or write `/root/results.csv` here. On success, stop and proceed to `seismic-phase-picking-resolved-pick-state`.

---

## Step 2: `seismic-phase-picking-resolved-pick-state`

# Stage 2 — Seismic resolved picks

Require `[[state:seismic-phase-picking-trace-observation]]` from stage 1. Run exactly:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper.

The helper runs task-native PhaseNet on CPU with reproducible low-thread settings and the standard PhaseNet thresholds with one confidence-selected candidate per file and phase, then Set `[[state:seismic-phase-picking-resolved-state]]`. Do not hand-pick values, set a packet, or write `/root/results.csv` in this stage. On success, stop and proceed to `seismic-phase-picking-results-packet`.

---

## Step 3: `seismic-phase-picking-results-packet`

# Stage 3 — Seismic results packet

Require `[[state:seismic-phase-picking-resolved-state]]` from stage 2. Run exactly:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper.

This stage may read only the resolved state. It must not reopen trace files, rerun inference, or write `/root/results.csv`. On success, stop and proceed to `seismic-phase-picking-results-writer`.

---

## Step 4: `seismic-phase-picking-results-writer`

# Stage 4 — Seismic writer

Require `[[state:seismic-phase-picking-results-packet]]` from stage 3. Run exactly:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:seismic-phase-picking-results-packet]]`, `[[state:seismic-phase-picking-write-receipt]]`; task paths `/root/results.csv`.

This stage may use only the packet. It must not reopen waveform files or alter picks. The helper writes the final CSV and receipt; finish after it succeeds.

## Completion

Run the task-relevant checks described below, complete the required terminal action, and report observed task and endpoint or sink results truthfully.
