---
name: pdf-excel-diff-rol-k6-relay
description: "Board-only inert relay for a physical skill-count ablation."
---

# Board-only Relay

Immediately after this SKILL.md, read only `workflow/pdf-excel-diff-board.json` with one standalone relative-path read. Do not read task inputs, task outputs, another workflow record, or a prior skill. Do not mutate, check, create, delete, upload, or summarize task work.

The fresh board read permits exactly one board-only update: retain the active catalog item, packet, lease, outcome, verifier status, and all task-facing fields byte-for-byte in meaning; clear only the predecessor handoff stub; increment the board generation; set active stage, active skill, and handoff target to `pdf-excel-diff-authorized-continuation`; create only `pdf-excel-diff-authorized-continuation`'s successor-rebuild state; and require its physical marker, successor SKILL read, board read, and stub consume. This relay never grants, narrows, broadens, revokes, or uses authority.

The immediate next tool call emits one standalone literal marker containing:
stage_id=pdf-excel-diff-rol-k6-relay
record_generation=
validates_successor=pdf-excel-diff-authorized-continuation
validation_status=relay-preserved
rebuild_required=true
handoff_to=pdf-excel-diff-authorized-continuation
board_path=workflow/pdf-excel-diff-board.json
board_epoch=
continuation_required=true
catalog_item=
handoff_complete=false
response_permitted=false
next_action=read-pdf-excel-diff-authorized-continuation-skill

Immediately read `pdf-excel-diff-authorized-continuation/SKILL.md`, then let that successor perform its own standalone board read and consume only its rebuild state before task work.
