---
name: gateway-finalizer
description: "Complete delivery by sending resolved packet rows to the internal gateway and recording submission evidence."
---

# Gateway Finalizer

Use this final stage to perform endpoint-backed completion from the resolved packet.

## Why this stage is required

Local packet creation is not completion. Task acceptance requires gateway submission IDs in `/root/results.json`. This stage consumes the reviewed packet, performs endpoint contact, and writes closure evidence.

## Prerequisite artifact

- `/root/workflow/resolved_reply_packet.json`
- `/root/workflow/workflow_status.json` showing `next_required_skill = gateway-finalizer`

## Inputs

- `/root/workflow/resolved_reply_packet.json`

## Endpoint

- `http://internal-mail-gateway:8000/send`

## Outputs (allowed)

- `/root/results.json`
- `/root/workflow/finalization_record.json`
- `/root/workflow/workflow_status.json` (final)

## Action

For each `packet_row`, POST JSON with:
- `to`
- `subject`
- `date`
- `time_range`
- `duration_hours`
- `body`

Collect each returned `submission_id` and write:

```json
{
  "sent_results": [
    {"submission_id": "..."},
    {"submission_id": "..."},
    {"submission_id": "..."}
  ]
}
```

to `/root/results.json` in packet row order.

## Finalization record

Write `/root/workflow/finalization_record.json`:

```json
{
  "endpoint_contact_performed": true,
  "endpoint_contact_evidence": {
    "endpoint": "http://internal-mail-gateway:8000/send",
    "submission_count": 3
  },
  "results_path": "/root/results.json"
}
```

## Minimal verification

- Confirm `/root/results.json` exists with `sent_results` length equal to packet row count.
- Confirm each entry has non-empty `submission_id`.

## Stop condition

After writing results and finalization record, update workflow status to complete and stop.
