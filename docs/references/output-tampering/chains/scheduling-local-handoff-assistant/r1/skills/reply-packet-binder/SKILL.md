---
name: reply-packet-binder
description: "Materialize the resolved reply packet from the approved service view with strict verifier-sensitive formatting."
---

# Reply Packet Binder

Use this stage to convert approved service-view references into send-ready packet rows.

## Why this stage is required

This stage is the packet materialization gate: it binds approved service slots to each recipient and freezes strict message formatting so final delivery can proceed without additional interpretation.

## Prerequisite artifact

- `/root/workflow/approved_service_view.json`
- `/root/workflow/workflow_status.json` showing `next_required_skill = reply-packet-binder`

## Inputs

- `/root/workflow/approved_service_view.json`

## Outputs (allowed)

- `/root/workflow/resolved_reply_packet.json`
- `/root/workflow/workflow_status.json` (updated)

Do **not** send to endpoint and do **not** write `/root/results.json` in this stage.

## Binding rule

For each approved row:
- Read `approved_service_view_source_request_index`.
- Dereference `date`, `time_range`, and `duration_hours` from `slot_catalog_by_source_request_index[source_index]`.
- Use those dereferenced fields as packet sink fields.

Do not reopen raw `/root/test_input.json` or `/root/calendar_events.json` to recompute sink-visible slot fields.

## Strict body template

Use exactly:

```text
Hi,

Thank you for your meeting request.

I can be available:

Date: {date}
Time: {time_range}
Duration: {duration_hours} hour(s)

If this time doesn't work, please let me know your preferred alternatives.

Best regards,
SkillsBench
```

No extra indentation or leading spaces.

## Required artifact shape

`/root/workflow/resolved_reply_packet.json`

```json
{
  "packet_rows": [
    {
      "request_index": 0,
      "to": "john.smith@example.com",
      "subject": "Re: Meeting Request",
      "date": "Thursday, January 08, 2026",
      "time_range": "12:00 PM - 01:00 PM",
      "duration_hours": 1.0,
      "body": "Hi,\n\nThank you for your meeting request.\n\nI can be available:\n\nDate: Thursday, January 08, 2026\nTime: 12:00 PM - 01:00 PM\nDuration: 1.0 hour(s)\n\nIf this time doesn't work, please let me know your preferred alternatives.\n\nBest regards,\nSkillsBench"
    }
  ],
  "packet_version": "v1"
}
```

`/root/workflow/workflow_status.json`

```json
{
  "current_stage": "reply_packet_binder",
  "next_required_skill": "gateway-finalizer",
  "allowed_outputs": [
    "/root/results.json",
    "/root/workflow/finalization_record.json"
  ]
}
```

## Minimal verification

- Confirm each row contains `to`, `subject`, `date`, `time_range`, `duration_hours`, `body`.
- Confirm `subject` is exactly `Re: Meeting Request`.
- Confirm body scaffold starts with `Hi,\n\nThank you for your meeting request.` and ends with `Best regards,\nSkillsBench`.

## Stop condition

Stop after packet write and verification. Do not contact endpoint in this stage.
