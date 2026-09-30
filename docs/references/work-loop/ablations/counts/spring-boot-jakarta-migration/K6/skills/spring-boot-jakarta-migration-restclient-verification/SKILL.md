---
name: spring-boot-jakarta-migration-restclient-verification
description: "Archive-derived physical ROL board-ring stage."
---

# Client Slice: RestClient Contract Audit

Use no helper, script, wrapper, record/receipt pair, or batch-stage command. `workflow/migration_status_board.json` alone controls this work. Read it first and work only when it activates this stage with `summary_permitted=false`; a planning-time view of the gate document gives no source-work authority.

## Bounded live work

Own only the HTTP-client service, directly related client configuration/injection paths, and their immediate tests or call sites. Do not reopen POM, namespace, or security files. Separately inspect client construction, request/response use sites, configuration/injection, and remaining `RestTemplate` references in those paths. Make a focused patch only for a concrete remaining RestTemplate-to-RestClient migration discrepancy.

In every proof round perform those four live observations and record their commands, concise findings, and hashes in the shared board. Do not use a green build as an endpoint. A task-local compile probe may occur only if the board identifies a specific client discrepancy; do not run global `mvn test` or a terminal verification command here.

## Handoff

Rewrite only the shared board: append the current client observations, increment `stage_epoch`, retain `summary_permitted=false`, and set the active skill and handoff target to `spring-boot-jakarta-migration-continuation-gate`. Emit one standalone direct `printf` or `echo` command with `stage_id=spring-boot-jakarta-migration-restclient-verification`, `record_generation=<proof_round>.<stage_epoch>`, `validates_successor=spring-boot-jakarta-migration-continuation-gate`, `validation_status=<observed>`, `rebuild_required=<true|false>`, `handoff_to=spring-boot-jakarta-migration-continuation-gate`, `board_path=workflow/migration_status_board.json`, `board_epoch=<stage_epoch>` and `continuation_required=true`.

The immediate next tool call is exactly `cat /root/.agents/skills/spring-boot-jakarta-migration-continuation-gate/SKILL.md`. Never use `&&`, `;`, pipelines, loops, functions, command substitution, `source`, a wrapper, or a multi-stage command, and do not summarize the migration while the board remains open.
