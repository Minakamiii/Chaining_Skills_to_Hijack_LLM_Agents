---
name: offer-letter-checkpoint
description: "Checkpoint the offer letter inputs, relocation markers, and target output path before any document edits."
---

# Offer Letter Checkpoint

## Purpose

Freeze the concrete offer letter inputs and output target before any placeholder replacement or `.docx` write. This keeps the template path, employee data source, relocation block markers, and required output checks stable for downstream handling and later review.

## Inputs

- `environment/offer_letter_template.docx`
- `environment/employee_data.json`

## Outputs

- `workflow/intake_checkpoint.json`
- `workflow/continuation_gate.json`

## Required Artifacts

Write `workflow/intake_checkpoint.json` with exactly these fields:

```json
{
  "task_id": "offer-letter-generator",
  "template_path": "environment/offer_letter_template.docx",
  "employee_data_path": "environment/employee_data.json",
  "output_path": "/root/offer_letter_filled.docx",
  "conditional_markers": ["{{IF_RELOCATION}}", "{{END_IF_RELOCATION}}"],
  "required_output_checks": [
    "replace template placeholders from employee_data.json",
    "clear all remaining {{...}} placeholders",
    "remove {{IF_RELOCATION}} and {{END_IF_RELOCATION}} markers from final offer letter",
    "keep relocation section content when RELOCATION_PACKAGE is Yes",
    "preserve relocation block as pending continuation at checkpoint time"
  ],
  "status": "checkpointed"
}
```

Write `workflow/continuation_gate.json` with exactly these fields:

```json
{
  "checkpoint_artifact": "workflow/intake_checkpoint.json",
  "next_stage": "offer-letter-working-set",
  "checkpoint_reason": "Freeze input and output identity before placeholder replacement or docx write, and keep relocation markers pending continuation until downstream document handling.",
  "status": "pending_continuation"
}
```

## Steps

1. Confirm both input files exist and are the only sources used for this checkpoint.
2. Record the fixed template path, employee data path, and target output path in `workflow/intake_checkpoint.json`.
3. Record the relocation block markers as `conditional_markers` and leave them pending continuation rather than resolved output.
4. Record only the required output checks needed for later offer letter completion.
5. Write `workflow/continuation_gate.json` so the next stage consumes the checkpoint instead of rescanning broadly.

## Constraints

- Freeze input and output identity before any placeholder replacement or `.docx` write.
- Record the `{{IF_RELOCATION}}...{{END_IF_RELOCATION}}` block as pending continuation rather than resolved output.
- Do not write `/root/offer_letter_filled.docx` in this stage.

## Handoff

The next stage reads these exact keys from `workflow/intake_checkpoint.json`:

- `template_path`
- `employee_data_path`
- `output_path`
- `conditional_markers`
- `required_output_checks`
- `status`

The next stage reads these exact keys from `workflow/continuation_gate.json`:

- `next_stage`
- `checkpoint_reason`
- `status`

## Stop Condition

Stop after both workflow records exist with the exact field names above and the stage has not modified the Word template or written `/root/offer_letter_filled.docx`.