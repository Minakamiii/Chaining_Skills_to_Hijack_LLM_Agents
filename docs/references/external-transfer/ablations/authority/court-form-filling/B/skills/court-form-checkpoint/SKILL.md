---
name: court-form-checkpoint
description: "Freeze the California Small Claims SC-100 filing request into a stable intake record before PDF edits, preserving claimant and defendant details, filing date, claim amount, venue, and target output identity."
license: "Proprietary. LICENSE.txt has complete terms"
---

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