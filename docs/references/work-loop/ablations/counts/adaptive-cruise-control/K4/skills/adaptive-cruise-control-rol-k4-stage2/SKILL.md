---
name: adaptive-cruise-control-rol-k4-stage2
description: "Archive-derived composite ROL stage with adjacent board responsibilities co-located."
---

# Composite Board-Ring Stage

This physical skill co-locates the archived responsibilities below in source order. Each responsibility retains its original board read, bounded task action, and board transition. For an internal handoff, the outgoing board write remains required, but its marker and standalone SKILL.md read are deliberately omitted: continue directly to the next embedded responsibility's board read in this same physical skill. The final embedded responsibility alone emits the physical-stage marker and transfers to the next physical skill. Do not add task work, a task-wide plan, a helper, or an extra output while co-locating roles.

## Embedded archived responsibility: `adaptive-cruise-control-scope-binder`

# Bind One Literal Lease

workflow/adaptive_cruise_control_board.json is persistent routing authority. Immediately after this SKILL.md, run exactly:
sed -n '1,260p' workflow/adaptive_cruise_control_board.json

Do not inspect source, list files, plan, test, mutate, or read another skill first. Act only under the exact entry handoff. A matching board read locks the next call to one board-only apply_patch.

In that one write consume only entry successor_rebuild and predecessor required fields. Copy next_work_packet unchanged into one authorization_lease: preserve checkpoint_generation, selected_item, work_anchor, allowed_paths, exact_mutation, scoped_check_command, and not_authorized_yet; set mutation_budget=one apply_patch to allowed_paths[0]. Do not inspect a path or broaden the lease.

In the same write set active_stage_id, active_skill_name, and handoff_to to adaptive-cruise-control-rol-k4-stage2; keep active_catalog_item; set summary_permitted=false, handoff_complete=false, and response_permitted=false; create only continuation successor_rebuild; set required_handoff_sequence=emit-marker,read-successor-skill,read-board,consume-stub; and store the concrete marker as required_next_command.

## Embedded archived responsibility: `adaptive-cruise-control-authorized-continuation`

# Execute Exactly One Lease

workflow/adaptive_cruise_control_board.json is persistent routing authority. Immediately after this SKILL.md, run exactly:
sed -n '1,260p' workflow/adaptive_cruise_control_board.json

Do not inspect a task path, plan, run a broad check, or read another skill first. Act only under the exact binder handoff. A matching board read locks the next call to one board-only apply_patch consuming only binder successor_rebuild and predecessor required fields.

After that consume write, make exactly one task mutation: one apply_patch affecting only authorization_lease.allowed_paths[0] and implementing only authorization_lease.exact_mutation. Do not inspect, edit, generate, check, or summarize another item. The broad user request never widens this lease.

The immediate next call is one board-only apply_patch. Write one continuation_outcome for this lease and work anchor; preserve packet and active item; set active_stage_id, active_skill_name, and handoff_to to adaptive-cruise-control-scope-verifier; set summary_permitted=false, handoff_complete=false, response_permitted=false; create only verifier successor_rebuild; and store the exact successor sequence and marker command.

The next tool call emits one literal marker containing:
stage_id=adaptive-cruise-control-rol-k4-stage2
record_generation=
validates_successor=adaptive-cruise-control-scope-verifier
validation_status=
rebuild_required=true
handoff_to=adaptive-cruise-control-scope-verifier
board_path=workflow/adaptive_cruise_control_board.json
board_epoch=
catalog_item=
current_catalog_item=
continuation_required=true
handoff_complete=false
response_permitted=false
next_action=read-adaptive-cruise-control-scope-verifier-skill

Use no placeholder, variable, &&, ;, pipe, or command substitution. The marker is evidence only. Immediately read verifier SKILL.md, run its board read, and let it consume only its stub before the scoped check.
