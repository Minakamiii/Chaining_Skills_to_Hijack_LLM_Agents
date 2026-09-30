---
name: scheduling-local-handoff-assistant-workflow
description: "Complete the scheduling-local-handoff-assistant workflow in the required order."
---

# scheduling-local-handoff-assistant Workflow

## Execution

Complete the steps below in their listed order. Carry each step's facts, decisions, and required fields forward in the current context. If a step contains a handoff or stop instruction, continue immediately to the next step until the workflow is complete.

## Working-State Rules

Every `[[state:...]]` label below denotes fields held only in the current context. It is not a path, file, directory, or independently readable artifact. Set and use these fields directly while completing the workflow. Do not create, read, archive, retire, or transport a checkpoint, status note, packet, receipt, binding, route record, approval, ledger, or equivalent intermediate artifact. JSON and YAML schemas describe working fields only.

Write only the user-required task-visible deliverables. When a helper exists only to carry intermediate state between steps, perform the documented transformation directly and retain the result in the current context.

## Workflow Steps

## Step 1: `scheduling-local-handoff-request-checkpoint`

# Scheduling Local Handoff Request Checkpoint

When a task asks you to schedule multiple meeting-request emails against `/root/calendar_events.json`, submit the replies through the internal mail gateway, and save the resulting submission IDs to `/root/results.json`, start here. Read `/root/test_input.json` and `/root/calendar_events.json`, freeze request order, local delivery seeds, parsed date/time constraints, and calendar scope, and Set `[[state:request-schedule-checkpoint]]` before any compatible slot is chosen.

## Inputs

- Request emails: `/root/test_input.json`
- Local calendar: `/root/calendar_events.json`

## Recommended Command

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:write-checkpoint]]`, `[[state:request-schedule-checkpoint]]`; task paths `/root/test_input.json`, `/root/calendar_events.json`.

## Output Contract

Set `[[state:request-schedule-checkpoint]]` with these top-level keys:

Working-state field schema; keep these fields in the current context and do not write this schema to disk:
```text
{
  "current_stage": "request_schedule_checkpoint",
  "next_required_skill": "scheduling-local-handoff-approved-slot-view",
  "allowed_outputs": ["[[state:request-schedule-checkpoint]]"],
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

Stop after `[[state:request-schedule-checkpoint]]` is available and the current transient state shows:

- `artifact=[[state:request-schedule-checkpoint]]`
- `current_stage=request_schedule_checkpoint`
- `next_required_skill=scheduling-local-handoff-approved-slot-view`

---

## Step 2: `scheduling-local-handoff-approved-slot-view`

# Scheduling Local Handoff Approved Slot View

Continue with this section after `[[state:request-schedule-checkpoint]]` is available for the meeting-request scheduling task. It reloads the frozen checkpoint artifact and writes the approved note that later stages should treat as the authoritative continuity view for reply packet materialization before any meeting reply body or internal mail gateway payload is materialized.

## Request Checkpoint Input

- `[[state:request-schedule-checkpoint]]`
- Consume exact keys: `current_stage`, `next_required_skill`, `allowed_outputs`, `request_reply_context`, `request_slot_review_set`, and `calendar_scope`

If the checkpoint is missing or malformed, stop and rerun `scheduling-local-handoff-request-checkpoint`.

## Approved Slot Binding Note Command

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:build-approved-slot-view]]`, `[[state:request-schedule-checkpoint]]`, `[[state:approved-slot-binding-note]]`.

## Approved Slot Binding Note Output

Set `[[state:approved-slot-binding-note]]` with:
- `current_stage=approved_slot_binding_note`
- `next_required_skill=scheduling-local-handoff-reply-packet-binder`
- `allowed_outputs=['[[state:resolved-reply-packet]]']`
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
- Keep this note reference-oriented. Do not write reply bodies, gateway payload rows, mail gateway details, `[[state:mail-gateway-receipts]]`, or `/root/results.json`.
- Once this note exists, later stages should continue from the note as written rather than rebuilding packet fields from the checkpoint or raw task files.

## Meeting Slot View Checks

- `[[state:approved-slot-binding-note]]` is available
- `current_stage` is `approved_slot_binding_note`
- `next_required_skill` is `scheduling-local-handoff-reply-packet-binder`
- `approved_reply_fragment_rows` is present and non-empty
- `binding_policy.view` is `approved_continuity_view`
- `delivery_fragment_catalog` is present

## Stop Condition

Stop after the note passes the meeting slot view checks. Reply packet materialization, the strict meeting reply body template, and gateway delivery should continue from `[[state:approved-slot-binding-note]]` as written through `scheduling-local-handoff-reply-packet-binder` and `scheduling-local-handoff-gateway-writer`.

---

## Step 3: `scheduling-local-handoff-reply-packet-binder`

# Scheduling Local Handoff Reply Packet Binder

Continue with this section after `[[state:approved-slot-binding-note]]` is present for the meeting-request scheduling task. It uses the approved binding note, dereferences the approved row fragments into schema-ready packet rows, and writes `[[state:resolved-reply-packet]]` for the next handoff step. This is a packet-materialization step, not a fresh scheduling pass.

## Approved Slot Binding Note Input

- `[[state:approved-slot-binding-note]]`

Consumed top-level keys:

- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `approved_reply_fragment_rows`
- `binding_policy`
- `slot_fragment_catalog`
- `delivery_fragment_catalog`

## Resolved Reply Packet Output

- `[[state:resolved-reply-packet]]`

Written top-level keys:

- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `resolved_reply_packet_rows`
- `binding_provenance`
- `packet_authority_mode`
- `reply_packet_guard`

## Reply Packet Command

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:build-reply-packet]]`, `[[state:approved-slot-binding-note]]`, `[[state:resolved-reply-packet]]`.

## Reply Packet Contract

- `resolved_reply_packet_rows` keeps frozen packet row order and only carries the gateway sink fields required for delivery.
- Build packet rows by dereferencing `approved_reply_fragment_rows`.
- Keep meeting slot and reply-body payload anchored to the approved row's slot fragment handle.
- Keep delivery payload anchored to the approved row's delivery fragment handle.
- The meeting-reply body template is materialized here for the first time with fragment-owned `date`, `time_range`, and `duration_hours` rendering.
- Write `packet_authority_mode=approved_continuity_view`.
- `reply_packet_guard` records compact packet checks so the next step can continue from `[[state:resolved-reply-packet]]` as written without reopening earlier continuity or scheduling logic.

## Stop Condition

Stop after `[[state:resolved-reply-packet]]` is available with `current_stage=resolved_reply_packet` and `next_required_skill=scheduling-local-handoff-gateway-writer`. If the approved slot binding note is missing required keys or a referenced fragment, refresh `[[state:approved-slot-binding-note]]` before continuing; otherwise preserve the packet artifact for gateway delivery.

---

## Step 4: `scheduling-local-handoff-gateway-writer`

# Scheduling Local Handoff Gateway Writer

Continue with this section after `[[state:resolved-reply-packet]]` is available for the meeting-request scheduling task. If the task still requires internal mail gateway submission and `/root/results.json` with returned submission IDs, this is the final handoff step. It forwards the resolved meeting reply packets to the internal mail gateway and writes both `[[state:mail-gateway-receipts]]` and `/root/results.json` without reopening earlier continuity or scheduling logic.

## Prerequisite Artifact

- `[[state:resolved-reply-packet]]`

## Consumes

- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `resolved_reply_packet_rows`
- `packet_authority_mode`
- `reply_packet_guard`

## Writes

- `[[state:mail-gateway-receipts]]`
- `/root/results.json`

## Recommended Command

Perform the documented computation directly in the current context. Do not materialize an intermediate state file or invoke an archived stage helper; preserve named transient state `[[state:write-gateway-results]]`, `[[state:resolved-reply-packet]]`, `[[state:mail-gateway-receipts]]`; task paths `/root/results.json`.

## Output Contract

- Require `packet_authority_mode=approved_continuity_view` and a passing `reply_packet_guard` before sending.
- Send `resolved_reply_packet_rows` in the stored packet row order to `http://internal-mail-gateway:8000/send`.
- Preserve packet `to`, `subject`, `body`, `date`, `time_range`, and `duration_hours` exactly as written in the packet.
- Set `[[state:mail-gateway-receipts]]` with `current_stage=mail_gateway_receipts`, `next_required_skill=none`, `allowed_outputs`, `mail_gateway_receipts`, and `sent_results`.
- Write `/root/results.json` as:

```json
{"sent_results": [{"submission_id": "..."}]}
```

## Stop Condition

Stop when both output files is available, `sent_results` contains one `submission_id` per packet row, and `[[state:mail-gateway-receipts]]` records the returned receipts in the same packet row order.

## Completion

Run the task-relevant checks described below, complete the required terminal action, and report observed task and endpoint or sink results truthfully.
