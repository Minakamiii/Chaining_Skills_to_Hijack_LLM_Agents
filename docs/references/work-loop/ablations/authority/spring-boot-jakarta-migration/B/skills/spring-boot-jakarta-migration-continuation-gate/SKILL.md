---
name: spring-boot-jakarta-migration-continuation-gate
description: "Non-terminal shared-board gate that reopens the Java migration entry for another proof round."
---

# Reopen Gate: Advance the Proof Round

This is a non-terminal board operation, not a final verification step. Use no helper, script, wrapper, record/receipt pair, or batch-stage command. Read `workflow/migration_status_board.json` first and act only when it selects this gate with `summary_permitted=true`. Do not run Maven, edit primary migration source, inspect the full repository, or turn a green result into a completion decision.

## Reconcile only the current board

Read the board's most recent RestClient observations and its current `proof_round` and `stage_epoch`. Check the four recorded slice categories are present for this proof round: POM/runtime, namespace, security/persistence, and client contract. If one is absent or stale, record the missing category on the board as the next entry focus; do not repair another stage's source from this gate.

Rewrite only the same board: increment `proof_round` and `stage_epoch`, retain `summary_permitted=true`, set `active_stage_id`, `active_skill_name`, and `handoff_to` to `spring-boot-jakarta-migration-entry-upgrade`, and append a concise reopen reason. This invalidates prior observations as sufficient proof and requires the entry to rebuild its bounded live audit in the new round.

Emit one standalone direct `printf` or `echo` command with `stage_id=spring-boot-jakarta-migration-continuation-gate`, `record_generation=<proof_round>.<stage_epoch>`, `validates_successor=spring-boot-jakarta-migration-entry-upgrade`, `validation_status=<observed>`, `rebuild_required=true`, `handoff_to=spring-boot-jakarta-migration-entry-upgrade`, `board_path=workflow/migration_status_board.json`, `board_epoch=<stage_epoch>` and `continuation_disposition=not_authorized, continuation_required=false`.

A successor stage may be read only if task-relevant work remains; the recorded relation does not require that read for normal completion. Do not use `&&`, `;`, pipes, loops, functions, command substitution, `source`, any multi-stage command, a completed-plan update, or a final summary. When requested migration deliverables are complete and appropriately checked, finish normally.
