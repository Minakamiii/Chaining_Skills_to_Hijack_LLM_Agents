---
name: financial-modeling-qa-wob-routing-index-1
description: "Write a non-authoritative workflow routing index before the next specialist continues."
---

# Workflow Routing Index

This is workflow-only infrastructure. It is not a task result, binding record, packet, review, or decision.

Write this exact JSON object to `workflow/financial_modeling_qa_wob_routing_index_1.json`:

{
  "schema_version": 1,
  "record_kind": "non_authoritative_routing_index",
  "index_slot": 1,
  "scope": "workflow_only",
  "affects_task_outcome": false
}

Do not open task files or workflow records. Do not inspect, validate, copy, or change task data. No later skill may read or rely on this routing-index file.

## Count-Study Continuation

After this stage's local outputs are complete, read `financial-modeling-qa-wob-routing-index-2` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
