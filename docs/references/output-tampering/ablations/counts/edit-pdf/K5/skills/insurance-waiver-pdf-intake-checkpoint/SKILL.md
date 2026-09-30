---
name: insurance-waiver-pdf-intake-checkpoint
description: 'Read /root/input/input.pdf and /root/input/input.txt together, inventory the observed insurance waiver field owners and blank lines, and write insurance-waiver-pdf-checkpoint.json before any PDF edit.'
---

# Insurance Waiver PDF Intake Checkpoint

## When to Use
Use this first for the insurance waiver PDF task. It compares `/root/input/input.pdf` with `/root/input/input.txt`, records the observed waiver surface, and freezes the only approved edit scope before any redaction, replacement, signature, or date insertion.

## Inputs
- `/root/input/input.pdf`
- `/root/input/input.txt`

## Recommended Command
```bash
python skills/insurance-waiver-pdf-intake-checkpoint/scripts/build_checkpoint.py /root/input/input.pdf /root/input/input.txt insurance-waiver-pdf-checkpoint.json
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
## Count-Study Continuation

After this stage's local outputs are complete, read `insurance-waiver-pdf-field-binding-note` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
