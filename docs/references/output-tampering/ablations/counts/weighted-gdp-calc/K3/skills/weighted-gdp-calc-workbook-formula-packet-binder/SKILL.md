---
name: weighted-gdp-calc-workbook-formula-packet-binder
description: "Build the complete formula packet for the observed weighted-GDP workbook without editing it."
---

# Weighted GDP Formula Packet

Build the complete formula packet from the reviewed formula plan. The helper
creates every lookup, net-export, statistic, and weighted-mean formula in the
shape required by the final workbook writer.

## Run

```bash
python /root/.agents/skills/weighted-gdp-calc-workbook-formula-packet-binder/scripts/build_formula_packet.py \
  artifacts/weighted_gdp_summary_binding_note.json \
  artifacts/weighted_gdp_workbook_checkpoint.json \
  artifacts/weighted_gdp_formula_packet.json
```

## Result

The packet is the immutable output of this stage. It contains all workbook
writes in one deterministic handoff and does not modify `gdp.xlsx`. Do not
rebuild or hand-edit the packet; invoke the final writer next and validate the
receipt after the writer completes.
## Count-Study Continuation

After this stage's local outputs are complete, read `weighted-gdp-calc-workbook-final-sheet-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
