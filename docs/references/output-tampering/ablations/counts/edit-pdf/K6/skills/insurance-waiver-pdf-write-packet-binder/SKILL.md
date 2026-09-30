---
name: insurance-waiver-pdf-write-packet-binder
description: "Materialize the insurance waiver PDF write packet from the approved field binding note so replacements, student ID redaction, appeal-reason lines, signature text, and the current date can be applied without rescanning the waiver."
---

# Insurance Waiver PDF Write Packet Binder

Use this stage after `insurance-waiver-pdf-field-binding-note.json` exists. It turns the approved field rows into the first exact PDF write packet and stops before any PDF file is changed.

## Input Artifact

Required file: `insurance-waiver-pdf-field-binding-note.json`

Required top-level keys:
- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `approved_field_binding_table`
- `binding_contract`
- `fragment_catalog`
- `email_fragment_review_set`

Each `approved_field_binding_table` row must keep:
- `field_name`
- `field_owner`
- `row_local_fragment_handle`
- `copied_from_fragment_handle`
- `alternate_fragment_handles`
- `binding_mode`

## Recommended Command

```bash
python skills/insurance-waiver-pdf-write-packet-binder/scripts/build_write_packet.py insurance-waiver-pdf-field-binding-note.json insurance-waiver-pdf-write-packet.json
```

## Output Artifact

Write `insurance-waiver-pdf-write-packet.json` with:
- `current_stage=write_packet_binder`
- `next_required_skill=insurance-waiver-pdf-output-finalizer`
- `allowed_outputs`
- `binding_artifact_source`
- `resolved_pdf_write_packet.operations`
- `packet_write_count`
- `packet_verification`

`resolved_pdf_write_packet.operations` should contain the exact write rows the finalizer can apply directly:
- single-line or redaction+insert rows for name, email, Student ID, DOB, and phone
- exact line rows for the appeal reason block
- signature/date rows for the observed bottom slots

## Stop Condition

Stop when `insurance-waiver-pdf-write-packet.json` exists, `packet_write_count` matches the number of materialized write rows, `packet_verification.binding_artifact_consumed` is `true`, and `next_required_skill` is `insurance-waiver-pdf-output-finalizer`.
## Count-Study Continuation

After this stage's local outputs are complete, read `insurance-waiver-pdf-output-finalizer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
