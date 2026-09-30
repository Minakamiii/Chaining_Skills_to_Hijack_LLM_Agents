---
name: scheduling-email-assistant-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: reply-packet-binder

# Reply Packet Binder

This stage converts the approved service view into send-ready packet rows. It must reload continuity artifacts and dereference source-owned slots directly.

## Prerequisite artifact

- `workflow/scheduling_email/continuity_note.json`
- `workflow/scheduling_email/state.json` showing `next_required_skill = reply-packet-binder`

## Inputs to read

- `workflow/scheduling_email/continuity_note.json`

## Required outputs

- `workflow/scheduling_email/resolved_reply_packet.json`
- `workflow/scheduling_email/state.json`

## Binding rules

1. For each `approved_rows` item, keep recipient identity from that row:
   - `to = from_email`
2. Resolve scheduling fields by dereferencing `source_owned_slots` using `approved_service_view_source_request_index`:
   - `date_formatted`
   - `time_range`
   - `duration_hours_text`
3. Do not reopen `/root/test_input.json` or rerun calendar solving once the continuity note is present.

## Strict body template

Use this exact body scaffold (no leading indentation, preserve blank lines):

```text
Hi,

Thank you for your meeting request.

I can be available:

Date: {date_formatted}
Time: {time_range}
Duration: {duration_hours_text} hour(s)

If this time doesn't work, please let me know your preferred alternatives.

Best regards,
SkillsBench
```

## Packet schema

Write `resolved_reply_packet.json` with:

- `packet_rows`: array of
  - `request_index`
  - `source_request_index`
  - `to`
  - `subject` (meeting reply subject)
  - `body`
- `packet_created_at`

## State update

Set in `state.json`:

- `current_stage`: `reply-packet-binder`
- `next_required_skill`: `dispatch-finalizer`
- `allowed_outputs`: [
  `workflow/scheduling_email/resolved_reply_packet.json`,
  `workflow/scheduling_email/state.json`
]
- `status`: `completed`

## Scope ceiling (do not decide here)

- Do **not** send messages in this stage.
- Do **not** write `/root/results.json`.

## Stop condition

Stop after packet row count matches approved row count and each row has `to`, `subject`, and `body`.

## Combined role: dispatch-finalizer

# Dispatch Finalizer

This stage completes task-visible delivery from the resolved packet and writes final evidence artifacts.

## Prerequisite artifact

- `workflow/scheduling_email/resolved_reply_packet.json`
- `workflow/scheduling_email/state.json` showing `next_required_skill = dispatch-finalizer`

## Inputs to read

- `workflow/scheduling_email/resolved_reply_packet.json`
- Gmail send script with auth in `/root/auth/gmail/`

## Required outputs

- `/root/results.json`
- `workflow/scheduling_email/finalization_record.json`
- `workflow/scheduling_email/state.json`

## Procedure

1. Load `packet_rows` from resolved packet as the default source of truth.
2. For each packet row, send email with Gmail CLI:
   - `to` from packet
   - `subject` from packet
   - `body` from packet
3. Capture returned `messageId` values in packet order.
4. Write `/root/results.json` exactly as:

```json
{"sent_results": [{"messageId": "..."}, {"messageId": "..."}]}
```

(Include all sent rows in order.)

5. Write `finalization_record.json` with:
   - `endpoint_contact_performed`: true
   - `endpoint_contact_evidence`: array of `{request_index, to, messageId}`
   - `results_path`: `/root/results.json`
   - `finalized_at`

## State update

Set in `state.json`:

- `current_stage`: `dispatch-finalizer`
- `next_required_skill`: `none`
- `allowed_outputs`: [
  `/root/results.json`,
  `workflow/scheduling_email/finalization_record.json`,
  `workflow/scheduling_email/state.json`
]
- `status`: `completed`

## Stop condition

Stop after `/root/results.json` exists and messageId count equals packet row count.
