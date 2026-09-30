---
name: game-match-checkpoint
description: "Freeze the financial data analysis request into a stable intake checkpoint before any workbook analysis or PDF extraction begins."
---

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
## Routing-Depth Continuation

After this stage's local outputs are complete, read the game-match-scope skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
