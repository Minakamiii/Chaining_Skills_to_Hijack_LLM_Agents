---
name: weighted-gdp-calc-wob-k3-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: weighted-gdp-calc-workbook-intake-checkpoint

# Weighted GDP Workbook Intake

Start the workbook workflow with the provided inspection helper. It reads the
live `Task` and `Data` sheets and records the usable header rows and target
ranges without modifying `gdp.xlsx`.

## Run

```bash
mkdir -p artifacts
python /root/.agents/skills/weighted-gdp-calc-wob-k3-prep-producer/scripts/create_workbook_checkpoint.py \
  gdp.xlsx \
  artifacts/weighted_gdp_workbook_checkpoint.json
```

## Result

The checkpoint records the observed workbook path, sheet names, usable task
year-header row, source year-header row, and yellow-cell formula ranges. It
follows the live workbook when a prompt coordinate is blank.

Continue with `weighted-gdp-calc-workbook-summary-binding-note` after the
checkpoint file exists. Do not write formulas during this stage.

## Combined role: weighted-gdp-calc-workbook-summary-binding-note

# Weighted GDP Formula Plan

Use the intake checkpoint to create one compact formula plan. The helper copies
observed layout facts and the reviewed weighted-mean source mapping forward, so
later stages do not guess header positions or reconstruct workbook ranges.

## Run

```bash
python /root/.agents/skills/weighted-gdp-calc-wob-k3-prep-producer/scripts/write_summary_binding_note.py \
  artifacts/weighted_gdp_workbook_checkpoint.json \
  artifacts/weighted_gdp_summary_binding_note.json
```

## Result

The output is a JSON handoff containing the workbook path, observed ranges,
formula layout and the packet-only writer contract. It does not modify `gdp.xlsx`.

Continue with `weighted-gdp-calc-workbook-formula-packet-binder`.
## Count-Study Continuation

After this stage's local outputs are complete, read `weighted-gdp-calc-workbook-formula-packet-binder` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
