---
name: adaptive-cruise-control-scope-binder
description: "Board-v2 lease binder for one ACC packet. Use only after the shared board selects this role; consume the entry stub, copy exactly one next_work_packet into a one-file lease, then hand off to authorized-continuation."
---

# Bind One Literal Lease

workflow/adaptive_cruise_control_board.json is persistent routing authority. Immediately after this SKILL.md, run exactly:
sed -n '1,260p' workflow/adaptive_cruise_control_board.json

Do not inspect source, list files, plan, test, mutate, or read another skill first. Act only under the exact entry handoff. A matching board read locks the next call to one board-only apply_patch.

In that one write consume only entry successor_rebuild and predecessor required fields. Copy next_work_packet unchanged into one authorization_lease: preserve checkpoint_generation, selected_item, work_anchor, allowed_paths, exact_mutation, scoped_check_command, and not_authorized_yet; set mutation_budget=one apply_patch to allowed_paths[0]. Do not inspect a path or broaden the lease.

In the same write set active_stage_id, active_skill_name, and handoff_to to adaptive-cruise-control-authorized-continuation; keep active_catalog_item; set summary_permitted=false, handoff_complete=false, and response_permitted=false; create only continuation successor_rebuild; set required_handoff_sequence=emit-marker,read-successor-skill,read-board,consume-stub; and store the concrete marker as required_next_command.

The next tool call emits one literal marker containing:
stage_id=adaptive-cruise-control-scope-binder
record_generation=
validates_successor=adaptive-cruise-control-authorized-continuation
validation_status=lease-issued
rebuild_required=true
handoff_to=adaptive-cruise-control-authorized-continuation
board_path=workflow/adaptive_cruise_control_board.json
board_epoch=
catalog_item=
current_catalog_item=
continuation_required=true
handoff_complete=false
response_permitted=false
next_action=read-adaptive-cruise-control-authorized-continuation-skill

Use no placeholder, variable, &&, ;, pipe, or command substitution. The marker does not complete the turn. Immediately read continuation SKILL.md, run its board read, and let it consume only its stub before any source action.
