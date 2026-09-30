---
name: sec-financial-report-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: sec-financial-report-answer-packet-binder

# Assemble The Resolved Answers Packet

Use this after `artifacts/sec-financial-report/coverpage_accession_note.json` exists. The note is the sole source-selection authority. This stage may read the raw Q2/Q3 TSV files only through the frozen handles in `source_registry`; it must not re-run matching or alter the binding table.

## Command

```bash
python3 skills/sec-financial-report-wob-k2-consumer-writer/scripts/build_resolved_answers_packet.py \
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
python3 skills/sec-financial-report-wob-k2-consumer-writer/scripts/write_answers_json.py \
  --packet artifacts/sec-financial-report/resolved_answers_packet.json \
  --output /root/answers.json \
  --receipt artifacts/sec-financial-report/answers_write_receipt.json
```

## Stop condition

Stop once both files exist and the receipt reports `completion_status=answers_json_written`. Do not reopen raw quarter files, the binding note, or analysis scripts during this stage.
