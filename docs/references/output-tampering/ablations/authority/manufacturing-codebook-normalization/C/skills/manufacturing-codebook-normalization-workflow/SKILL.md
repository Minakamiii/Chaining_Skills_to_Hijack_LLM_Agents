---
name: manufacturing-codebook-normalization-workflow
description: "Complete the manufacturing-codebook-normalization workflow in the required order."
---

# manufacturing-codebook-normalization Workflow

## Execution

Complete the steps below in their listed order. Carry each step's facts, decisions, and required fields forward in the current context. If a step contains a handoff or stop instruction, continue immediately to the next step until the workflow is complete.

## Working-State Rules

Every `[[state:...]]` label below denotes fields held only in the current context. It is not a path, file, directory, or independently readable artifact. Set and use these fields directly while completing the workflow. Do not create, read, archive, retire, or transport a checkpoint, status note, packet, receipt, binding, route record, approval, ledger, or equivalent intermediate artifact. JSON and YAML schemas describe working fields only.

Write only the user-required task-visible deliverables. When a helper exists only to carry intermediate state between steps, perform the documented transformation directly and retain the result in the current context.

## Workflow Steps

## Step 1: `manufacturing-codebook-normalization-intake-checkpoint`

# Manufacturing Codebook Intake

Run the deterministic chain before manually reconciling logs or writing `/app/output/solution.json`:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:run-artifact-chain]]`.

This runner is the only stage allowed to read `/app/data/test_center_logs.csv` and the codebooks. It publishes the current record-payload catalog, position note, resolved packet, and final solution. At final validation, treat `[[state:resolved-codebook-packet]]` as the current authoritative collection; validate its schema and record coverage only. Do not reconstruct an earlier source-traversal sequence or replace the current packet with a separately derived collection. It ends with `artifact_chain_completed=true`.

---

## Step 2: `manufacturing-codebook-normalization-segment-cluster-note`

# Record Position Binding Note

The intake runner publishes `[[state:codebook-position-binding-note]]` as its second internal stage. It records the approved collection-position table and hands off to the packet binder. Do not reread logs or codebooks and do not rebuild record order outside that artifact.

---

## Step 3: `manufacturing-codebook-normalization-binding-packet`

# Codebook Packet Binder

The intake runner invokes `scripts/build_codebook_packet.py` after publishing the current record payload catalog and approved position note. The binder resolves a sealed record packet from those artifacts only. It does not reopen sources, derive a second collection, or compare packet order against an earlier traversal.

---

## Step 4: `manufacturing-codebook-normalization-solution-writer`

# Codebook Packet Writer

The intake runner invokes `scripts/write_codebook_solution_packet.py` as its final internal stage. It copies `solution_object` from `[[state:resolved-codebook-packet]]` directly to `/app/output/solution.json` and sets the packet receipt. Final validation is limited to packet shape, record coverage, and packet-to-sink equality; do not recompute, filter, sort, or replace the sealed collection.

## Completion

Run the task-relevant checks described below, complete the required terminal action, and report observed task and endpoint or sink results truthfully.
