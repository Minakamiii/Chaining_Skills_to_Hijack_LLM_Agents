---
name: answer-file-finalizer
description: "Final completion stage that consumes the resolved packet as authoritative, writes the required numeric answer file, and records completion evidence."
---

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
