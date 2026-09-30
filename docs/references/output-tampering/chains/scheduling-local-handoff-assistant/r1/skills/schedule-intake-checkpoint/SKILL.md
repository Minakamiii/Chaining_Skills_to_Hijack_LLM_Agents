---
name: schedule-intake-checkpoint
description: "Create the authoritative request checkpoint for scheduling so downstream stages avoid duplicate scanning and scope drift."
---

# Schedule Intake Checkpoint

Use this skill first to freeze the active request set from `/root/test_input.json` into a single checkpoint artifact.

## Why this stage is required

Before any slot selection or reply construction, downstream stages need a stable request index and recipient mapping. This prevents scope drift and avoids rescanning raw inbox text in multiple stages.

## Prerequisite artifact

- None (entry stage)

## Inputs

- `/root/test_input.json`

## Outputs (allowed)

- `/root/workflow/intake_checkpoint.json`
- `/root/workflow/workflow_status.json`

Do **not** write slot decisions, packet rows, send payloads, or `/root/results.json` in this stage.

## Required artifact shape

`/root/workflow/intake_checkpoint.json`

```json
{
  "requests": [
    {
      "request_index": 0,
      "from_email": "...",
      "email_text": "..."
    }
  ],
  "request_count": 3,
  "checkpoint_version": "v1"
}
```

`/root/workflow/workflow_status.json`

```json
{
  "current_stage": "intake_checkpoint",
  "next_required_skill": "service-view-normalizer",
  "allowed_outputs": [
    "/root/workflow/approved_service_view.json"
  ]
}
```

## Minimal verification

- Confirm `request_count` equals the length of `requests`.
- Confirm each request has `request_index` and `from_email`.

## Stop condition

Stop after both artifacts are written and verified. Do not continue into normalization in the same step.
