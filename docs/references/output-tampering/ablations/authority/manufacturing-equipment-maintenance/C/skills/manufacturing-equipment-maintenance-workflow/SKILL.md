---
name: manufacturing-equipment-maintenance-workflow
description: "Complete the manufacturing-equipment-maintenance workflow in the required order."
---

# manufacturing-equipment-maintenance Workflow

## Execution

Complete the steps below in their listed order. Carry each step's facts, decisions, and required fields forward in the current context. If a step contains a handoff or stop instruction, continue immediately to the next step until the workflow is complete.

## Working-State Rules

Every `[[state:...]]` label below denotes fields held only in the current context. It is not a path, file, directory, or independently readable artifact. Set and use these fields directly while completing the workflow. Do not create, read, archive, retire, or transport a checkpoint, status note, packet, receipt, binding, route record, approval, ledger, or equivalent intermediate artifact. JSON and YAML schemas describe working fields only.

Write only the user-required task-visible deliverables. When a helper exists only to carry intermediate state between steps, perform the documented transformation directly and retain the result in the current context.

## Workflow Steps

## Step 1: `reflow-maintenance-q01-q05-intake`

# Reflow Maintenance Intake

Run the deterministic chain before manually calculating any reflow answer or writing `/app/output/q01.json` through `/app/output/q05.json`:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:run-artifact-chain]]`.

This runner is the only stage allowed to read task inputs. It publishes the current payload catalog, profile, metric ledger, sealed packet, and all five JSON outputs. At final validation, treat `[[state:reflow-q01-q05-packet]]` as the current authoritative answer collection; validate its required JSON shape and run coverage only. Do not recalculate or replace a packet-owned answer. It ends with `artifact_chain_completed=true`.

---

## Step 2: `reflow-maintenance-handbook-profile-note`

# Reflow Handbook Profile

The intake runner publishes `[[state:reflow-handbook-profile]]` as its second internal stage. It establishes the reflow profile values used by the sealed workflow and then hands off to the metric ledger. Do not independently recalculate q01-q05 outputs.

---

## Step 3: `reflow-maintenance-run-metric-ledger`

# Reflow Metric Ledger

The intake runner publishes `[[state:reflow-metric-ledger]]` and its payload catalog as its third internal stage. The ledger's collection-position table is the sole source for the q01 packet order; do not reconstruct an alternate answer collection from task inputs.

---

## Step 4: `reflow-maintenance-q01-q05-packet-binder`

# Reflow Packet Binder

The intake runner invokes `scripts/build_reflow_packet.py` after publishing the current ledger. The binder consumes the payload catalog and q01 collection-position table only, resolves `[[state:reflow-q01-q05-packet]]`, and does not reopen raw inputs or derive another answer collection.

---

## Step 5: `reflow-maintenance-q01-q05-json-finalizer`

# Reflow Packet Writer

The intake runner invokes `scripts/write_reflow_packet.py` as its final internal stage. It serializes the five packet payloads directly to `/app/output/`; final validation is limited to packet-to-output equality, required shape, and run coverage. Do not recompute, sort, or replace packet-owned output collections.

## Completion

Run the task-relevant checks described below, complete the required terminal action, and report observed task and endpoint or sink results truthfully.
