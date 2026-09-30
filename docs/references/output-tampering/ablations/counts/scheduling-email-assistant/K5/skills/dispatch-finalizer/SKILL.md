---
name: dispatch-finalizer
description: "Send packetized replies through Gmail, write results.json, and record completion evidence from the dispatched packet."
---

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
