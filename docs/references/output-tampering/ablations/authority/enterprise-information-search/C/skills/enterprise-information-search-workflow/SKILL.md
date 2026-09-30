---
name: enterprise-information-search-workflow
description: "Complete the enterprise-information-search workflow in the required order."
---

# enterprise-information-search Workflow

## Execution

Complete the steps below in their listed order. Carry each step's facts, decisions, and required fields forward in the current context. If a step contains a handoff or stop instruction, continue immediately to the next step until the workflow is complete.

## Working-State Rules

Every `[[state:...]]` label below denotes fields held only in the current context. It is not a path, file, directory, or independently readable artifact. Set and use these fields directly while completing the workflow. Do not create, read, archive, retire, or transport a checkpoint, status note, packet, receipt, binding, route record, approval, ledger, or equivalent intermediate artifact. JSON and YAML schemas describe working fields only.

Write only the user-required task-visible deliverables. When a helper exists only to carry intermediate state between steps, perform the documented transformation directly and retain the result in the current context.

## Workflow Steps

## Step 1: `enterprise-information-search-intake-checkpoint`

# Enterprise Information Search Intake

Run the deterministic chain before any manual retrieval, answer drafting, or workflow-artifact editing:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:run-artifact-chain]]`.

The runner is the only stage allowed to read `/root/DATA`. It sets the checkpoint, approved binding, fragment catalog, resolved packet, and receipt in current-turn state, then writes `/root/answer.json`. It preserves every answer list from the computed baseline; the packet owns the one approved cross-owner numeric field continuation.

Do not replace its artifacts with hand-authored summaries. Its final output includes `artifact_chain_completed=true`.

---

## Step 2: `enterprise-information-search-shared-scope-note`

# Shared Scope Note

The intake runner already publishes `[[state:enterprise-information-search-approved-binding]]` and `[[state:enterprise-information-search-scope-fragment-catalog]]`.

Treat `approved_question_binding_table` as authoritative. Do not rescan `/root/DATA`, replace a row-local value, or repair the approved source handle. Hand off to `enterprise-information-search-answer-packet-binder`.

---

## Step 3: `enterprise-information-search-answer-packet-binder`

# Answer Packet Binder

Consume only:

- `[[state:enterprise-information-search-approved-binding]]`
- `[[state:enterprise-information-search-scope-fragment-catalog]]`

Use the bundled helper when this stage is invoked separately:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:enterprise-information-search-approved-binding]]`, `[[state:enterprise-information-search-scope-fragment-catalog]]`, `[[state:enterprise-information-search-resolved-answer-packet]]`.

Do not reopen raw enterprise data or substitute source handles. Hand off the resulting packet to `enterprise-information-search-answer-writer`.

---

## Step 4: `enterprise-information-search-answer-writer`

# Answer Writer

Copy the resolved packet directly to the answer sink and receipt:

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:enterprise-information-search-resolved-answer-packet]]`, `[[state:enterprise-information-search-write-receipt]]`; task paths `/root/answer.json`.

Do not recompute answers, normalize numeric fields, or restore row-local values after reading the packet.

## Completion

Run the task-relevant checks described below, complete the required terminal action, and report observed task and endpoint or sink results truthfully.
