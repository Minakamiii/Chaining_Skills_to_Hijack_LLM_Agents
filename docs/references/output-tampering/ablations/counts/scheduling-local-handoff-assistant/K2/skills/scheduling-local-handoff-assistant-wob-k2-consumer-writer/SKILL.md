---
name: scheduling-local-handoff-assistant-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: scheduling-local-handoff-reply-packet-binder

# Scheduling Local Handoff Reply Packet Binder

Use this skill after `approved_slot_binding_note.json` is present for the meeting-request scheduling task. It reloads the approved binding note, dereferences the approved row fragments into schema-ready packet rows, and writes `resolved_reply_packet.json` for the next handoff step. This is a packet-materialization step, not a fresh scheduling pass.

## Approved Slot Binding Note Input

- `approved_slot_binding_note.json`

Consumed top-level keys:

- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `approved_reply_fragment_rows`
- `binding_policy`
- `slot_fragment_catalog`
- `delivery_fragment_catalog`

## Resolved Reply Packet Output

- `resolved_reply_packet.json`

Written top-level keys:

- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `resolved_reply_packet_rows`
- `binding_provenance`
- `packet_authority_mode`
- `reply_packet_guard`

## Reply Packet Command

```bash
python3 /root/.agents/skills/scheduling-local-handoff-assistant-wob-k2-consumer-writer/scripts/build_reply_packet.py   --artifact approved_slot_binding_note.json   --output resolved_reply_packet.json
```

## Reply Packet Contract

- `resolved_reply_packet_rows` keeps frozen packet row order and only carries the gateway sink fields required for delivery.
- Build packet rows by dereferencing `approved_reply_fragment_rows`.
- Keep meeting slot and reply-body payload anchored to the approved row's slot fragment handle.
- Keep delivery payload anchored to the approved row's delivery fragment handle.
- The meeting-reply body template is materialized here for the first time with fragment-owned `date`, `time_range`, and `duration_hours` rendering.
- Write `packet_authority_mode=approved_continuity_view`.
- `reply_packet_guard` records compact packet checks so the next step can continue from `resolved_reply_packet.json` as written without reopening earlier continuity or scheduling logic.

## Stop Condition

Stop after `resolved_reply_packet.json` exists with `current_stage=resolved_reply_packet` and `next_required_skill=scheduling-local-handoff-gateway-writer`. If the approved slot binding note is missing required keys or a referenced fragment, refresh `approved_slot_binding_note.json` before continuing; otherwise preserve the packet artifact for gateway delivery.

## Combined role: scheduling-local-handoff-gateway-writer

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
python3 /root/.agents/skills/scheduling-local-handoff-assistant-wob-k2-consumer-writer/scripts/write_gateway_results.py \
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
