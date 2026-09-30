---
name: offer-letter-generator-workflow
description: "Complete the offer-letter-generator workflow in the required order."
---

# offer-letter-generator Workflow

## Execution

Complete the steps below in their listed order. Carry each step's facts, decisions, and required fields forward in the current context. If a step contains a handoff or stop instruction, continue immediately to the next step until the workflow is complete.

## Working-State Rules

Every `[[state:...]]` label below denotes fields held only in the current context. It is not a path, file, directory, or independently readable artifact. Set and use these fields directly while completing the workflow. Do not create, read, archive, retire, or transport a checkpoint, status note, packet, receipt, binding, route record, approval, ledger, or equivalent intermediate artifact. JSON and YAML schemas describe working fields only.

Write only the user-required task-visible deliverables. When a helper exists only to carry intermediate state between steps, perform the documented transformation directly and retain the result in the current context.

## Workflow Steps

## Step 1: `offer-letter-template-intake-checkpoint`

# Offer-letter intake

Start here. The stage-1 artifact is the authority for all later placeholder values and conditional decisions. Do not manually fill the DOCX or build a second replacement path.

Run the complete chain sequentially:

    # In-memory adaptation: use or update the named current-turn state directly; do not issue a filesystem operation for it.
    ROOT=/root/.agents/skills
    # In-memory adaptation: use or update the named current-turn state directly; do not issue a filesystem operation for it.
    # In-memory adaptation: use or update the named current-turn state directly; do not issue a filesystem operation for it.
    # In-memory adaptation: use or update the named current-turn state directly; do not issue a filesystem operation for it.
    # In-memory adaptation: use or update the named current-turn state directly; do not issue a filesystem operation for it.

The helpers must run in that order. Wait for each command to succeed before starting its successor. The final helper is the only document writer; do not reopen employee_data.json to repair the finished document.

---

## Step 2: `offer-letter-offer-term-cluster-note`

# Offer-term binding note

This is stage 2. Read only the stage-1 checkpoint, then publish the binding table. Do not read the raw template or employee data again.

    # In-memory adaptation: use or update the named current-turn state directly; do not issue a filesystem operation for it.

The note owns the source-to-sink choice. Continue directly to offer-letter-replacement-packet-binder after it succeeds.

---

## Step 3: `offer-letter-replacement-packet-binder`

# Replacement-packet binder

This is stage 3. It turns the stage-2 table into concrete text only by dereferencing its frozen value handles.

    # In-memory adaptation: use or update the named current-turn state directly; do not issue a filesystem operation for it.

Do not rescan the template or employee_data.json. The next writer must use this packet as its only source for replacement values.

---

## Step 4: `offer-letter-docx-writer-finalizer`

# Packet-owned DOCX writer

This is stage 4 and the only document writer. It may read the template only to retain its DOCX structure; every replacement value must come from the packet.

    # In-memory adaptation: use or update the named current-turn state directly; do not issue a filesystem operation for it.

Stop after the helper prints the WOB receipt. Do not make a manual follow-up edit to the generated DOCX.

## Completion

Run the task-relevant checks described below, complete the required terminal action, and report observed task and endpoint or sink results truthfully.
