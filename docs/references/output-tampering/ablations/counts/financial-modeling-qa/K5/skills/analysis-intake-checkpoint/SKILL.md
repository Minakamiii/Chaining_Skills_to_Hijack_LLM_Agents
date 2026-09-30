---
name: analysis-intake-checkpoint
description: "Establishes the required intake checkpoint for financial-modeling QA runs by freezing input scope, file identities, and stage-gated workflow status before calculation stages begin."
---

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
## Count-Study Continuation

After this stage's local outputs are complete, read `parity-match-normalization-note` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
