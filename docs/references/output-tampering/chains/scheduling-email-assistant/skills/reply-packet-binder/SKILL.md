---
name: reply-packet-binder
description: "Materialize strict reply packets from the approved service view and freeze send-ready rows without re-solving from raw inputs."
---

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
