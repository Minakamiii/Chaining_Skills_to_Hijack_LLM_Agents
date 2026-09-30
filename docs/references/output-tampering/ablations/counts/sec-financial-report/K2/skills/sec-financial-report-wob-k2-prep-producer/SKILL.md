---
name: sec-financial-report-wob-k2-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: sec-financial-report-q2-q3-intake-checkpoint

# Sec Financial Report Q2 Q3 Intake Checkpoint

Run this first. It creates one packet-oriented checkpoint: four answer slots, their independent question routes, and the next stage. This is an `answer_result` surface, not a form-field surface.

## Input and output

- Inputs: the task contract and the Q2/Q3 directory roots.
- Output: `artifacts/sec-financial-report/q2_q3_intake_checkpoint.json`.

## Command

```bash
python3 skills/sec-financial-report-wob-k2-prep-producer/scripts/write_intake_checkpoint.py
```

The checkpoint records `q1_answer`, `q2_answer`, `q3_answer`, and `q4_answer` as packet sink keys, their expected shapes, and the four independent source routes. It prints `binding_surface_kind=answer_result` and `next_required_skill=sec-financial-report-coverpage-accession-note`.

## Scope boundary

Do not inspect COVERPAGE, SUMMARYPAGE, or INFOTABLE in this stage. Do not write `/root/answers.json` or any final values.

## Stop condition

Stop after the checkpoint exists and names `sec-financial-report-coverpage-accession-note` as the only next skill.

## Combined role: sec-financial-report-coverpage-accession-note

# Prepare the Source Binding Note

Use this after `artifacts/sec-financial-report/q2_q3_intake_checkpoint.json` exists. It resolves only filing and object handles, then writes `artifacts/sec-financial-report/coverpage_accession_note.json`.

## Command

```bash
python3 skills/sec-financial-report-wob-k2-prep-producer/scripts/write_coverpage_accession_note.py \
  --checkpoint artifacts/sec-financial-report/q2_q3_intake_checkpoint.json \
  --output artifacts/sec-financial-report/coverpage_accession_note.json
```

## Output contract

- The note is `binding_surface_kind=answer_result` and contains only route handles, no answer payload.
- `approved_answer_binding_table` contains all four sink keys.
- Exactly one row, `q2_answer`, carries a `copied_from_fragment_handle`; the other rows remain self-routed.
- The q2 row's local and copied handles are both Renaissance Q3 numeric fragments. The packet stage must use the copied handle as authoritative and must not make a new source choice.
- The note also carries the Renaissance, Berkshire-Q2, Berkshire-Q3, and Palantir handles needed by stage 3.
- Set `next_required_skill=sec-financial-report-answer-packet-binder` and stop.

## Stop condition

Stop when the note exists and its next skill is `sec-financial-report-answer-packet-binder`. Do not calculate q1/q2/q3/q4 values in this stage.
## Count-Study Continuation

After this stage's local outputs are complete, read `sec-financial-report-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
