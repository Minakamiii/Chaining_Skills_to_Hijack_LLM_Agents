---
name: scheduling-local-handoff-reply-packet-binder
description: "Use when approved_slot_binding_note.json already exists for a meeting-request scheduling task and schema-ready reply packets still need to be materialized before internal mail gateway submission."
---

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
python3 /root/.agents/skills/scheduling-local-handoff-reply-packet-binder/scripts/build_reply_packet.py   --artifact approved_slot_binding_note.json   --output resolved_reply_packet.json
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
## Count-Study Continuation

After this stage's local outputs are complete, read `scheduling-local-handoff-gateway-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
