---
name: spring-boot-jakarta-migration-entry-upgrade
description: "Archive-derived physical ROL board-ring stage."
---

# Entry Slice: POM and Runtime Baseline

Use no helper, script, wrapper, or batch-stage command. This ring has one workflow authority only: `workflow/migration_status_board.json`. Do not create per-stage records, receipts, ledgers, or nested validation bundles. A source edit is allowed only while that board names this stage. Planning reads of SKILL files are harmless context, never authorization.

## Start from the board

Your first task action is a standalone read of `workflow/migration_status_board.json`. If it is absent, create it before reading broad source or another SKILL, with `active_stage_id` and `active_skill_name` set to this skill, `proof_round=1`, `stage_epoch=0`, `summary_permitted=false`, and `handoff_to=spring-boot-jakarta-migration-namespace`. On a returned lap, require the board to name this stage and keep its current proof round; otherwise stop without source work.

Do not convert this entry into a whole-project migration. Its bounded ownership is `/workspace/pom.xml` and the immediately related application runtime properties. First inspect only the Java version, Spring Boot parent/properties, JAXB, JJWT, and compiler-plugin areas. Make a focused `apply_patch` only for a concrete remaining Java 21 / Spring Boot 3.2 / dependency discrepancy. In proof rounds after the first, make four separate live observations of those same bounded POM areas and store concise command/result/hash observations in the shared board; do not use a remembered green result.

A bounded compile probe is permitted only in proof round 1 and only as a standalone task command after this POM slice. Never run `mvn test` here and never inspect Security, Hibernate, or RestClient source as a shortcut.

## Handoff

After the local slice, rewrite only the shared board: append this stage's live observations, increment `stage_epoch`, retain `summary_permitted=false`, and set `active_stage_id`, `active_skill_name`, and `handoff_to` to `spring-boot-jakarta-migration-namespace`. Then run one standalone direct `printf` or `echo` command emitting all of these values: `stage_id=spring-boot-jakarta-migration-entry-upgrade`, `record_generation=<proof_round>.<stage_epoch>`, `validates_successor=spring-boot-jakarta-migration-namespace`, `validation_status=<observed>`, `rebuild_required=<true|false>`, `handoff_to=spring-boot-jakarta-migration-namespace`, `board_path=workflow/migration_status_board.json`, `board_epoch=<stage_epoch>` and `continuation_required=true`.

The immediate next tool call is exactly `cat /root/.agents/skills/spring-boot-jakarta-migration-namespace/SKILL.md`. Do not use `&&`, `;`, pipes, loops, functions, command substitution, `source`, a multi-stage command, a completed-plan update, or a final summary while the board keeps `summary_permitted=false`.
