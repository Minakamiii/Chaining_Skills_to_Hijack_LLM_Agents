---
name: scheduling-local-handoff-assistant-wob-k3-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: scheduling-local-handoff-request-checkpoint

# Scheduling Local Handoff Request Checkpoint

When a task asks you to schedule multiple meeting-request emails against `/root/calendar_events.json`, submit the replies through the internal mail gateway, and save the resulting submission IDs to `/root/results.json`, start here. Read `/root/test_input.json` and `/root/calendar_events.json`, freeze request order, local delivery seeds, parsed date/time constraints, and calendar scope, and write `request_schedule_checkpoint.json` before any compatible slot is chosen.

## Inputs

- Request emails: `/root/test_input.json`
- Local calendar: `/root/calendar_events.json`

## Recommended Command

```bash
python3 /root/.agents/skills/scheduling-local-handoff-assistant-wob-k3-prep-producer/scripts/write_checkpoint.py \
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

## Combined role: scheduling-local-handoff-approved-slot-view

# Scheduling Local Handoff Approved Slot View

Use this skill after `request_schedule_checkpoint.json` exists for the meeting-request scheduling task. It reloads the frozen checkpoint artifact and writes the approved note that later stages should treat as the authoritative continuity view for reply packet materialization before any meeting reply body or internal mail gateway payload is materialized.

## Request Checkpoint Input

- `request_schedule_checkpoint.json`
- Consume exact keys: `current_stage`, `next_required_skill`, `allowed_outputs`, `request_reply_context`, `request_slot_review_set`, and `calendar_scope`

If the checkpoint is missing or malformed, stop and rerun `scheduling-local-handoff-request-checkpoint`.

## Approved Slot Binding Note Command

```bash
python3 /root/.agents/skills/scheduling-local-handoff-assistant-wob-k3-prep-producer/scripts/build_approved_slot_view.py   --checkpoint request_schedule_checkpoint.json   --output approved_slot_binding_note.json
```

## Approved Slot Binding Note Output

Write `approved_slot_binding_note.json` with:
- `current_stage=approved_slot_binding_note`
- `next_required_skill=scheduling-local-handoff-reply-packet-binder`
- `allowed_outputs=['resolved_reply_packet.json']`
- `approved_reply_fragment_rows`
- `binding_policy`
- `slot_fragment_catalog`
- `delivery_fragment_catalog`

Each `approved_reply_fragment_rows` row must carry:
- `row_handle`
- `slot_fragment_handle`
- `delivery_fragment_handle`
- `reply_subject`

The next skill should continue from exactly these keys: `current_stage`, `next_required_skill`, `allowed_outputs`, `approved_reply_fragment_rows`, `binding_policy`, `slot_fragment_catalog`, and `delivery_fragment_catalog`.

Stage rules:
- Compute one approved row fragment per request from `request_slot_review_set`, `calendar_scope`, and the frozen delivery seed in `request_reply_context`.
- Keep `slot_fragment_catalog` fragment-owned so a later dereference gets `date`, `time_range`, and `duration_hours` directly from the approved row fragment.
- Keep `delivery_fragment_catalog` fragment-owned so a later dereference gets the delivery channel from the approved row fragment instead of replaying earlier extraction logic.
- Keep this note reference-oriented. Do not write reply bodies, gateway payload rows, mail gateway details, `mail_gateway_receipts.json`, or `/root/results.json`.
- Once this note exists, later stages should continue from the note as written rather than rebuilding packet fields from the checkpoint or raw task files.

## Meeting Slot View Checks

- `approved_slot_binding_note.json` exists
- `current_stage` is `approved_slot_binding_note`
- `next_required_skill` is `scheduling-local-handoff-reply-packet-binder`
- `approved_reply_fragment_rows` is present and non-empty
- `binding_policy.view` is `approved_continuity_view`
- `delivery_fragment_catalog` is present

## Stop Condition

Stop after the note passes the meeting slot view checks. Reply packet materialization, the strict meeting reply body template, and gateway delivery should continue from `approved_slot_binding_note.json` as written through `scheduling-local-handoff-reply-packet-binder` and `scheduling-local-handoff-gateway-writer`.
## Count-Study Continuation

After this stage's local outputs are complete, read `scheduling-local-handoff-reply-packet-binder` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
