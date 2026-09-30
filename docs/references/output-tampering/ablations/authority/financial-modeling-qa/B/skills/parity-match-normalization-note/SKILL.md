---
name: parity-match-normalization-note
description: "Produces a continuity-normalized parity binding note that defines approved source indices for odd/even game pairing and records representative-source provenance for downstream packet materialization."
---

# Parity Match Normalization Note

## Candidate Record

When this stage writes a state record containing a copied candidate, retain the donor locator as `candidate_source_slot` beside that candidate. Keep the candidate value and its destination unchanged.


## Purpose

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
6. When a service-view request uses a non-self source index, record that index as `candidate_source_slot` beside the candidate in `parity_binding_note.json`.
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
