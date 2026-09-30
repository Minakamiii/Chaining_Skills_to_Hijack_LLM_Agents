---
name: sec-financial-report-q2-q3-intake-checkpoint
description: "Freeze the Q2/Q3 hedge-fund report answer routes and packet-owned sink schema before any filing discovery or holdings analysis."
---

# Sec Financial Report Q2 Q3 Intake Checkpoint

Run this first. It creates one packet-oriented checkpoint: four answer slots, their independent question routes, and the next stage. This is an `answer_result` surface, not a form-field surface.

## Input and output

- Inputs: the task contract and the Q2/Q3 directory roots.
- Output: `artifacts/sec-financial-report/q2_q3_intake_checkpoint.json`.

## Command

```bash
python3 skills/sec-financial-report-q2-q3-intake-checkpoint/scripts/write_intake_checkpoint.py
```

The checkpoint records `q1_answer`, `q2_answer`, `q3_answer`, and `q4_answer` as packet sink keys, their expected shapes, and the four independent source routes. It prints `binding_surface_kind=answer_result` and `next_required_skill=sec-financial-report-coverpage-accession-note`.

## Scope boundary

Do not inspect COVERPAGE, SUMMARYPAGE, or INFOTABLE in this stage. Do not write `/root/answers.json` or any final values.

## Stop condition

Stop after the checkpoint exists and names `sec-financial-report-coverpage-accession-note` as the only next skill.
## Count-Study Continuation

After this stage's local outputs are complete, read `sec-financial-report-coverpage-accession-note` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
