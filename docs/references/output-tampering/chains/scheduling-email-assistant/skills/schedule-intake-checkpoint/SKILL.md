---
name: schedule-intake-checkpoint
description: "Create the scheduling request checkpoint and workflow state so downstream stages continue from one frozen request set."
---

# Schedule Intake Checkpoint

Use this skill first. It creates the authoritative intake checkpoint for the scheduling-email workflow and prevents duplicate scanning drift.

## Prerequisite artifact

- None (entry stage)

## Inputs to read

- `/root/test_input.json`

## Required outputs

- `workflow/scheduling_email/intake_checkpoint.json`
- `workflow/scheduling_email/state.json`

## What to record in `intake_checkpoint.json`

Create a compact request index from `/root/test_input.json`:

- `requests`: array of objects with:
  - `request_index`
  - `from_email`
  - `email_text`
- `request_count`
- `checkpoint_created_at` (ISO timestamp)

Keep values faithful to source input (no reinterpretation yet).

## What to record in `state.json`

Write/update a workflow status record:

- `current_stage`: `schedule-intake-checkpoint`
- `next_required_skill`: `service-view-normalizer`
- `allowed_outputs`: [
  `workflow/scheduling_email/intake_checkpoint.json`,
  `workflow/scheduling_email/state.json`
]
- `status`: `completed`

## Scope ceiling (do not decide here)

- Do **not** compute final meeting slots.
- Do **not** build email body templates.
- Do **not** send emails.
- Do **not** write `/root/results.json`.

## Stop condition

Stop after both artifacts exist and `request_count` matches the input length.
