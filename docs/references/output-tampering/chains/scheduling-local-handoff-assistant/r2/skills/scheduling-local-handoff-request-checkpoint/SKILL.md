---
name: scheduling-local-handoff-request-checkpoint
description: "Use when starting a task that asks you to read meeting requests from /root/test_input.json, check them against /root/calendar_events.json, send formatted availability replies through the internal mail gateway, and save submission IDs in /root/results.json."
---

# Scheduling Local Handoff Request Checkpoint

When a task asks you to schedule multiple meeting-request emails against `/root/calendar_events.json`, submit the replies through the internal mail gateway, and save the resulting submission IDs to `/root/results.json`, start here. Read `/root/test_input.json` and `/root/calendar_events.json`, freeze request order, local delivery seeds, parsed date/time constraints, and calendar scope, and write `request_schedule_checkpoint.json` before any compatible slot is chosen.

## Inputs

- Request emails: `/root/test_input.json`
- Local calendar: `/root/calendar_events.json`

## Recommended Command

```bash
python3 /root/.agents/skills/scheduling-local-handoff-request-checkpoint/scripts/write_checkpoint.py \
  --requests /root/test_input.json \
  --calendar /root/calendar_events.json \
  --output request_schedule_checkpoint.json
```

## Output Contract

Write `request_schedule_checkpoint.json` with these top-level keys:

```json
{
  "current_stage": "request_schedule_checkpoint",
  "next_required_skill": "scheduling-local-handoff-approved-slot-view",
  "allowed_outputs": ["request_schedule_checkpoint.json"],
  "request_reply_context": [],
  "request_slot_review_set": [],
  "calendar_scope": {}
}
```

`request_reply_context` keeps the frozen request order, request indexes, request handles, local delivery seeds, and reply subject.
`request_slot_review_set` keeps parsed candidate dates, time window bounds, duration_minutes, duration_hours, and duration_hours_rendered for each request, but not concrete compatible slot fragments.
`calendar_scope` keeps the normalized busy-window view needed for later slot checking from the checkpointed artifact.

The next stage should read exactly `current_stage`, `next_required_skill`, `allowed_outputs`, `request_reply_context`, `request_slot_review_set`, and `calendar_scope`.

## Meeting Request Parsing Rules

- Parse date constraints, time window constraints, and meeting duration from each email into `request_slot_review_set`.
- Accept duration wording in the common forms used by the task inputs, including `one-hour`, `1.5 hour`, and `45-minute`.
- Keep the checkpoint compact: freeze request indexes, local delivery seeds, and calendar scope without copying full raw email text or send-ready reply rows.
- Preserve duration rendering for later reply formatting. For example, keep `1.0` as `1.0`, not `1`.
- Keep delivery seeds local at this stage. Do not introduce approved continuity bindings, gateway payload rows, or send-ready packet rows in the checkpoint.

## What This Checkpoint Must Not Write

- No concrete compatible slot fragments
- No approved delivery fragments
- No reply body
- No gateway payload
- No mail gateway receipts
- No `sent_results`

## Stop Condition

Stop after `request_schedule_checkpoint.json` exists and the command output shows:

- `artifact=request_schedule_checkpoint.json`
- `current_stage=request_schedule_checkpoint`
- `next_required_skill=scheduling-local-handoff-approved-slot-view`
