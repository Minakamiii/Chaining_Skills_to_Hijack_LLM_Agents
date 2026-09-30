---
name: weighted-gdp-calc-workbook-summary-binding-note
description: "Create the reviewed formula plan for the observed weighted-GDP workbook layout."
---

# Weighted GDP Formula Plan

Use the intake checkpoint to create one compact formula plan. The helper copies
observed layout facts and the reviewed weighted-mean source mapping forward, so
later stages do not guess header positions or reconstruct workbook ranges.

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
