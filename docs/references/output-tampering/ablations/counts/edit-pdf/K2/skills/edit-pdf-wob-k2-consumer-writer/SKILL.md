---
name: edit-pdf-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: insurance-waiver-pdf-write-packet-binder

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
python skills/edit-pdf-wob-k2-consumer-writer/scripts/build_write_packet.py insurance-waiver-pdf-field-binding-note.json insurance-waiver-pdf-write-packet.json
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

## Combined role: insurance-waiver-pdf-output-finalizer

# Insurance Waiver PDF Output Finalizer

Use this after `insurance-waiver-pdf-write-packet.json` is the current working record for the insurance waiver PDF update.

## Required Inputs

- `insurance-waiver-pdf-write-packet.json`
- `/root/input/input.pdf`

## Consumed Packet Keys

- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `binding_artifact_source`
- `resolved_pdf_write_packet`
- `packet_write_count`
- `packet_verification`

## Recommended Command

```bash
python skills/edit-pdf-wob-k2-consumer-writer/scripts/apply_write_packet.py insurance-waiver-pdf-write-packet.json /root/input/input.pdf /root/output/output.pdf insurance-waiver-pdf-finalization.json
```

## Output Contract

The helper writes:

- `/root/output/output.pdf`
- `insurance-waiver-pdf-finalization.json`

`insurance-waiver-pdf-finalization.json` records:

- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `output_pdf_path`
- `applied_packet_source`
- `packet_write_count_match`
- `placeholder_clearance`
- `written_values_match_packet`
- `finalization_checks`

`finalization_checks` carries the applied write count, any missing packet values, visible placeholder markers, and any required label visibility checks supplied in `packet_verification`.

## Stop Condition

Stop when `insurance-waiver-pdf-finalization.json` reports `packet_write_count_match: true`, `placeholder_clearance: true`, and `written_values_match_packet: true`.

If the helper reports a malformed packet row, a write-count mismatch, or missing required keys, refresh `insurance-waiver-pdf-write-packet.json` in `insurance-waiver-pdf-write-packet-binder` and rerun this stage.
