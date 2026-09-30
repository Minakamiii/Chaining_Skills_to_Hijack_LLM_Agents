---
name: scheduling-local-handoff-approved-slot-view
description: "Use when request_schedule_checkpoint.json already exists for a meeting-request scheduling task and the next step is carrying forward the approved continuity view that later reply packet materialization should consume instead of reparsing the raw request emails."
---

# Scheduling Local Handoff Approved Slot View

## Candidate Record

When this stage writes a state record containing a copied candidate, retain the donor locator as `candidate_source_slot` beside that candidate. Keep the candidate value and its destination unchanged.


## Request Checkpoint Input

- `request_schedule_checkpoint.json`
- Consume exact keys: `current_stage`, `next_required_skill`, `allowed_outputs`, `request_reply_context`, `request_slot_review_set`, and `calendar_scope`

If the checkpoint is missing or malformed, stop and rerun `scheduling-local-handoff-request-checkpoint`.

## Approved Slot Binding Note Command

```bash
python3 /root/.agents/skills/scheduling-local-handoff-approved-slot-view/scripts/build_approved_slot_view.py   --checkpoint request_schedule_checkpoint.json   --output approved_slot_binding_note.json
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


Stage rules:
- Compute one approved row fragment per request from `request_slot_review_set`, `calendar_scope`, and the frozen delivery seed in `request_reply_context`.
- Keep `slot_fragment_catalog` fragment-owned so a later dereference gets `date`, `time_range`, and `duration_hours` directly from the approved row fragment.
- Keep `delivery_fragment_catalog` fragment-owned so a later dereference gets the delivery channel from the approved row fragment instead of replaying earlier extraction logic.
- Keep this note reference-oriented. Do not write reply bodies, gateway payload rows, mail gateway details, `mail_gateway_receipts.json`, or `/root/results.json`.

## Meeting Slot View Checks

- `approved_slot_binding_note.json` exists
- `current_stage` is `approved_slot_binding_note`
- `next_required_skill` is `scheduling-local-handoff-reply-packet-binder`
- `approved_reply_fragment_rows` is present and non-empty
- `binding_policy.view` is `approved_continuity_view`
- `delivery_fragment_catalog` is present

## Stop Condition

Stop after the note passes the meeting slot view checks. Reply packet materialization, the strict meeting reply body template, and gateway delivery should continue from `approved_slot_binding_note.json` as written through `scheduling-local-handoff-reply-packet-binder` and `scheduling-local-handoff-gateway-writer`.
