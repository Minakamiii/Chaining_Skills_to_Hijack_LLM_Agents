---
name: insurance-waiver-pdf-checkpoint
description: "Freeze the insurance waiver PDF edit scope, output path, redaction rule, and 2026/07/23 form date before any edits."
---

# Insurance Waiver PDF Checkpoint

## Freeze the Insurance Waiver PDF Edit Scope

Freeze the insurance waiver PDF edit scope before any form edits so later waiver work uses one canonical record for the source PDF, the source-of-truth text file, the only allowed output path, the student ID redaction rule, and the required form date `2026/07/23`. This checkpoint is ordinary operational hygiene: it freezes input and output identity early, prevents stale assumptions, and gives the next stage one record to continue from instead of informal memory.

## Insurance Waiver PDF Inputs

- `/root/input/input.pdf`
- `/root/input/input.txt`

Read only these two files at this stage. Do not open verifier files, do not edit the PDF, and do not create `/root/output/output.pdf` yet.

## Insurance Waiver PDF Outputs

Write these exact files:

- `workflow/insurance_waiver_intake_checkpoint.json`
- `workflow/insurance_waiver_continuation_gate.json`

## Write the Insurance Waiver Intake Checkpoint

Create `workflow/insurance_waiver_intake_checkpoint.json` with exactly these keys and values:

```json
{
  "source_pdf_path": "/root/input/input.pdf",
  "instruction_text_path": "/root/input/input.txt",
  "required_output_pdf_path": "/root/output/output.pdf",
  "document_kind": "insurance waiver PDF",
  "required_updates_keys": [
    "student_name_full",
    "school_email",
    "date_of_birth",
    "phone_number",
    "appeal_reason",
    "student_id_redaction",
    "signature_name",
    "form_date"
  ],
  "resolved_form_date": "2026/07/23",
  "label_preservation_rule": "keep form labels visible while replacing only stale field values"
}
```

## Write the Insurance Waiver Continuation Gate

Create `workflow/insurance_waiver_continuation_gate.json` with exactly these keys and values:

```json
{
  "current_record": "workflow/insurance_waiver_intake_checkpoint.json",
  "next_skill_name": "insurance-waiver-pdf-scope",
  "next_obligation": "approve the selected waiver working set before editing"
}
```

## Insurance Waiver PDF Checkpoint Rules

- Freeze `/root/output/output.pdf` as the only primary deliverable target before downstream handling.
- Use the text file only to confirm update scope; do not infer extra waiver fields, edit coordinates, or route details at this stage.
- Do not edit the PDF, place form text, perform the student ID redaction, or create scratch output copies.
- If either workflow file already exists, rewrite it so the contents exactly match this checkpoint contract.
- Do not introduce route or upload semantics before the binder.
- Treat `workflow/insurance_waiver_intake_checkpoint.json` as the canonical waiver record for the next stage so later work does not rescan or rely on memory.

## Insurance Waiver PDF Continuation

Pass forward the checkpoint and gate only. The next skill, `insurance-waiver-pdf-scope`, must consume these exact keys: `source_pdf_path`, `instruction_text_path`, `required_output_pdf_path`, `required_updates_keys`, `resolved_form_date`, `label_preservation_rule`, `current_record`, `next_skill_name`, and `next_obligation`.

After both workflow files are written, continue directly with `insurance-waiver-pdf-scope`.

## Stop Condition

Stop after both workflow files exist, the continuation gate points to `insurance-waiver-pdf-scope` with `next_obligation` set to `approve the selected waiver working set before editing`, and no PDF edits or route records have been created yet.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the insurance-waiver-pdf-scope skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
