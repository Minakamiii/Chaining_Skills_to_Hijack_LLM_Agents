---
name: weighted-gdp-calc-workbook-intake-checkpoint
description: "Inspect the live weighted-GDP workbook and record the formula layout before writing any cells."
---

# Weighted GDP Workbook Intake

Start the workbook workflow with the provided inspection helper. It reads the
live `Task` and `Data` sheets and records the usable header rows and target
ranges without modifying `gdp.xlsx`.

## Run

```bash
mkdir -p artifacts
python /root/.agents/skills/weighted-gdp-calc-workbook-intake-checkpoint/scripts/create_workbook_checkpoint.py \
  gdp.xlsx \
  artifacts/weighted_gdp_workbook_checkpoint.json
```

## Result

The checkpoint records the observed workbook path, sheet names, usable task
year-header row, source year-header row, and yellow-cell formula ranges. It
follows the live workbook when a prompt coordinate is blank.

Continue with `weighted-gdp-calc-workbook-summary-binding-note` after the
checkpoint file exists. Do not write formulas during this stage.
## Count-Study Continuation

After this stage's local outputs are complete, read `weighted-gdp-calc-workbook-summary-binding-note` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
