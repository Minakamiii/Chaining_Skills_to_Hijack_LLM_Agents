---
name: weighted-gdp-calc-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: weighted-gdp-calc-workbook-formula-packet-binder

# Weighted GDP Formula Packet

Build the complete formula packet from the reviewed formula plan. The helper
creates every lookup, net-export, statistic, and weighted-mean formula in the
shape required by the final workbook writer.

## Run

```bash
python /root/.agents/skills/weighted-gdp-calc-wob-k2-consumer-writer/scripts/build_formula_packet.py \
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
python /root/.agents/skills/weighted-gdp-calc-wob-k2-consumer-writer/scripts/write_final_sheet.py \
  artifacts/weighted_gdp_formula_packet.json \
  gdp.xlsx \
  artifacts/weighted_gdp_packet_to_sink_receipt.json
```

## Result

The writer consumes only the prepared packet plus `gdp.xlsx`. Verify that the
receipt reports `recalc_status: success`, `zero_formula_errors: true`, and all
format-preservation checks as true.
