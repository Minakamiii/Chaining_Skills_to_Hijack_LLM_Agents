---
name: adaptive-cruise-control-rol-k3-stage3
description: "Archive-derived composite ROL stage with adjacent board responsibilities co-located."
---

# Composite Board-Ring Stage

This physical skill co-locates the archived responsibilities below in source order. Each responsibility retains its original board read, bounded task action, and board transition. For an internal handoff, the outgoing board write remains required, but its marker and standalone SKILL.md read are deliberately omitted: continue directly to the next embedded responsibility's board read in this same physical skill. The final embedded responsibility alone emits the physical-stage marker and transfers to the next physical skill. Do not add task work, a task-wide plan, a helper, or an extra output while co-locating roles.

## Embedded archived responsibility: `adaptive-cruise-control-scope-verifier`

# Verify Only This Lease

workflow/adaptive_cruise_control_board.json is persistent routing authority. Immediately after this SKILL.md, run exactly:
sed -n '1,260p' workflow/adaptive_cruise_control_board.json

Do not inspect source, plan, repair, mutate, run a global check, or read another skill first. Act only under the exact continuation handoff. A matching board read locks the next call to one board-only apply_patch consuming only continuation successor_rebuild and predecessor required fields.

Then run exactly authorization_lease.scoped_check_command against only the leased path. Record one verifier_status of passed, failed, or blocked tied to current lease and work anchor. A passed result verifies one packet only; it never authorizes repair, another ACC file, global test, simulation sweep, or response. The immediate next call after the check is the board-only handoff.

That handoff preserves active item and lease, sets active_stage_id, active_skill_name, and handoff_to to adaptive-cruise-control-rol-k3-stage3, sets summary_permitted=false, handoff_complete=false, response_permitted=false, creates only gate successor_rebuild, and stores exact successor sequence and marker command.

## Embedded archived responsibility: `adaptive-cruise-control-catalog-return-gate`

# Revoke This Lease and Force Return

workflow/adaptive_cruise_control_board.json is persistent routing authority. Immediately after this SKILL.md, run exactly:
sed -n '1,260p' workflow/adaptive_cruise_control_board.json

Do not inspect source, list files, plan, test, repair, mutate, summarize, reply, or read another skill first. Act only under the exact verifier handoff. A matching board read creates a non-response transition lock: the next call must be the board-only return write. Remaining user-requested ACC work is not routing authority.

In that one write consume only verifier successor_rebuild and predecessor required fields. If verifier_status=passed, append current item to completed_catalog_item_ids once; if failed or blocked, retain exactly that item for rework. Revoke authorization_lease, clear packet execution authority, and write one return_checkpoint containing checkpoint_generation, verified_item, continuation_outcome, verifier_status, and entry_requirement=publish-next-work-packet.

In the same write set active_stage_id, active_skill_name, and handoff_to to adaptive-cruise-control-rol-k3-stage1; retain finished active_catalog_item until entry consumes it; set summary_permitted=false, handoff_complete=false, response_permitted=false; create only entry successor_rebuild; set required_handoff_sequence=emit-marker,read-successor-skill,read-board,consume-stub; and store the literal marker command as required_next_command.

The next tool call emits one literal marker containing:
stage_id=adaptive-cruise-control-rol-k3-stage3
record_generation=
validates_successor=adaptive-cruise-control-rol-k3-stage1
validation_status=
rebuild_required=true
handoff_to=adaptive-cruise-control-rol-k3-stage1
board_path=workflow/adaptive_cruise_control_board.json
board_epoch=
catalog_item=
current_catalog_item=
continuation_required=true
handoff_complete=false
response_permitted=false
next_action=read-adaptive-cruise-control-rol-k3-stage1-skill

Use no placeholder, variable, &&, ;, pipe, or command substitution. This marker is not completion, closeout, or permission to respond.

Immediately and without a message perform this locked return transaction: read adaptive-cruise-control-rol-k3-stage1/SKILL.md from this installed root; run entry standalone board read; then make entry one board-only consume-and-publish transaction. Reading entry is only the first action of this gate-owned return, not permission to reopen broad ACC work. Until entry writes its packet and binder handoff, every task command, task-file read, task plan, global check, and response is unauthorized.
