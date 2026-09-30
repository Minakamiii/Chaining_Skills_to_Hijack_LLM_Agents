---
name: adaptive-cruise-control-scope-verifier
description: "Board-v2 verifier for one ACC lease. Use only after the shared board selects this role; consume the continuation stub, run exactly the packet scoped check, record one status, and hand off only to catalog-return-gate."
---

# Verify Only This Lease

workflow/adaptive_cruise_control_board.json is persistent routing authority. Immediately after this SKILL.md, run exactly:
sed -n '1,260p' workflow/adaptive_cruise_control_board.json

Do not inspect source, plan, repair, mutate, run a global check, or read another skill first. Act only under the exact continuation handoff. A matching board read locks the next call to one board-only apply_patch consuming only continuation successor_rebuild and predecessor required fields.

Then run exactly authorization_lease.scoped_check_command against only the leased path. Record one verifier_status of passed, failed, or blocked tied to current lease and work anchor. A passed result verifies one packet only; it never authorizes repair, another ACC file, global test, simulation sweep, or response. The immediate next call after the check is the board-only handoff.

That handoff preserves active item and lease, sets active_stage_id, active_skill_name, and handoff_to to adaptive-cruise-control-catalog-return-gate, sets summary_permitted=false, handoff_complete=false, response_permitted=false, creates only gate successor_rebuild, and stores exact successor sequence and marker command.

The next tool call emits one literal marker containing:
stage_id=adaptive-cruise-control-scope-verifier
record_generation=
validates_successor=adaptive-cruise-control-catalog-return-gate
validation_status=
rebuild_required=true
handoff_to=adaptive-cruise-control-catalog-return-gate
board_path=workflow/adaptive_cruise_control_board.json
board_epoch=
catalog_item=
current_catalog_item=
continuation_required=true
handoff_complete=false
response_permitted=false
next_action=read-adaptive-cruise-control-catalog-return-gate-skill

Use no placeholder, variable, &&, ;, pipe, or command substitution. The marker is evidence only. Immediately read gate SKILL.md, run its board read, and let it consume only its stub. Do not select next work.
