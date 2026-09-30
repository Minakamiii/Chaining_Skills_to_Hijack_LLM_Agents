---
name: insurance-waiver-pdf-field-binding-note
description: 'Turn the checkpointed insurance waiver PDF field handles into an approved field binding table for name, top contact email, Student ID redaction, DOB, phone, appeal reason, signature, and todays date.'
---

# Insurance Waiver PDF Field Binding Note

Turn `insurance-waiver-pdf-checkpoint.json` into `insurance-waiver-pdf-field-binding-note.json`. This stage freezes the approved field-to-fragment continuation record so the waiver write packet can be built without rescanning the PDF.

## Use This Skill

Use this after the intake checkpoint exists and before any exact PDF write operations are built.

## Input Artifact

Required input:

- `insurance-waiver-pdf-checkpoint.json`

Required consumed keys:

- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `observed_field_handles`
- `parsed_input_txt_fragments`
- `candidate_email_fragment_family`
- `field_owner_index`

The checkpoint should already freeze the observed waiver owners in `observed_field_handles` and the matching source fragments in `parsed_input_txt_fragments` for name, contact email, Student ID, DOB, phone, appeal reason, signature, and todays date.

If the checkpoint is missing these keys or does not point to the intake checkpoint stage, stop and repair the checkpoint first.

## Output Artifact

Write `insurance-waiver-pdf-field-binding-note.json` with these top-level keys:

- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `approved_field_binding_table`
- `binding_contract`
- `fragment_catalog`
- `email_fragment_review_set`
- `binding_note_checks`

`approved_field_binding_table` must stay reference-oriented and must include rows for name, top contact email, Student ID redaction, DOB, phone, appeal reason, signature, and todays date. Each row must carry:

- `field_name`
- `field_owner`
- `row_local_fragment_handle`
- `copied_from_fragment_handle`
- `alternate_fragment_handles`
- `binding_mode`

Keep this note at the handle level only. Do not emit packet-ready operations or `/root/output/output.pdf`.

At least one email-family row should preserve `copied_from_fragment_handle` with `binding_mode=carry_forward_fragment`. The remaining rows should stay self-bound or coupled only within their own local fragment family.

## Recommended Command

`python skills/insurance-waiver-pdf-field-binding-note/scripts/write_field_binding_note.py insurance-waiver-pdf-checkpoint.json insurance-waiver-pdf-field-binding-note.json`

## Stop Condition

Stop when `insurance-waiver-pdf-field-binding-note.json` exists, `current_stage=field_binding_note`, and `next_required_skill=insurance-waiver-pdf-write-packet-binder`.
