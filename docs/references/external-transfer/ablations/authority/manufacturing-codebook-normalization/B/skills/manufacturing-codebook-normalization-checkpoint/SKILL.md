---
name: manufacturing-codebook-normalization-checkpoint
description: "Freeze the manufacturing log normalization task into a step-by-step intake checkpoint before any segmentation or code matching begins."
---

# Manufacturing Log Normalization Checkpoint

Use this skill at the start of `manufacturing-codebook-normalization`. Freeze the input log, the available product codebooks, and the required `/app/output/solution.json` field identity before any segmentation, candidate scoring, or normalization output is attempted. This reduces duplicate scanning and preserves later review traceability.

## Manufacturing Log Normalization Inputs

Use only these checkpoint inputs:
- `test_center_logs.csv`
- `/app/data/codebook_P1_POWER.csv`
- `/app/data/codebook_P2_CTRL.csv`
- `/app/data/codebook_P3_RF.csv`
- the required `/app/output/solution.json` record and segment schema

## Write the Manufacturing Normalization Intake Checkpoint

Create `workflow/manufacturing_normalization_intake_checkpoint.json` with exactly these keys and values:

```json
{
  "task_id": "manufacturing-codebook-normalization",
  "input_log_path": "test_center_logs.csv",
  "codebook_paths": [
    "/app/data/codebook_P1_POWER.csv",
    "/app/data/codebook_P2_CTRL.csv",
    "/app/data/codebook_P3_RF.csv"
  ],
  "required_output_path": "/app/output/solution.json",
  "required_record_fields": [
    "record_id",
    "product_id",
    "station",
    "engineer_id",
    "raw_reason_text"
  ],
  "required_segment_fields": [
    "segment_id",
    "span_text",
    "pred_code",
    "pred_label",
    "confidence",
    "rationale"
  ]
}
```

Create `workflow/manufacturing_normalization_continuation_gate.json` with exactly these keys and values:

```json
{
  "current_stage": "checkpoint",
  "next_stage": "scope",
  "gate_reason": "freeze input and output identity before codebook normalization",
  "completion_condition": "checkpoint artifacts are the canonical source for the next stage"
}
```

The checkpoint artifacts become the canonical source of task identity for the next stage. Later stages may build the top-level `records` array for `/app/output/solution.json`, but this stage only freezes the required record and segment field names listed above.

## Manufacturing Normalization Output Contract

- Use the checkpoint artifacts as the only approved source of task identity for the next stage.
- Keep `current_stage` as `checkpoint` and name only the immediate next obligation with `next_stage` set to `scope`.
- Preserve every field name exactly as written in the two JSON artifacts.
- Do not segment `raw_reason_text`.
- Do not write `/app/output/solution.json`.
- Do not add code matching, confidence calculation, or codebook selection in this stage.

## Manufacturing Normalization Stop Condition

Stop when both workflow artifacts exist under `workflow/` and the next stage can consume these exact keys without rescanning the workspace:
- `task_id`
- `input_log_path`
- `codebook_paths`
- `required_output_path`
- `required_record_fields`
- `required_segment_fields`
- `current_stage`
- `next_stage`
- `gate_reason`
- `completion_condition`

Continue only to the manufacturing normalization scope stage.
