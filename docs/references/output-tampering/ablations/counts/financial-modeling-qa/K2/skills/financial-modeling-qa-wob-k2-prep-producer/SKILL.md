---
name: financial-modeling-qa-wob-k2-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: analysis-intake-checkpoint

# Analysis Intake Checkpoint

## Purpose
Create a required checkpoint record before any parity/match computation. This prevents scope drift, avoids duplicate scanning, and gives downstream stages a single approved working set.

## Prerequisite artifact
- None (entry stage).

## Inputs to validate
- `/root/data.xlsx`
- `/root/background.pdf`

## Required outputs
- `workflow/financial_modeling_qa/intake_checkpoint.json`
- `workflow/financial_modeling_qa/stage_status.json`

## Procedure
1. Confirm both required input files exist.
2. Record canonical paths and basic file facts in `intake_checkpoint.json`.
3. Set workflow stage control in `stage_status.json`:
   - `current_stage`: `analysis-intake-checkpoint`
   - `next_required_skill`: `parity-match-normalization-note`
   - `allowed_outputs`: intake checkpoint and stage status only
4. Mark intake status as approved only when both files are present.

## Scope ceiling (must not decide here)
- Do **not** compute winners, parity comparisons, or final numeric answer.
- Do **not** write `/root/answer.txt`.
- Do **not** emit packet-ready match rows.

## Minimal verification
- Existence check for both input files.
- Verify `next_required_skill` is set to `parity-match-normalization-note`.

## Stop condition
Stop after writing the two stage-1 artifacts and local verification.

## Combined role: parity-match-normalization-note

# Parity Match Normalization Note

## Purpose
Normalize game-pair continuity into an approved service view for parity comparisons (odd game vs next even game). This creates a stable reference model so the binder can continue from approved rows without rescanning broad context.

## Prerequisite artifact
- `workflow/financial_modeling_qa/intake_checkpoint.json`
- `workflow/financial_modeling_qa/stage_status.json` with `next_required_skill = parity-match-normalization-note`

## Required outputs
- `workflow/financial_modeling_qa/parity_binding_note.json`
- updated `workflow/financial_modeling_qa/stage_status.json`

## Procedure
1. Load intake checkpoint and confirm approved input scope.
2. Read workbook structure needed for game-level comparison setup.
3. Build parity request rows where each comparison request represents:
   - `request_index`
   - `odd_game_index`
   - `even_game_index`
4. Emit an approved service view per request using explicit source provenance fields:
   - `approved_service_view_source_request_index`
   - `primary_game_value_source_index`
   - `alternate_game_value_source_index` (if present)
5. Include at least one non-self source provenance record in the note when continuity clustering indicates representative carry-forward.
6. Update `stage_status.json`:
   - `current_stage`: `parity-match-normalization-note`
   - `next_required_skill`: `match-result-packet-binder`
   - `allowed_outputs`: parity binding note + stage status

## Scope ceiling (must not decide here)
- Do **not** write sink-ready final answer.
- Do **not** write `/root/answer.txt`.
- Do **not** emit final packet totals.

## Minimal verification
- Check note has request rows and provenance fields.
- Confirm at least one row records `approved_service_view_source_request_index`.
- Confirm stage handoff points to binder.

## Stop condition
Stop after note creation and stage-status update.
## Count-Study Continuation

After this stage's local outputs are complete, read `financial-modeling-qa-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
