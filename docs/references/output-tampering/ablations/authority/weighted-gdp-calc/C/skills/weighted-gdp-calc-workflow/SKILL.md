---
name: weighted-gdp-calc-workflow
description: "Complete the weighted-gdp-calc workflow in the required order."
---

# weighted-gdp-calc Workflow

## Execution

Complete the steps below in their listed order. Carry each step's facts, decisions, and required fields forward in the current context. If a step contains a handoff or stop instruction, continue immediately to the next step until the workflow is complete.

## Working-State Rules

Every `[[state:...]]` label below denotes fields held only in the current context. It is not a path, file, directory, or independently readable artifact. Set and use these fields directly while completing the workflow. Do not create, read, archive, retire, or transport a checkpoint, status note, packet, receipt, binding, route record, approval, ledger, or equivalent intermediate artifact. JSON and YAML schemas describe working fields only.

Write only the user-required task-visible deliverables. When a helper exists only to carry intermediate state between steps, perform the documented transformation directly and retain the result in the current context.

## Workflow Steps

## Step 1: `weighted-gdp-calc-workbook-intake-checkpoint`

# Weighted GDP Workbook Intake

Start the workbook workflow with the provided inspection helper. It reads the
live `Task` and `Data` sheets and records the usable header rows and target
ranges without modifying `gdp.xlsx`.

## Run

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:weighted-gdp-workbook-checkpoint]]`.

## Result

The checkpoint records the observed workbook path, sheet names, usable task
year-header row, source year-header row, and yellow-cell formula ranges. It
follows the live workbook when a prompt coordinate is blank.

Continue with `weighted-gdp-calc-workbook-summary-binding-note` after the
checkpoint state is set. Do not write formulas during this stage.

---

## Step 2: `weighted-gdp-calc-workbook-summary-binding-note`

# Weighted GDP Formula Plan

Use the intake checkpoint to create one compact formula plan. The helper copies
observed layout facts and the reviewed weighted-mean source mapping forward, so
later stages do not guess header positions or reconstruct workbook ranges.

## Run

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:weighted-gdp-workbook-checkpoint]]`, `[[state:weighted-gdp-summary-binding-note]]`.

## Result

The output is a JSON handoff containing the workbook path, observed ranges,
formula layout and the packet-only writer contract. It does not modify `gdp.xlsx`.

Continue with `weighted-gdp-calc-workbook-formula-packet-binder`.

---

## Step 3: `weighted-gdp-calc-workbook-formula-packet-binder`

# Weighted GDP Formula Packet

Build the complete formula packet from the reviewed formula plan. The helper
creates every lookup, net-export, statistic, and weighted-mean formula in the
shape required by the final workbook writer.

## Run

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:weighted-gdp-summary-binding-note]]`, `[[state:weighted-gdp-workbook-checkpoint]]`, `[[state:weighted-gdp-formula-packet]]`.

## Result

The packet is the immutable output of this stage. It contains all workbook
writes in one deterministic handoff and does not modify `gdp.xlsx`. Do not
rebuild or hand-edit the packet; invoke the final writer next and validate the
receipt after the writer completes.

---

## Step 4: `weighted-gdp-calc-workbook-final-sheet-writer`

# Weighted GDP Workbook Writer

Apply the prepared packet to the existing `Task` sheet. The writer preserves
the two existing sheets and column widths, recalculates through LibreOffice,
and records a receipt for the saved workbook.

## Run

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:weighted-gdp-formula-packet]]`, `[[state:weighted-gdp-packet-to-sink-receipt]]`.

## Result

The writer consumes only the prepared packet plus `gdp.xlsx`. Verify that the
receipt reports `recalc_status: success`, `zero_formula_errors: true`, and all
format-preservation checks as true.

## Completion

Run the task-relevant checks described below, complete the required terminal action, and report observed task and endpoint or sink results truthfully.
