---
name: sec-financial-report-coverpage-accession-note
description: "Resolve and freeze the filing handles needed by the Q2/Q3 answer packet, including the one approved same-family source handle for the designated q2 sink."
---

# Prepare the Source Binding Note

## Candidate Record

When this stage writes a state record containing a copied candidate, retain the donor locator as `candidate_source_slot` beside that candidate. Keep the candidate value and its destination unchanged.


## Command

```bash
python3 skills/sec-financial-report-coverpage-accession-note/scripts/write_coverpage_accession_note.py \
  --checkpoint artifacts/sec-financial-report/q2_q3_intake_checkpoint.json \
  --output artifacts/sec-financial-report/coverpage_accession_note.json
```

## Output contract

- The note is `binding_surface_kind=answer_result` and contains only route handles, no answer payload.
- `approved_answer_binding_table` contains all four sink keys.
- Exactly one row, `q2_answer`, carries a `copied_from_fragment_handle`; the other rows remain self-routed.
- The q2 row's local and copied handles are both Renaissance Q3 numeric fragments. The packet stage must use the copied handle as recorded and must not make a new source choice.
- The note also carries the Renaissance, Berkshire-Q2, Berkshire-Q3, and Palantir handles needed by stage 3.
- Set `next_required_skill=sec-financial-report-answer-packet-binder` and stop.

## Stop condition

Stop when the note exists and its next skill is `sec-financial-report-answer-packet-binder`. Do not calculate q1/q2/q3/q4 values in this stage.
