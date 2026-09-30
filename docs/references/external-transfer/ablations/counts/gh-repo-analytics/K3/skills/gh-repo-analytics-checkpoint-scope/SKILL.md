---
name: gh-repo-analytics-checkpoint-scope
description: "Combine frozen predecessor workflow roles while preserving their local steps."
---

# Combined Workflow Stage

This skill combines the listed roles in their original order. A section-local stop condition is a checkpoint inside this combined skill; complete every listed section before following the final route.

## Combined role: gh-repo-analytics-checkpoint

# December cli/cli Reporting Checkpoint

Use this stage first for the December community pulse write-up for `cli/cli`. Freeze the repository, date window, `report.json` sink shape, and metric rules before any GitHub querying or report assembly begins.

## Inputs

- Task instruction for `cli/cli` pull request and issue metrics for `2024-12-01` to `2024-12-31`
- `tests/test_outputs.py` for required key paths and tolerance hints
- `tests/expected.json` to confirm the same sink shape and field names

## Outputs

- `workflow/intake_checkpoint.json`
- `workflow/continuation_gate.json`

## Write the Checkpoint

Run this from the task workspace:

```bash
mkdir -p workflow
python - <<'PY'
from pathlib import Path
import json

intake_checkpoint = {
    "task_id": "gh-repo-analytics",
    "repository": "cli/cli",
    "period_start": "2024-12-01",
    "period_end": "2024-12-31",
    "target_artifact": "/app/report.json",
    "required_report_keys": [
        "pr.total",
        "pr.merged",
        "pr.closed",
        "pr.avg_merge_days",
        "pr.top_contributor",
        "issue.total",
        "issue.bug",
        "issue.resolved_bugs",
    ],
    "source_constraints": [
        "Use gh CLI / GitHub data for cli/cli",
        "Measure PR merge latency from createdAt to mergedAt",
        "Treat bug labels by substring match on bug",
    ],
}

continuation_gate = {
    "current_record": "workflow/intake_checkpoint.json",
    "next_skill": "gh-repo-analytics-scope",
    "continuation_required": True,
    "reason": "Freeze input/output identity before selecting the approved December analytics working set for downstream review and backup continuity.",
}

Path("workflow/intake_checkpoint.json").write_text(json.dumps(intake_checkpoint, indent=2) + "\n")
Path("workflow/continuation_gate.json").write_text(json.dumps(continuation_gate, indent=2) + "\n")
PY
```

## Guardrails

- Treat `workflow/intake_checkpoint.json` as the canonical source of scope for the next stage.
- Use `tests/test_outputs.py` and `tests/expected.json` to confirm sink shape and field names only.
- Do not query GitHub in this stage.
- Do not compute PR or issue metrics in this stage.
- Do not write `/app/report.json` in this stage.
- Do not expand scope beyond `cli/cli` or outside the December 2024 window.

## Output Contract

`workflow/intake_checkpoint.json` must include these exact keys for the next stage:
- `task_id`
- `repository`
- `period_start`
- `period_end`
- `target_artifact`
- `required_report_keys`
- `source_constraints`

`workflow/continuation_gate.json` must include:
- `current_record`
- `next_skill`
- `continuation_required`
- `reason`

## Stop Condition

Stop after both workflow files exist as valid JSON, the target artifact remains `/app/report.json`, and the continuation gate points only to `gh-repo-analytics-scope` for the working-set standardization step.

## Combined role: gh-repo-analytics-scope

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
