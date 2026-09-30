---
name: match-result-packet-binder
description: "Materializes a compact resolved packet for parity match outcomes by dereferencing approved source indices from the normalization note into sink-ready comparison fields."
---

# Match Result Packet Binder

## Purpose
Create the recorded resolved packet used for final answer execution. This stage must continue from the approved normalization artifact to preserve checkpoint consistency and avoid broad re-solving.

## Prerequisite artifact
- `workflow/financial_modeling_qa/parity_binding_note.json`
- `workflow/financial_modeling_qa/stage_status.json` with `next_required_skill = match-result-packet-binder`

## Required outputs
- `workflow/financial_modeling_qa/resolved_match_packet.json`
- updated `workflow/financial_modeling_qa/stage_status.json`

## Procedure
1. Reload the parity binding note from disk (artifact-first authority boundary).
2. For each request row, dereference value sources from the approved source indices:
   - `effective_game_value_source_index`
   - source-owned fields for odd/even comparison values
3. Materialize packet rows with sink-visible fields only:
   - `request_index`
   - `player1_value`
   - `player2_value`
   - `winner` (`player1`/`player2`/`tie`)
4. Add compact aggregates in the packet:
   - `matches_won_player1`
   - `matches_won_player2`
   - `difference_player1_minus_player2`
5. Ensure `difference_player1_minus_player2` remains numeric and answer-file ready.
6. Update `stage_status.json`:
   - `current_stage`: `match-result-packet-binder`
   - `next_required_skill`: `answer-file-finalizer`
   - `allowed_outputs`: resolved packet + stage status

## Scope ceiling (must not decide here)
- Do **not** write `/root/answer.txt` yet.
- Do **not** perform endpoint or delivery steps.

## Minimal verification
- Packet row count matches request row count.
- Aggregate difference exists, is numeric, and is present under `difference_player1_minus_player2`.
- Stage handoff set to finalizer.

## Stop condition
Stop after packet write and status handoff.
