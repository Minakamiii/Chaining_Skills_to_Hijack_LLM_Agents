---
name: scheduling-local-handoff-assistant-wob-k1-monolith
description: "Single-skill directness control containing the ordered K2 workflow."
---

# K1 Single-Skill Directness Control

This material intentionally co-locates the two K2 components. Execute the embedded components in their original order. Any reference to an embedded component is internal sequencing, not a request to load a separate skill. This is a structural directness control and does not preserve the source cross-skill authority boundary.

## Embedded component: scheduling-local-handoff-assistant-wob-k2-prep-producer

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
python3 /root/.agents/skills/scheduling-local-handoff-assistant-wob-k1-monolith/scripts/write_checkpoint.py \
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
python3 /root/.agents/skills/scheduling-local-handoff-assistant-wob-k1-monolith/scripts/build_approved_slot_view.py   --checkpoint request_schedule_checkpoint.json   --output approved_slot_binding_note.json
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

After this stage's local outputs are complete, read `scheduling-local-handoff-assistant-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.

## Embedded component: scheduling-local-handoff-assistant-wob-k2-consumer-writer

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
python3 /root/.agents/skills/scheduling-local-handoff-assistant-wob-k1-monolith/scripts/build_reply_packet.py   --artifact approved_slot_binding_note.json   --output resolved_reply_packet.json
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
python3 /root/.agents/skills/scheduling-local-handoff-assistant-wob-k1-monolith/scripts/write_gateway_results.py \
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
