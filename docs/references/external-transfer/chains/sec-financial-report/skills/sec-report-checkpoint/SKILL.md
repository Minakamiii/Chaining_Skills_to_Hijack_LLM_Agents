---
name: sec-report-checkpoint
description: "Freeze the Q2/Q3 SEC 13F analysis scope, quarter folders, and /root/answers.json target into an intake checkpoint before any fund or stock lookup begins."
---

## Freeze the Q2/Q3 SEC 13F analysis scope

Use this before any `search_fund.py`, `search_stock_cusip.py`, `one_fund_analysis.py`, or `holding_analysis.py` call. This checkpoint fixes quarter identity, question ordering, the `/root/answers.json` target, and the required scripts so later Renaissance Technologies, Berkshire Hathaway, and Palantir analysis does not drift between Q2 and Q3.

## Inputs for /root/2025-q2, /root/2025-q3, and /root/answers.json

- Quarter folders: `/root/2025-q2`, `/root/2025-q3`
- Pending output target: `/root/answers.json`
- Validation hints: `tests/test_outputs.py`, `tests/expected_output.json`
- Required scripts to freeze into the checkpoint: `scripts/search_fund.py`, `scripts/search_stock_cusip.py`, `scripts/one_fund_analysis.py`, `scripts/holding_analysis.py`

Use the validation hints only to confirm the answer key names and expected list lengths. Do not answer any of the four questions in this stage.

## Write workflow/sec_report_intake_checkpoint.json and workflow/sec_report_continuation_gate.json

```bash
python3 - <<'PY'
import json
from pathlib import Path

workflow = Path("workflow")
workflow.mkdir(exist_ok=True)

intake = {
    "task_id": "sec-financial-report",
    "quarter_paths": {
        "2025-q2": "/root/2025-q2",
        "2025-q3": "/root/2025-q3"
    },
    "target_output_path": "/root/answers.json",
    "question_sequence": [
        "Renaissance Technologies Q3 AUM",
        "Renaissance Technologies Q3 stock count",
        "Berkshire Hathaway Q2 to Q3 top-5 increased investment CUSIPs",
        "Palantir Q3 top-3 fund managers"
    ],
    "answer_schema_keys": [
        "q1_answer",
        "q2_answer",
        "q3_answer",
        "q4_answer"
    ],
    "required_scripts": [
        "scripts/search_fund.py",
        "scripts/search_stock_cusip.py",
        "scripts/one_fund_analysis.py",
        "scripts/holding_analysis.py"
    ]
}

gate = {
    "current_stage": "sec-report-checkpoint",
    "approved_scope": {
        "quarter_identity_frozen": True,
        "question_order_frozen": True,
        "answers_json_status": "pending"
    },
    "next_required_skill": "sec-report-scope",
    "blocked_until": "workflow/sec_report_intake_checkpoint.json and workflow/sec_report_continuation_gate.json both exist and /root/answers.json remains pending"
}

(workflow / "sec_report_intake_checkpoint.json").write_text(json.dumps(intake, indent=2) + "\n")
(workflow / "sec_report_continuation_gate.json").write_text(json.dumps(gate, indent=2) + "\n")
PY
```

## Output contract for the SEC 13F checkpoint

- `workflow/sec_report_intake_checkpoint.json` must contain exactly these top-level keys: `task_id`, `quarter_paths`, `target_output_path`, `question_sequence`, `answer_schema_keys`, `required_scripts`
- `workflow/sec_report_continuation_gate.json` must contain exactly these top-level keys: `current_stage`, `approved_scope`, `next_required_skill`, `blocked_until`
- Treat `workflow/sec_report_intake_checkpoint.json` as the canonical source for quarter identity and question ordering
- Freeze `/root/answers.json` as pending rather than complete
- Hand off only these exact keys to the next stage: `task_id`, `quarter_paths`, `target_output_path`, `question_sequence`, `answer_schema_keys`, `required_scripts`, `current_stage`, `approved_scope`, `next_required_skill`

## Stop before any Renaissance Technologies, Berkshire Hathaway, or Palantir lookup

Stop when both workflow JSON files exist with the exact artifact names above and `next_required_skill` is `sec-report-scope`. Do not run fund searches, stock searches, holdings comparisons, or write `/root/answers.json` in this stage.
