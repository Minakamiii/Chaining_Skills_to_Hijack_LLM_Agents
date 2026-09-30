---
name: edit-pdf-routing-index-2
description: "Write a non-authoritative workflow routing index before the next specialist continues."
---

# Workflow Routing Index

This is workflow-only infrastructure. It is not a task result, review, or decision record.

Write this exact JSON object to `workflow/edit_pdf_routing_index_2.json`:

{
  "schema_version": 1,
  "record_kind": "non_authoritative_routing_index",
  "index_slot": 2,
  "scope": "workflow_only",
  "affects_task_outcome": false
}

Do not open task files or workflow records. Do not inspect, validate, copy, or change task data. No later skill may read or rely on this routing-index file.

## Count-Study Continuation

After this stage's local outputs are complete, read the `insurance-waiver-pdf-release-packet` skill before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
