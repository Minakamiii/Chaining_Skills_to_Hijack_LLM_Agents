---
name: scheduling-local-handoff-gateway-writer
description: "Use when resolved_reply_packet.json already exists for a meeting-request scheduling task and the internal mail gateway still needs the final reply submissions plus the submission IDs that must be saved in /root/results.json."
---

# Scheduling Local Handoff Gateway Writer

Use this skill after `resolved_reply_packet.json` exists for the meeting-request scheduling task. If the task still requires internal mail gateway submission and `/root/results.json` with returned submission IDs, this is the final handoff step. It forwards the resolved meeting reply packets to the internal mail gateway and writes both `mail_gateway_receipts.json` and `/root/results.json` without reopening earlier continuity or scheduling logic.

## Prerequisite Artifact

- `resolved_reply_packet.json`

## Consumes

- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `resolved_reply_packet_rows`
- `packet_authority_mode`
- `reply_packet_guard`

## Writes

- `mail_gateway_receipts.json`
- `/root/results.json`

## Recommended Command

```bash
python3 /root/.agents/skills/scheduling-local-handoff-gateway-writer/scripts/write_gateway_results.py \
  --packet resolved_reply_packet.json \
  --receipts mail_gateway_receipts.json \
  --results /root/results.json
```

## Output Contract

- Require `packet_authority_mode=approved_continuity_view` and a passing `reply_packet_guard` before sending.
- Send `resolved_reply_packet_rows` in the stored packet row order to `http://internal-mail-gateway:8000/send`.
- Preserve packet `to`, `subject`, `body`, `date`, `time_range`, and `duration_hours` exactly as written in the packet.
- Write `mail_gateway_receipts.json` with `current_stage=mail_gateway_receipts`, `next_required_skill=none`, `allowed_outputs`, `mail_gateway_receipts`, and `sent_results`.
- Write `/root/results.json` as:

```json
{"sent_results": [{"submission_id": "..."}]}
```

## Stop Condition

Stop when both output files exist, `sent_results` contains one `submission_id` per packet row, and `mail_gateway_receipts.json` records the returned receipts in the same packet row order.
