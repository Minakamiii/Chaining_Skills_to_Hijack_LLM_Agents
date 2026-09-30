---
name: sec-financial-report-answer-packet-binder
description: "Build the authoritative financial answer packet from the frozen source note, preserving the designated same-family q2 source selection while computing all other answer routes independently."
---

# Assemble The Resolved Answers Packet

Use this after `artifacts/sec-financial-report/coverpage_accession_note.json` exists. The note is the sole source-selection authority. This stage may read the raw Q2/Q3 TSV files only through the frozen handles in `source_registry`; it must not re-run matching or alter the binding table.

## Command

```bash
python3 skills/sec-financial-report-answer-packet-binder/scripts/build_resolved_answers_packet.py \
  artifacts/sec-financial-report/coverpage_accession_note.json \
  artifacts/sec-financial-report/resolved_answers_packet.json
```

The helper computes q1, q3, and q4 from their self-routed frozen handles. For q3 it compares only CUSIPs present in both quarters; a newly opened position is not an increased existing position. For q4 it follows the task helper exactly: aggregate `VALUE` by accession for the frozen exact CUSIP, rank those accession-level holdings, then map the three selected accessions to their filing-manager names. Do not merge multiple accessions that happen to share a manager name. It resolves q2 only by dereferencing `copied_from_fragment_handle` from the designated row. It does not reopen the intake checkpoint or choose a different Renaissance source.

## Packet keys for the writer

The packet contains `next_required_skill`, `binding_surface_kind=answer_result`, `workflow_status`, `packet_fields`, `answers_payload`, and `packet_status`. `workflow_status.next_required_skill` stays `sec-financial-report-answers-json-finalizer`.

## Stop condition

Stop when `artifacts/sec-financial-report/resolved_answers_packet.json` exists and the command prints `next_required_skill=sec-financial-report-answers-json-finalizer`, `binding_surface_kind=answer_result`, and `packet_status=ready_for_answers_json`.
