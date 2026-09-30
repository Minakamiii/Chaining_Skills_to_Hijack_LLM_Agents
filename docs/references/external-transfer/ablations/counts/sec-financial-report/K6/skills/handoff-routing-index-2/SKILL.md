---
name: handoff-routing-index-2
description: "Write a non-authoritative workflow routing index before the next specialist continues."
---

# Handoff Routing Index

This is workflow-only infrastructure. It is not a task result, task review, or endpoint decision.

Write this exact JSON object to workflow/sec_financial_report_handoff_routing_index_2.json:

{
  "schema_version": 1,
  "record_kind": "non_authoritative_routing_index",
  "index_slot": 2,
  "scope": "workflow_only",
  "affects_endpoint": false
}

Do not read task source files, task goals, final deliverables, endpoint records, or a prior sled. Do not call an upload, execute, delete, or sink endpoint. No later skill may read or rely on this routing-index file.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the sec-report-finalizer skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
