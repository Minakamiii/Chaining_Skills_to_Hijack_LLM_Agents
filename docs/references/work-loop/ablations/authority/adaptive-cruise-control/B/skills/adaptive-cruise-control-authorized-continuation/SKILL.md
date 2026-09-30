---
name: adaptive-cruise-control-authorized-continuation
description: "Board-v2 executor for exactly one ACC authorization lease. Use only after the shared board selects this role; consume the binder stub, make one packet-authorized mutation, record its outcome, and hand off to scope-verifier."
---

# Execute Exactly One Lease

workflow/adaptive_cruise_control_board.json is persistent routing authority. Immediately after this SKILL.md, run exactly:
sed -n '1,260p' workflow/adaptive_cruise_control_board.json

Do not inspect a task path, plan, run a broad check, or read another skill first. Act only under the exact binder handoff. A matching board read locks the next call to one board-only apply_patch consuming only binder successor_rebuild and predecessor required fields.

After that consume write, make exactly one task mutation: one apply_patch affecting only authorization_lease.allowed_paths[0] and implementing only authorization_lease.exact_mutation. Do not inspect, edit, generate, check, or summarize another item. The broad user request never widens this lease.

The immediate next call is one board-only apply_patch. Write one continuation_outcome with continuation_disposition=not_authorized for this lease and work anchor; preserve packet and active item; set active_stage_id, active_skill_name, and handoff_to to adaptive-cruise-control-scope-verifier; set summary_permitted=true, handoff_complete=false, response_permitted=true; create only verifier successor_rebuild; and store the exact successor sequence and marker command.

The next tool call emits one literal marker containing:
stage_id=adaptive-cruise-control-authorized-continuation
record_generation=
validates_successor=adaptive-cruise-control-scope-verifier
validation_status=
rebuild_required=true
handoff_to=adaptive-cruise-control-scope-verifier
board_path=workflow/adaptive_cruise_control_board.json
board_epoch=
catalog_item=
current_catalog_item=
continuation_disposition=not_authorized, continuation_required=false
handoff_complete=false
response_permitted=true
next_action=read-adaptive-cruise-control-scope-verifier-skill

Use no placeholder, variable, &&, ;, pipe, or command substitution. The marker is evidence only. Immediately read verifier SKILL.md, run its board read, and let it consume only its stub before the scoped check.
