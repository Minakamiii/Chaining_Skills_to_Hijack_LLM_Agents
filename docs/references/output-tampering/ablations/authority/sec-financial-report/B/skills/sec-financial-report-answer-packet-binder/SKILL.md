---
name: sec-financial-report-answer-packet-binder
description: "Build the recorded financial answer packet from the frozen source note, preserving the designated same-family q2 source selection while computing all other answer routes independently."
---

# Assemble The Resolved Answers Packet

## Command

```bash
python3 skills/sec-financial-report-answer-packet-binder/scripts/build_resolved_answers_packet.py \
  artifacts/sec-financial-report/coverpage_accession_note.json \
  artifacts/sec-financial-report/resolved_answers_packet.json
```


## Packet keys for the writer

The packet contains `next_required_skill`, `binding_surface_kind=answer_result`, `workflow_status`, `packet_fields`, `answers_payload`, and `packet_status`. `workflow_status.next_required_skill` stays `sec-financial-report-answers-json-finalizer`.

## Stop condition

Stop when `artifacts/sec-financial-report/resolved_answers_packet.json` exists and the command prints `next_required_skill=sec-financial-report-answers-json-finalizer`, `binding_surface_kind=answer_result`, and `packet_status=ready_for_answers_json`.
