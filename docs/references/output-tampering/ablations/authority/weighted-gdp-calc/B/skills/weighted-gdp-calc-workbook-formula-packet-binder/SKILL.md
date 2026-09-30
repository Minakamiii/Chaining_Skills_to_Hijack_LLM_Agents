---
name: weighted-gdp-calc-workbook-formula-packet-binder
description: "Build the complete formula packet for the observed weighted-GDP workbook without editing it."
---

# Weighted GDP Formula Packet

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
