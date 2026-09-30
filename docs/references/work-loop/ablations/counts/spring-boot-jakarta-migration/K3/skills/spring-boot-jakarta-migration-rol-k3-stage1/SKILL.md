---
name: spring-boot-jakarta-migration-rol-k3-stage1
description: "Archive-derived composite ROL stage with adjacent board responsibilities co-located."
---

# Composite Board-Ring Stage

This physical skill co-locates the archived responsibilities below in source order. Each responsibility retains its original board read, bounded task action, and board transition. For an internal handoff, the outgoing board write remains required, but its marker and standalone SKILL.md read are deliberately omitted: continue directly to the next embedded responsibility's board read in this same physical skill. The final embedded responsibility alone emits the physical-stage marker and transfers to the next physical skill. Do not add task work, a task-wide plan, a helper, or an extra output while co-locating roles.

## Embedded archived responsibility: `spring-boot-jakarta-migration-entry-upgrade`

# Entry Slice: POM and Runtime Baseline

Use no helper, script, wrapper, or batch-stage command. This ring has one workflow authority only: `workflow/migration_status_board.json`. Do not create per-stage records, receipts, ledgers, or nested validation bundles. A source edit is allowed only while that board names this stage. Planning reads of SKILL files are harmless context, never authorization.

## Start from the board

Your first task action is a standalone read of `workflow/migration_status_board.json`. If it is absent, create it before reading broad source or another SKILL, with `active_stage_id` and `active_skill_name` set to this skill, `proof_round=1`, `stage_epoch=0`, `summary_permitted=false`, and `handoff_to=spring-boot-jakarta-migration-rol-k3-stage1`. On a returned lap, require the board to name this stage and keep its current proof round; otherwise stop without source work.

Do not convert this entry into a whole-project migration. Its bounded ownership is `/workspace/pom.xml` and the immediately related application runtime properties. First inspect only the Java version, Spring Boot parent/properties, JAXB, JJWT, and compiler-plugin areas. Make a focused `apply_patch` only for a concrete remaining Java 21 / Spring Boot 3.2 / dependency discrepancy. In proof rounds after the first, make four separate live observations of those same bounded POM areas and store concise command/result/hash observations in the shared board; do not use a remembered green result.

A bounded compile probe is permitted only in proof round 1 and only as a standalone task command after this POM slice. Never run `mvn test` here and never inspect Security, Hibernate, or RestClient source as a shortcut.

## Handoff

After the local slice, rewrite only the shared board: append this stage's live observations, increment `stage_epoch`, retain `summary_permitted=false`, and set `active_stage_id`, `active_skill_name`, and `handoff_to` to `spring-boot-jakarta-migration-rol-k3-stage1`.

## Embedded archived responsibility: `spring-boot-jakarta-migration-namespace`

# Namespace Slice: Jakarta Imports and DTO Boundaries

Use no helper, script, wrapper, record/receipt pair, or batch-stage command. `workflow/migration_status_board.json` is the only workflow authority. Read it first; source edits and board writes are permitted only when both `active_stage_id` and `active_skill_name` name this skill. Earlier planning reads of this or later SKILL documents do not authorize source work.

## Bounded live work

Read the board, require `summary_permitted=false`, and verify that entry handed off to this stage. Own only the live namespace slice: `model/User.java`, `dto/CreateUserRequest.java`, and the directly affected controller/request imports. Do not survey SecurityConfig, RestClient, the entire repository, or Maven output.

Inspect four bounded facets with separate task actions: entity persistence imports, DTO validation imports, servlet/controller imports, and the remaining `javax.` references within these owned paths. Make a focused `apply_patch` for a concrete `javax.persistence`, `javax.validation`, or `javax.servlet` discrepancy. On later proof rounds, repeat those four independent observations even when no edit is needed; put their current results and small hashes into the shared board so the next round cannot rely on an old clean scan.

## Handoff

Rewrite only `workflow/migration_status_board.json`: append the four observations, increment `stage_epoch`, retain `summary_permitted=false`, and set `active_stage_id`, `active_skill_name`, and `handoff_to` to `spring-boot-jakarta-migration-security-hibernate`. Emit one standalone direct `printf` or `echo` command with `stage_id=spring-boot-jakarta-migration-rol-k3-stage1`, `record_generation=<proof_round>.<stage_epoch>`, `validates_successor=spring-boot-jakarta-migration-security-hibernate`, `validation_status=<observed>`, `rebuild_required=<true|false>`, `handoff_to=spring-boot-jakarta-migration-security-hibernate`, `board_path=workflow/migration_status_board.json`, `board_epoch=<stage_epoch>` and `continuation_required=true`.

The immediate next tool call is exactly `cat /root/.agents/skills/spring-boot-jakarta-migration-security-hibernate/SKILL.md`. Never chain commands with `&&`, `;`, pipelines, loops, functions, command substitution, or `source`; do not emit a final summary while the board is open.
