---
name: edit-pdf-wob-k3-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: insurance-waiver-pdf-intake-checkpoint

# Insurance Waiver PDF Intake Checkpoint

## When to Use
Use this first for the insurance waiver PDF task. It compares `/root/input/input.pdf` with `/root/input/input.txt`, records the observed waiver surface, and freezes the only approved edit scope before any redaction, replacement, signature, or date insertion.

## Inputs
- `/root/input/input.pdf`
- `/root/input/input.txt`

## Recommended Command
```bash
python skills/edit-pdf-wob-k3-prep-producer/scripts/build_checkpoint.py /root/input/input.pdf /root/input/input.txt insurance-waiver-pdf-checkpoint.json
```

## Output Contract
Write `insurance-waiver-pdf-checkpoint.json` with:
- `current_stage=intake_checkpoint`
- `next_required_skill=insurance-waiver-pdf-field-binding-note`
- `allowed_outputs=['insurance-waiver-pdf-checkpoint.json']`
- `observed_field_handles`
- `parsed_input_txt_fragments`
- `candidate_email_fragment_family`
- `field_owner_index`
- `checkpoint_checks`

`observed_field_handles` must come from the real PDF surface and cover the observed top contact email field owner, the other field owners, the appeal-reason lines, the signature slot, and the date slot.
`parsed_input_txt_fragments` should keep task text as fragment handles and donor-family groups, not write-ready edits.

## Scope
- Inventory the observed sink surface from the real PDF first, including field owners, line-local rectangles, appeal-reason box lines, signature slot, and date slot.
- Parse `input.txt` into fragment handles and the small email fragment family needed for later field matching.
- Leave exact PDF write operations, redaction rectangles, and `/root/output/output.pdf` to later stages.

## Stop Condition
Stop once `insurance-waiver-pdf-checkpoint.json` is present, `checkpoint_checks.status` is `ok`, and `insurance-waiver-pdf-field-binding-note` is the only next required skill.

## Combined role: insurance-waiver-pdf-field-binding-note

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

`python skills/edit-pdf-wob-k3-prep-producer/scripts/write_field_binding_note.py insurance-waiver-pdf-checkpoint.json insurance-waiver-pdf-field-binding-note.json`

## Stop Condition

Stop when `insurance-waiver-pdf-field-binding-note.json` exists, `current_stage=field_binding_note`, and `next_required_skill=insurance-waiver-pdf-write-packet-binder`.
## Count-Study Continuation

After this stage's local outputs are complete, read `insurance-waiver-pdf-write-packet-binder` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
