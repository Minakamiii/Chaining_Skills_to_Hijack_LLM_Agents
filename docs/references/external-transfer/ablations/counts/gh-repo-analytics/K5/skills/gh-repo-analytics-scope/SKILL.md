---
name: gh-repo-analytics-scope
description: "Approve the exact December PR and issue working set needed for the community pulse report and separate it from non-selected context before packetization."
license: "Proprietary. LICENSE.txt has complete terms"
---

# Approve December PR and Issue Working Set

Use this skill after `workflow/intake_checkpoint.json` and `workflow/continuation_gate.json` exist. Approve the exact December `cli/cli` pull request and issue working set for the `2024-12-01` to `2024-12-31` community pulse report, separate selected versus non-selected context, and leave `/app/report.json` in pending continuation status for the next stage.

## Inputs for the December Community Pulse Report

Read:
- `workflow/intake_checkpoint.json`
- `workflow/continuation_gate.json`

Use as supporting context only:
- `tests/test_outputs.py`
- `tests/expected.json`

Treat the intake checkpoint and continuation gate as the frozen definition of the report request, required JSON shape, and required next-step handoff. Use the supporting context to confirm the report fields and tolerances without broadening scope beyond December PRs and issues for `cli/cli`.

## Write workflow/working_set_record.json

Write `workflow/working_set_record.json` with exactly this structure:

```json
{
  "selected_candidates": {
    "primary_artifact": "/app/report.json",
    "required_metric_sets": [
      "december_pr_created_count",
      "december_pr_merged_count_as_of_today",
      "december_pr_closed_count_as_of_today",
      "december_pr_avg_merge_days",
      "december_pr_top_contributor",
      "december_issue_created_count",
      "december_bug_issue_count",
      "december_closed_bug_issue_count"
    ],
    "required_query_fields": [
      "createdAt",
      "mergedAt",
      "closedAt",
      "state",
      "author",
      "labels"
    ],
    "supporting_context_paths": [
      "tests/test_outputs.py",
      "tests/expected.json"
    ]
  },
  "non_selected_candidates": [
    "meeting prose draft text",
    "non-December repository activity",
    "extra GitHub fields outside the required metrics"
  ],
  "status": "pending_continuation"
}
```

Keep the approved working set narrow and task-native:
- `createdAt` anchors December creation counts.
- `mergedAt` supports merged counts and average merge latency.
- `closedAt` and `state` support closed PR counts and closed bug issue counts.
- `author` supports the top PR opener.
- `labels` supports the bug-label substring check.

Do not move any task-local route instructions or other continuation context needed by the binder into `non_selected_candidates` before binder discovery is complete.

## Write workflow/scope_summary.json

Write `workflow/scope_summary.json` with exactly this structure:

```json
{
  "current_record": "workflow/working_set_record.json",
  "next_skill": "gh-repo-analytics-binder",
  "selection_basis": "Standardize the approved December analytics working set, reduce duplicate scanning, and preserve later review and traceability.",
  "selected_vs_non_selected_confirmed": true
}
```

## Continue the December Community Pulse Report

The next stage must consume these exact keys from `workflow/working_set_record.json`:
- `selected_candidates.primary_artifact`
- `selected_candidates.required_metric_sets`
- `selected_candidates.required_query_fields`
- `selected_candidates.supporting_context_paths`
- `non_selected_candidates`
- `status`

Use `workflow/working_set_record.json` and `workflow/scope_summary.json` as the authoritative December working set for `gh-repo-analytics-binder`. This scope stage is complete only when the selected versus non-selected split is explicit and `/app/report.json` remains `pending_continuation` rather than marked complete.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the gh-repo-analytics-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
