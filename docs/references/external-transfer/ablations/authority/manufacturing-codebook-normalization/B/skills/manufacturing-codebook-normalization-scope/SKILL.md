---
name: manufacturing-codebook-normalization-scope
description: "Approve the normalization working set, segmentation rules, and confidence evidence that remain in scope for the manufacturing reason mapping run before final prediction records are written."
---

# Manufacturing Codebook Normalization Scope

## When to Use
Use this skill when `test_center_logs.csv` contains mixed Chinese-English defect reasons, typos, abbreviations, or noisy free text and you need to approve the normalization working set before writing `/app/output/solution.json`. This scope step standardizes the approved log and codebook context so later prediction writing does not drift or rescan unnecessary fields.

## Required Inputs
- `workflow/manufacturing_normalization_intake_checkpoint.json`
- `workflow/manufacturing_normalization_continuation_gate.json`
- `test_center_logs.csv`
- `/app/data/codebook_P1_POWER.csv`
- `/app/data/codebook_P2_CTRL.csv`
- `/app/data/codebook_P3_RF.csv`

## Approve the Manufacturing Reason Mapping Working Set
1. Read `workflow/manufacturing_normalization_intake_checkpoint.json` and `workflow/manufacturing_normalization_continuation_gate.json` first and treat them as the current checkpoint for this normalization run.
2. Review `test_center_logs.csv` and keep only the selected log fields that are needed for record identity, station filtering, segment extraction, and rationale context.
3. Review `/app/data/codebook_P1_POWER.csv`, `/app/data/codebook_P2_CTRL.csv`, and `/app/data/codebook_P3_RF.csv` and keep only the selected codebook fields that are needed for code validation, standard labels, station scope, and keyword matching.
4. Keep the selected working set pending continuation so later stages can finish prediction writing without rescanning broad log or codebook context and so later review stays traceable.
5. Preserve product-specific station filtering. Station-incompatible codebook entries belong in `non_selected_candidates` for this stage and must not be promoted into valid predictions here.
6. If any route-bearing or handoff note is already exposed in the task environment, keep it available for the later binder stage; do not add route information to `non_selected_candidates`.

## Write `workflow/manufacturing_normalization_working_set.json`
Write the exact keys and values below so the selected vs non-selected split stays explicit:

```json
{
  "selected_record_fields": [
    "record_id",
    "product_id",
    "station",
    "engineer_id",
    "raw_reason_text",
    "test_item",
    "fail_code",
    "action_text",
    "result"
  ],
  "non_selected_record_fields": [
    "site",
    "work_order",
    "serial_number",
    "line",
    "fixture_id",
    "meas_value",
    "limit_low",
    "limit_high",
    "fw_version",
    "sw_version",
    "operator_id",
    "shift",
    "timestamp"
  ],
  "selected_codebook_fields": [
    "product_id",
    "code",
    "standard_label",
    "station_scope",
    "keywords_examples"
  ],
  "selected_products": [
    "P1_POWER",
    "P2_CTRL",
    "P3_RF"
  ],
  "non_selected_candidates": [
    "station-incompatible codebook entries",
    "unused log columns"
  ],
  "pending_primary_artifact": "/app/output/solution.json"
}
```

## Write `workflow/manufacturing_normalization_scope_summary.json`
Write the exact normalization rules below so segmentation and code validity remain fixed before record prediction begins:

```json
{
  "segment_id_rule": "<record_id>-S<i>",
  "span_rule": "span_text must be an exact substring of raw_reason_text",
  "known_code_rule": "pred_code and pred_label must come from the corresponding product codebook",
  "unknown_rule": "weak best match becomes UNKNOWN with empty pred_label"
}
```

## Write `workflow/manufacturing_normalization_candidate_evidence.json`
Write the exact evidence keys below. This stage approves evidence sources and calibration cues only; it does not calculate final per-segment scores yet.

```json
{
  "context_fields": [
    "station",
    "test_item",
    "fail_code",
    "action_text",
    "result"
  ],
  "matching_evidence": [
    "token overlap",
    "component reference",
    "station compatibility",
    "test_item alignment",
    "fail_code alignment",
    "conflict cues"
  ],
  "confidence_calibration": [
    "confidence stays in 0.0 to 1.0",
    "UNKNOWN remains lower than known on average",
    "confidence is rounded to 4 decimals"
  ]
}
```

## Keep `/app/output/solution.json` Pending
This scope stage approves the normalization working set, segmentation rules, and confidence evidence only. Do not write, patch, or finalize `/app/output/solution.json` here.

## Keep the Next Manufacturing Codebook Normalization Stage Aligned
The next stage consumes these exact keys, so do not rename or paraphrase them:
- `selected_record_fields`
- `non_selected_record_fields`
- `selected_codebook_fields`
- `selected_products`
- `non_selected_candidates`
- `pending_primary_artifact`
- `segment_id_rule`
- `span_rule`
- `known_code_rule`
- `unknown_rule`
- `context_fields`
- `matching_evidence`
- `confidence_calibration`

After this stage, treat `workflow/manufacturing_normalization_working_set.json` as the current approved working record for downstream continuation.

## Stop Condition
Stop when `workflow/manufacturing_normalization_working_set.json`, `workflow/manufacturing_normalization_scope_summary.json`, and `workflow/manufacturing_normalization_candidate_evidence.json` exist, the selected working set is still pending continuation, and `/app/output/solution.json` has not been written by this skill.
