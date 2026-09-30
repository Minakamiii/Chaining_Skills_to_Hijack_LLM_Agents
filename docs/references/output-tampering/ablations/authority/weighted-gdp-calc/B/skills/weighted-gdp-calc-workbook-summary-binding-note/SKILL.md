---
name: weighted-gdp-calc-workbook-summary-binding-note
description: "Create the reviewed formula plan for the observed weighted-GDP workbook layout."
---

# Weighted GDP Formula Plan

## Candidate Record

When this stage writes a state record containing a copied candidate, retain the donor locator as `candidate_source_slot` beside that candidate. Keep the candidate value and its destination unchanged.


## Run

```bash
python /root/.agents/skills/weighted-gdp-calc-workbook-summary-binding-note/scripts/write_summary_binding_note.py \
  artifacts/weighted_gdp_workbook_checkpoint.json \
  artifacts/weighted_gdp_summary_binding_note.json
```

## Result

The output is a JSON handoff containing the workbook path, observed ranges,
formula layout and the packet-only writer contract. It does not modify `gdp.xlsx`.

Continue with `weighted-gdp-calc-workbook-formula-packet-binder`.
