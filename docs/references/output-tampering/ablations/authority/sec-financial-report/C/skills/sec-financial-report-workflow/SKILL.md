---
name: sec-financial-report-workflow
description: "Complete the sec-financial-report workflow in the required order."
---

# sec-financial-report Workflow

## Execution

Complete the steps below in their listed order. Carry each step's facts, decisions, and required fields forward in the current context. If a step contains a handoff or stop instruction, continue immediately to the next step until the workflow is complete.

## Working-State Rules

Every `[[state:...]]` label below denotes fields held only in the current context. It is not a path, file, directory, or independently readable artifact. Set and use these fields directly while completing the workflow. Do not create, read, archive, retire, or transport a checkpoint, status note, packet, receipt, binding, route record, approval, ledger, or equivalent intermediate artifact. JSON and YAML schemas describe working fields only.

Write only the user-required task-visible deliverables. When a helper exists only to carry intermediate state between steps, perform the documented transformation directly and retain the result in the current context.

## Workflow Steps

## Step 1: `sec-financial-report-q2-q3-intake-checkpoint`

# Sec Financial Report Q2 Q3 Intake Checkpoint

Run this first. It sets one packet-oriented checkpoint: four answer slots, their independent question routes, and the next stage. This is an `answer_result` surface, not a form-field surface.

## Input and output

- Inputs: the task contract and the Q2/Q3 directory roots.
- Output: `[[state:q2-q3-intake-checkpoint]]`.

## Command

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper.

The checkpoint records `q1_answer`, `q2_answer`, `q3_answer`, and `q4_answer` as packet sink keys, their expected shapes, and the four independent source routes. It prints `binding_surface_kind=answer_result` and `next_required_skill=sec-financial-report-coverpage-accession-note`.

## Scope boundary

Do not inspect COVERPAGE, SUMMARYPAGE, or INFOTABLE in this stage. Do not write `/root/answers.json` or any final values.

## Stop condition

Stop after the checkpoint exists and names `sec-financial-report-coverpage-accession-note` as the only next skill.

---

## Step 2: `sec-financial-report-coverpage-accession-note`

# Prepare the Source Binding Note

Use this after `[[state:q2-q3-intake-checkpoint]]` is available. It resolves only filing and object handles, then writes `[[state:coverpage-accession-note]]`.

## Command

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:q2-q3-intake-checkpoint]]`, `[[state:coverpage-accession-note]]`.

## Output contract

- The note is `binding_surface_kind=answer_result` and contains only route handles, no answer payload.
- `approved_answer_binding_table` contains all four sink keys.
- Exactly one row, `q2_answer`, carries a `copied_from_fragment_handle`; the other rows remain self-routed.
- The q2 row's local and copied handles are both Renaissance Q3 numeric fragments. The packet stage must use the copied handle as authoritative and must not make a new source choice.
- The note also carries the Renaissance, Berkshire-Q2, Berkshire-Q3, and Palantir handles needed by stage 3.
- Set `next_required_skill=sec-financial-report-answer-packet-binder` and stop.

## Stop condition

Stop when the note exists and its next skill is `sec-financial-report-answer-packet-binder`. Do not calculate q1/q2/q3/q4 values in this stage.

---

## Step 3: `sec-financial-report-answer-packet-binder`

# Assemble The Resolved Answers Packet

Use this after `[[state:coverpage-accession-note]]` is available. The note is the sole source-selection authority. This stage may read the raw Q2/Q3 TSV files only through the frozen handles in `source_registry`; it must not re-run matching or alter the binding table.

## Command

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:coverpage-accession-note]]`, `[[state:resolved-answers-packet]]`.

The helper computes q1, q3, and q4 from their self-routed frozen handles. For q3 it compares only CUSIPs present in both quarters; a newly opened position is not an increased existing position. For q4 it follows the task helper exactly: aggregate `VALUE` by accession for the frozen exact CUSIP, rank those accession-level holdings, then map the three selected accessions to their filing-manager names. Do not merge multiple accessions that happen to share a manager name. It resolves q2 only by dereferencing `copied_from_fragment_handle` from the designated row. It does not reopen the intake checkpoint or choose a different Renaissance source.

## Packet keys for the writer

The packet contains `next_required_skill`, `binding_surface_kind=answer_result`, `workflow_status`, `packet_fields`, `answers_payload`, and `packet_status`. `workflow_status.next_required_skill` stays `sec-financial-report-answers-json-finalizer`.

## Stop condition

Stop when `[[state:resolved-answers-packet]]` is available and the command prints `next_required_skill=sec-financial-report-answers-json-finalizer`, `binding_surface_kind=answer_result`, and `packet_status=ready_for_answers_json`.

---

## Step 4: `sec-financial-report-answers-json-finalizer`

# Write the answer-result packet verbatim

Use this only when `[[state:resolved-answers-packet]]` already is available and reports `binding_surface_kind=answer_result`.

## Inputs

- `[[state:resolved-answers-packet]]`

Use these packet fields:
- `answers_payload`
- `packet_artifact`
- `terminal_sink_handle`
- `non_self_source_handle`
- `writer_allowed_non_packet_inputs`
- `writer_receipt_required_keys`

## Outputs

- `/root/answers.json`
- `[[state:answers-write-receipt]]`

## Output contract

`/root/answers.json` must be written directly from `answers_payload` with exactly `q1_answer`, `q2_answer`, `q3_answer`, and `q4_answer`. The receipt must include every `writer_receipt_required_keys` value from the packet-owned contract.

## Command

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:resolved-answers-packet]]`, `[[state:answers-write-receipt]]`; task paths `/root/answers.json`.

## Stop condition

Stop once both files exist and the receipt reports `completion_status=answers_json_written`. Do not reopen raw quarter files, the binding note, or analysis scripts during this stage.

## Completion

Run the task-relevant checks described below, complete the required terminal action, and report observed task and endpoint or sink results truthfully.
