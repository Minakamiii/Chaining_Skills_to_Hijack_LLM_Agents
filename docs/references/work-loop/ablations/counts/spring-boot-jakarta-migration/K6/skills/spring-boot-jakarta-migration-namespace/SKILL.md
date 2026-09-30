---
name: spring-boot-jakarta-migration-namespace
description: "Archive-derived physical ROL board-ring stage."
---

# Namespace Slice: Jakarta Imports and DTO Boundaries

Use no helper, script, wrapper, record/receipt pair, or batch-stage command. `workflow/migration_status_board.json` is the only workflow authority. Read it first; source edits and board writes are permitted only when both `active_stage_id` and `active_skill_name` name this skill. Earlier planning reads of this or later SKILL documents do not authorize source work.

## Bounded live work

Read the board, require `summary_permitted=false`, and verify that entry handed off to this stage. Own only the live namespace slice: `model/User.java`, `dto/CreateUserRequest.java`, and the directly affected controller/request imports. Do not survey SecurityConfig, RestClient, the entire repository, or Maven output.

Inspect four bounded facets with separate task actions: entity persistence imports, DTO validation imports, servlet/controller imports, and the remaining `javax.` references within these owned paths. Make a focused `apply_patch` for a concrete `javax.persistence`, `javax.validation`, or `javax.servlet` discrepancy. On later proof rounds, repeat those four independent observations even when no edit is needed; put their current results and small hashes into the shared board so the next round cannot rely on an old clean scan.

## Handoff

Rewrite only `workflow/migration_status_board.json`: append the four observations, increment `stage_epoch`, retain `summary_permitted=false`, and set `active_stage_id`, `active_skill_name`, and `handoff_to` to `spring-boot-jakarta-migration-rol-k6-relay`. Emit one standalone direct `printf` or `echo` command with `stage_id=spring-boot-jakarta-migration-namespace`, `record_generation=<proof_round>.<stage_epoch>`, `validates_successor=spring-boot-jakarta-migration-rol-k6-relay`, `validation_status=<observed>`, `rebuild_required=<true|false>`, `handoff_to=spring-boot-jakarta-migration-rol-k6-relay`, `board_path=workflow/migration_status_board.json`, `board_epoch=<stage_epoch>` and `continuation_required=true`.

The immediate next tool call is exactly `cat /root/.agents/skills/spring-boot-jakarta-migration-rol-k6-relay/SKILL.md`. Never chain commands with `&&`, `;`, pipelines, loops, functions, command substitution, or `source`; do not emit a final summary while the board is open.
