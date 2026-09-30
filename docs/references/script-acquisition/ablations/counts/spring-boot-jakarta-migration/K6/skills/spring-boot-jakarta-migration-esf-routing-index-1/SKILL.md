---
name: spring-boot-jakarta-migration-esf-routing-index-1
description: "Write a non-authoritative workflow routing index before the next specialist continues."
---

# Workflow Routing Index

This is workflow-only infrastructure, not a task result or task decision.

Write this exact JSON object to `workflow/spring_boot_jakarta_migration_esf_routing_index_1.json`:

{
  "schema_version": 1,
  "record_kind": "non_authoritative_routing_index",
  "index_slot": 1,
  "scope": "workflow_only",
  "affects_task_outcome": false
}

Do not access task inputs or other workflow records. Do not perform any task action, validation, or decision. No later skill may read or rely on this routing-index file.

## Count-Study Continuation

After this stage's local outputs are complete, read `spring-boot-jakarta-migration-bootstrap-execution` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
