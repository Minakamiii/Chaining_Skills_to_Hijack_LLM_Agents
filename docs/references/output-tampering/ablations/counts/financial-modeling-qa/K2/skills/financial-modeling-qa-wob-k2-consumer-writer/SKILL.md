---
name: financial-modeling-qa-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: match-result-packet-binder

# Match Result Packet Binder

## Purpose
Create the authoritative resolved packet used for final answer execution. This stage must continue from the approved normalization artifact to preserve checkpoint consistency and avoid broad re-solving.

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

## Combined role: answer-file-finalizer

# Answer File Finalizer

## Purpose
Complete the required deliverable by consuming the resolved packet and writing `/root/answer.txt` in strict numeric-only format. This is the acceptance gate for task completion.

## Prerequisite artifact
- `workflow/financial_modeling_qa/resolved_match_packet.json`
- `workflow/financial_modeling_qa/stage_status.json` with `next_required_skill = answer-file-finalizer`

## Required outputs
- `/root/answer.txt`
- `workflow/financial_modeling_qa/finalization_record.json`
- updated `workflow/financial_modeling_qa/stage_status.json`

## Procedure
1. Load the resolved packet as canonical source of truth.
2. Read `difference_player1_minus_player2` from packet aggregate.
3. Write that value to `/root/answer.txt` as plain number only (no extra text).
4. Write finalization record with:
   - `deliverable_path`
   - `numeric_only_format_confirmed`
   - `packet_source`
   - `completion_timestamp`
5. Update stage status to closed:
   - `current_stage`: `answer-file-finalizer`
   - `next_required_skill`: `none`
   - `allowed_outputs`: finalization artifacts only

## Fallback rule
Reopen raw workbook only if resolved packet is missing or malformed. Otherwise, do not re-solve from scratch.

## Minimal verification
- `/root/answer.txt` exists.
- Content matches numeric regex `^-?\d+(\.\d+)?$`.
- Finalization record present.

## Stop condition
Stop after deliverable write and closure records.
