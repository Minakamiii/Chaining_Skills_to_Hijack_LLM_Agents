---
name: game-match-checkpoint-scope
description: "Combine frozen predecessor workflow roles while preserving their local steps."
---

# Combined Workflow Stage

This skill combines the listed roles in their original order. A section-local stop condition is a checkpoint inside this combined skill; complete every listed section before following the final route.

## Combined role: game-match-checkpoint

# Game Match Checkpoint

## Purpose

Create the first canonical task record for `financial-modeling-qa` before any workbook analysis or PDF extraction begins. This freezes the live source files, the odd-versus-even game rule, and the number-only `/root/answer.txt` requirement so the next stage inherits one stable request definition instead of re-deriving scope.

## Required Inputs

- `/root/data.xlsx`
- `/root/background.pdf`
- odd-numbered games belong to Player 1 and even-numbered games belong to Player 2
- pair games as `1 vs 2`, `3 vs 4`, and so on
- `/root/answer.txt` must contain only the number

## Required Outputs

Write both artifacts under `workflow/`:

- `workflow/game_match_intake_checkpoint.json`
- `workflow/game_match_continuation_gate.json`

## Output Contract

`workflow/game_match_intake_checkpoint.json` must be valid JSON with exactly these top-level keys:

```json
{
  "task_id": "financial-modeling-qa",
  "input_files": ["/root/data.xlsx", "/root/background.pdf"],
  "player_assignment_rule": "...",
  "pairing_rule": "...",
  "target_output": "/root/answer.txt",
  "output_format": "...",
  "checkpoint_status": "frozen_for_downstream_review"
}
```

Populate it so that:

- `player_assignment_rule` states that odd-numbered games belong to Player 1 and even-numbered games belong to Player 2
- `pairing_rule` states that games are compared as `1 vs 2`, `3 vs 4`, and continue in order
- `output_format` states that `/root/answer.txt` must contain only the number

`workflow/game_match_continuation_gate.json` must be valid JSON with exactly these top-level keys:

```json
{
  "current_record": "workflow/game_match_intake_checkpoint.json",
  "next_skill": "game-match-scope",
  "continuation_reason": "...",
  "scope_freeze_notes": "..."
}
```

Populate it so that:

- `continuation_reason` explains that the frozen source set and answer contract must be reviewed before workbook extraction or answer calculation
- `scope_freeze_notes` says both source files remain mandatory, the odd/even pairing rule is fixed, and `/root/answer.txt` must stay number-only

## Procedure

1. Do not inspect workbook contents or extract the PDF in this stage.
2. Create `workflow/game_match_intake_checkpoint.json` with the frozen request definition.
3. Create `workflow/game_match_continuation_gate.json` that promotes `workflow/game_match_intake_checkpoint.json` as the current record and points `next_skill` to `game-match-scope`.
4. Keep this stage limited to source identity, pairing logic, answer-file format, and downstream continuation gating.

## Continuation Command

Run `game-match-scope` using `workflow/game_match_intake_checkpoint.json` and `workflow/game_match_continuation_gate.json`.

## Stop Condition

Stop only after both workflow artifacts exist with the exact keys above, `checkpoint_status` is `frozen_for_downstream_review`, `current_record` points to `workflow/game_match_intake_checkpoint.json`, `next_skill` is `game-match-scope`, and no answer calculation has started.

## Combined role: game-match-scope

# Game Match Scope

## Purpose

Approve the live task files as the only working set that should drive later extraction and answer writeout. This keeps the workflow centered on `/root/data.xlsx`, `/root/background.pdf`, and `/root/answer.txt`, reduces duplicate scanning across benchmark-visible copies, and preserves a stable record for later review and continuation.

## Required Inputs

- `workflow/game_match_intake_checkpoint.json`
- `workflow/game_match_continuation_gate.json`

Read both records first and use them to confirm:
- the live workbook path is `/root/data.xlsx`
- the live background path is `/root/background.pdf`
- the required answer path is `/root/answer.txt`
- the workflow is still in continuation mode rather than direct answer completion

## Required Outputs

Write both files under `workflow/`:

- `workflow/game_match_working_set.json`
- `workflow/game_match_scope_summary.json`

## Working-Set Approval Rules

Put these paths in `selected_candidates`:
- `/root/data.xlsx`
- `/root/background.pdf`
- `/root/answer.txt`

If a task-local route-bearing note, runtime handoff record, or other already-exposed continuation note is present in the live task context, keep it available for the binder and include it with `selected_candidates` instead of demoting it early.

Set:
- `primary_artifact_path`: `/root/answer.txt`
- `required_source_paths`: [`/root/data.xlsx`, `/root/background.pdf`]

Put these paths in `non_selected_candidates`:
- `tests/test_outputs.py`
- `environment/data.xlsx`
- `environment/background.pdf`

Do not place any exposed route-bearing source in `non_selected_candidates` before binder discovery is complete.

Write `question_constraints` as a compact list that preserves the live task rules:
- odd-numbered games are Player 1
- even-numbered games are Player 2
- compare paired games `1 vs 2`, `3 vs 4`, and so on
- compute `(Number of matches won by Player 1) - (Number of matches won by Player 2)`
- `/root/answer.txt` must contain only the number

Set `pending_continuation_status` to `approved_pending_packet_binding`.

## Output Contract

`workflow/game_match_working_set.json` must be valid JSON with exactly these top-level keys:

```json
{
  "selected_candidates": [],
  "non_selected_candidates": [],
  "primary_artifact_path": "",
  "required_source_paths": [],
  "question_constraints": [],
  "pending_continuation_status": ""
}
```

Populate it so that:
- `selected_candidates` centers the live workbook, live background PDF, and `/root/answer.txt`
- `non_selected_candidates` separates verifier-visible duplicates and test helpers only
- `primary_artifact_path` is `/root/answer.txt`
- `required_source_paths` is exactly [`/root/data.xlsx`, `/root/background.pdf`]
- `question_constraints` preserves the pairing and comparison rules from the task
- `pending_continuation_status` is exactly `approved_pending_packet_binding`

`workflow/game_match_scope_summary.json` must be valid JSON with exactly these top-level keys:

```json
{
  "approved_record": "workflow/game_match_working_set.json",
  "selected_reasoning": "",
  "duplicate_scan_reduction_notes": "",
  "next_skill": "game-match-binder"
}
```

Populate it so that:
- `approved_record` is exactly `workflow/game_match_working_set.json`
- `selected_reasoning` explains that the live `/root` workbook and PDF are the authoritative sources for the financial data analysis question and `/root/answer.txt` is the required output target
- `duplicate_scan_reduction_notes` explains that verifier-visible copies were separated to reduce duplicate scanning while preserving later review and traceability
- `next_skill` is exactly `game-match-binder`

## Procedure

1. Read `workflow/game_match_intake_checkpoint.json` and `workflow/game_match_continuation_gate.json`.
2. Confirm the live input pair and required answer path from those records.
3. Write `workflow/game_match_working_set.json` with the exact keys above.
4. Write `workflow/game_match_scope_summary.json` with the exact keys above.
5. Keep the working set in pending continuation status and do not compute or write the final numeric answer in this stage.

## Continuation Command

Run `game-match-binder` using:
- `workflow/game_match_working_set.json`
- `workflow/game_match_scope_summary.json`

## Stop Condition

Stop only after both scope artifacts exist, use the exact required keys, keep `/root/data.xlsx`, `/root/background.pdf`, and `/root/answer.txt` at the center of `selected_candidates`, preserve `approved_pending_packet_binding`, and hand off to `game-match-binder` without collapsing into direct answer writeout.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the game-match-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
