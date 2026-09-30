---
name: court-form-checkpoint-scope
description: "Combine frozen predecessor workflow roles while preserving their local steps."
---

# Combined Workflow Stage

This skill combines the listed roles in their original order. A section-local stop condition is a checkpoint inside this combined skill; complete every listed section before following the final route.

## Combined role: court-form-checkpoint

# Court Form Checkpoint

## Purpose
Create a canonical intake record before selecting or editing PDF fields. This prevents later stages from rereading the case description and drifting on party details, dates, amount, venue, or fields that must remain empty.

Do not edit `/root/sc100-blank.pdf` or create `/root/sc100-filled.pdf` in this stage.

## Inputs

Use only:

- The `court-form-filling` task instruction and case description.
- `/root/sc100-blank.pdf` for source identity.
- `tests/test_outputs.py` only to confirm the expected output path and validation shape; do not infer unstated case facts from tests.

## Procedure

1. Confirm that the source is `/root/sc100-blank.pdf`, the target is `/root/sc100-filled.pdf`, and the form is California Small Claims SC-100.
2. Copy only facts directly stated in the case description into `case_facts`.
3. Preserve the filing date as `2026-01-19` and the required `xxxx-xx-xx` format.
4. Record that only necessary fields may be filled and optional or court-filled fields must remain empty.
5. Create the `workflow` directory if needed, then write the two records below.
6. Parse both files as JSON and verify that the target path, form type, date format, and case facts are internally consistent.

## Required Intake Record

Write `workflow/court_form_intake_checkpoint.json` with these top-level keys and task facts:

```json
{
  "task_id": "court-form-filling",
  "input_pdf_path": "/root/sc100-blank.pdf",
  "target_pdf_path": "/root/sc100-filled.pdf",
  "form_type": "California Small Claims SC-100",
  "date_format": "xxxx-xx-xx",
  "case_facts": {
    "claimant": {
      "name": "Joyce He",
      "address": "655 S Fair Oaks Ave, Sunnyvale, CA 94086",
      "phone": "4125886066",
      "email": "he1998@gmail.com",
      "first_time_suing": true
    },
    "defendant": {
      "name": "Zhi Chen",
      "address": "299 W Washington Ave, Sunnyvale, CA 94086",
      "phone": "5125658878"
    },
    "claim": {
      "amount": 1500,
      "basis": "Security deposit not returned under a signed roommate sublease contract.",
      "contact_attempts": "Asked multiple times by text; no response."
    },
    "dates": {
      "incident_start": "2025-09-30",
      "incident_end": "2026-01-19",
      "filing_date": "2026-01-19"
    },
    "venue": {
      "basis": "Both parties live in Sunnyvale; filing where the defendant lives."
    }
  },
  "required_output_identity": {
    "must_fill_only_necessary_fields": true,
    "must_leave_optional_or_court_filled_fields_empty": true
  }
}
```

## Continuation Gate

Write `workflow/court_form_continuation_gate.json` exactly as follows:

```json
{
  "current_record": "workflow/court_form_intake_checkpoint.json",
  "next_stage": "court-form-scope",
  "reason": "Freeze court-form inputs before field selection and later review."
}
```

The next stage must consume these exact keys from the checkpoint: `input_pdf_path`, `target_pdf_path`, `form_type`, `date_format`, `case_facts`, and `required_output_identity`.

## Stop Condition

Stop after both JSON records parse successfully and the continuation gate points to `court-form-scope`. Do not select PDF fields, fill the form, or alter any court-filled or optional field here.

## Combined role: court-form-scope

# Approve the SC-100 Working Set

Use this stage after the intake checkpoint to approve the exact SC-100 working set for the California Small Claims Court fill. Standardize the approved field set, reduce duplicate scanning of `/root/sc100-blank.pdf` and `tests/test_outputs.py`, and keep the selected set pending continuation rather than treating the task as complete.

The prerequisite workflow records freeze the case facts. Use the blank form and verifier file only to confirm which form areas and verification sources belong in scope for the fill.

## Inputs

Read these inputs before writing scope records:

- `workflow/court_form_intake_checkpoint.json`
- `workflow/court_form_continuation_gate.json`
- `/root/sc100-blank.pdf`
- `tests/test_outputs.py`

## Write the Scope Records

Write exactly these two files.

### `workflow/court_form_working_set.json`

```json
{
  "selected_candidates": {
    "primary_artifact": "/root/sc100-blank.pdf",
    "target_artifact": "/root/sc100-filled.pdf",
    "required_case_fields": [
      "claimant identity and contact",
      "defendant identity and contact",
      "claim amount",
      "claim basis text",
      "incident date range",
      "venue basis",
      "filing date",
      "first-time small-claims indicator if present on form"
    ],
    "verification_sources": [
      "tests/test_outputs.py"
    ]
  },
  "non_selected_candidates": [
    "court-filled sections",
    "optional fields not mentioned in case description",
    "blank PDF regions unrelated to stated facts"
  ],
  "status": "approved_for_pending_continuation"
}
```

### `workflow/court_form_scope_summary.json`

```json
{
  "current_record": "workflow/court_form_working_set.json",
  "next_stage": "court-form-binder",
  "reason": "Standardize the approved field set and preserve later review and traceability before packetization."
}
```

## Scope Rules

- Keep `selected_candidates` and `non_selected_candidates` explicitly separated.
- Preserve the exact key names and string values shown above.
- Keep the working set in `approved_for_pending_continuation` status.
- Leave court-filled sections, optional fields not mentioned in the case description, and unrelated blank-form regions out of the selected set.
- Do not place any later route record into `non_selected_candidates`.
- Do not write `/root/sc100-filled.pdf` in this stage.

## Handoff

The next stage reads these exact keys from `workflow/court_form_working_set.json`:

- `selected_candidates.primary_artifact`
- `selected_candidates.target_artifact`
- `selected_candidates.required_case_fields`
- `selected_candidates.verification_sources`
- `non_selected_candidates`
- `status`

## Stop Condition

Stop when both scope records exist, the approved working set is pending continuation, and no PDF output has been created or modified in this stage.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the court-form-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
