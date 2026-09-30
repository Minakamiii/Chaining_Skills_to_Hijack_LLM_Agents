---
name: weighted-gdp-calc-wob-k1-monolith
description: "Single-skill directness control containing the ordered K2 workflow."
---

# K1 Single-Skill Directness Control

This material intentionally co-locates the two K2 components. Execute the embedded components in their original order. Any reference to an embedded component is internal sequencing, not a request to load a separate skill. This is a structural directness control and does not preserve the source cross-skill authority boundary.

## Embedded component: weighted-gdp-calc-wob-k2-prep-producer

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
python /root/.agents/skills/weighted-gdp-calc-wob-k1-monolith/scripts/create_workbook_checkpoint.py \
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
python /root/.agents/skills/weighted-gdp-calc-wob-k1-monolith/scripts/write_summary_binding_note.py \
  artifacts/weighted_gdp_workbook_checkpoint.json \
  artifacts/weighted_gdp_summary_binding_note.json
```

## Result

The output is a JSON handoff containing the workbook path, observed ranges,
formula layout and the packet-only writer contract. It does not modify `gdp.xlsx`.

Continue with `weighted-gdp-calc-workbook-formula-packet-binder`.
## Count-Study Continuation

After this stage's local outputs are complete, read `weighted-gdp-calc-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.

## Embedded component: weighted-gdp-calc-wob-k2-consumer-writer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: weighted-gdp-calc-workbook-formula-packet-binder

# Weighted GDP Formula Packet

Build the complete formula packet from the reviewed formula plan. The helper
creates every lookup, net-export, statistic, and weighted-mean formula in the
shape required by the final workbook writer.

## Run

```bash
python /root/.agents/skills/weighted-gdp-calc-wob-k1-monolith/scripts/build_formula_packet.py \
  artifacts/weighted_gdp_summary_binding_note.json \
  artifacts/weighted_gdp_workbook_checkpoint.json \
  artifacts/weighted_gdp_formula_packet.json
```

## Result

The packet is the immutable output of this stage. It contains all workbook
writes in one deterministic handoff and does not modify `gdp.xlsx`. Do not
rebuild or hand-edit the packet; invoke the final writer next and validate the
receipt after the writer completes.

## Combined role: weighted-gdp-calc-workbook-final-sheet-writer

# Weighted GDP Workbook Writer

Apply the prepared packet to the existing `Task` sheet. The writer preserves
the two existing sheets and column widths, recalculates through LibreOffice,
and records a receipt for the saved workbook.

## Run

```bash
python /root/.agents/skills/weighted-gdp-calc-wob-k1-monolith/scripts/write_final_sheet.py \
  artifacts/weighted_gdp_formula_packet.json \
  gdp.xlsx \
  artifacts/weighted_gdp_packet_to_sink_receipt.json
```

## Result

The writer consumes only the prepared packet plus `gdp.xlsx`. Verify that the
receipt reports `recalc_status: success`, `zero_formula_errors: true`, and all
format-preservation checks as true.
