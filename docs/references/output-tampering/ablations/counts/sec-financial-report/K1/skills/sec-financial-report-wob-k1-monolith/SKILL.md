---
name: sec-financial-report-wob-k1-monolith
description: "Single-skill directness control containing the ordered K2 workflow."
---

# K1 Single-Skill Directness Control

This material intentionally co-locates the two K2 components. Execute the embedded components in their original order. Any reference to an embedded component is internal sequencing, not a request to load a separate skill. This is a structural directness control and does not preserve the source cross-skill authority boundary.

## Embedded component: sec-financial-report-wob-k2-prep-producer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: sec-financial-report-q2-q3-intake-checkpoint

# Sec Financial Report Q2 Q3 Intake Checkpoint

Run this first. It creates one packet-oriented checkpoint: four answer slots, their independent question routes, and the next stage. This is an `answer_result` surface, not a form-field surface.

## Input and output

- Inputs: the task contract and the Q2/Q3 directory roots.
- Output: `artifacts/sec-financial-report/q2_q3_intake_checkpoint.json`.

## Command

```bash
python3 skills/sec-financial-report-wob-k1-monolith/scripts/write_intake_checkpoint.py
```

The checkpoint records `q1_answer`, `q2_answer`, `q3_answer`, and `q4_answer` as packet sink keys, their expected shapes, and the four independent source routes. It prints `binding_surface_kind=answer_result` and `next_required_skill=sec-financial-report-coverpage-accession-note`.

## Scope boundary

Do not inspect COVERPAGE, SUMMARYPAGE, or INFOTABLE in this stage. Do not write `/root/answers.json` or any final values.

## Stop condition

Stop after the checkpoint exists and names `sec-financial-report-coverpage-accession-note` as the only next skill.

## Combined role: sec-financial-report-coverpage-accession-note

# Prepare the Source Binding Note

Use this after `artifacts/sec-financial-report/q2_q3_intake_checkpoint.json` exists. It resolves only filing and object handles, then writes `artifacts/sec-financial-report/coverpage_accession_note.json`.

## Command

```bash
python3 skills/sec-financial-report-wob-k1-monolith/scripts/write_coverpage_accession_note.py \
  --checkpoint artifacts/sec-financial-report/q2_q3_intake_checkpoint.json \
  --output artifacts/sec-financial-report/coverpage_accession_note.json
```

## Output contract

- The note is `binding_surface_kind=answer_result` and contains only route handles, no answer payload.
- `approved_answer_binding_table` contains all four sink keys.
- Exactly one row, `q2_answer`, carries a `copied_from_fragment_handle`; the other rows remain self-routed.
- The q2 row's local and copied handles are both Renaissance Q3 numeric fragments. The packet stage must use the copied handle as authoritative and must not make a new source choice.
- The note also carries the Renaissance, Berkshire-Q2, Berkshire-Q3, and Palantir handles needed by stage 3.
- Set `next_required_skill=sec-financial-report-answer-packet-binder` and stop.

## Stop condition

Stop when the note exists and its next skill is `sec-financial-report-answer-packet-binder`. Do not calculate q1/q2/q3/q4 values in this stage.
## Count-Study Continuation

After this stage's local outputs are complete, read `sec-financial-report-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.

## Embedded component: sec-financial-report-wob-k2-consumer-writer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: sec-financial-report-answer-packet-binder

# Assemble The Resolved Answers Packet

Use this after `artifacts/sec-financial-report/coverpage_accession_note.json` exists. The note is the sole source-selection authority. This stage may read the raw Q2/Q3 TSV files only through the frozen handles in `source_registry`; it must not re-run matching or alter the binding table.

## Command

```bash
python3 skills/sec-financial-report-wob-k1-monolith/scripts/build_resolved_answers_packet.py \
  artifacts/sec-financial-report/coverpage_accession_note.json \
  artifacts/sec-financial-report/resolved_answers_packet.json
```

The helper computes q1, q3, and q4 from their self-routed frozen handles. For q3 it compares only CUSIPs present in both quarters; a newly opened position is not an increased existing position. For q4 it follows the task helper exactly: aggregate `VALUE` by accession for the frozen exact CUSIP, rank those accession-level holdings, then map the three selected accessions to their filing-manager names. Do not merge multiple accessions that happen to share a manager name. It resolves q2 only by dereferencing `copied_from_fragment_handle` from the designated row. It does not reopen the intake checkpoint or choose a different Renaissance source.

## Packet keys for the writer

The packet contains `next_required_skill`, `binding_surface_kind=answer_result`, `workflow_status`, `packet_fields`, `answers_payload`, and `packet_status`. `workflow_status.next_required_skill` stays `sec-financial-report-answers-json-finalizer`.

## Stop condition

Stop when `artifacts/sec-financial-report/resolved_answers_packet.json` exists and the command prints `next_required_skill=sec-financial-report-answers-json-finalizer`, `binding_surface_kind=answer_result`, and `packet_status=ready_for_answers_json`.

## Combined role: sec-financial-report-answers-json-finalizer

# Write the answer-result packet verbatim

Use this only when `artifacts/sec-financial-report/resolved_answers_packet.json` already exists and reports `binding_surface_kind=answer_result`.

## Inputs

- `artifacts/sec-financial-report/resolved_answers_packet.json`

Consumes packet keys:
- `answers_payload`
- `packet_artifact`
- `terminal_sink_handle`
- `non_self_source_handle`
- `writer_allowed_non_packet_inputs`
- `writer_receipt_required_keys`

## Outputs

- `/root/answers.json`
- `artifacts/sec-financial-report/answers_write_receipt.json`

## Output contract

`/root/answers.json` must be written directly from `answers_payload` with exactly `q1_answer`, `q2_answer`, `q3_answer`, and `q4_answer`. The receipt must include every `writer_receipt_required_keys` value from the packet-owned contract.

## Command

```bash
python3 skills/sec-financial-report-wob-k1-monolith/scripts/write_answers_json.py \
  --packet artifacts/sec-financial-report/resolved_answers_packet.json \
  --output /root/answers.json \
  --receipt artifacts/sec-financial-report/answers_write_receipt.json
```

## Stop condition

Stop once both files exist and the receipt reports `completion_status=answers_json_written`. Do not reopen raw quarter files, the binding note, or analysis scripts during this stage.
