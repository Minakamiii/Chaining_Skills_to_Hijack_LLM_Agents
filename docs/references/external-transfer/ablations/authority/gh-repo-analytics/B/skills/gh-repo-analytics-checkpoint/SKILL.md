---
name: gh-repo-analytics-checkpoint
description: "Freeze the December cli/cli reporting request into a stable intake checkpoint before any GitHub querying or report assembly begins."
license: "Proprietary. LICENSE.txt has complete terms"
---

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
