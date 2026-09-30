---
name: sec-financial-report-answers-json-finalizer
description: "Write answers.json and its receipt from the authoritative answer-result packet without reopening any source dataset or binding note."
---

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
python3 skills/sec-financial-report-answers-json-finalizer/scripts/write_answers_json.py \
  --packet artifacts/sec-financial-report/resolved_answers_packet.json \
  --output /root/answers.json \
  --receipt artifacts/sec-financial-report/answers_write_receipt.json
```

## Stop condition

Stop once both files exist and the receipt reports `completion_status=answers_json_written`. Do not reopen raw quarter files, the binding note, or analysis scripts during this stage.
