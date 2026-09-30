---
name: weighted-gdp-calc-workbook-final-sheet-writer
description: "Apply the prepared weighted-GDP formula packet to the existing workbook and verify the saved result."
---

# Weighted GDP Workbook Writer

Apply the prepared packet to the existing `Task` sheet. The writer preserves
the two existing sheets and column widths, recalculates through LibreOffice,
and records a receipt for the saved workbook.

## Run

```bash
python /root/.agents/skills/weighted-gdp-calc-workbook-final-sheet-writer/scripts/write_final_sheet.py \
  artifacts/weighted_gdp_formula_packet.json \
  gdp.xlsx \
  artifacts/weighted_gdp_packet_to_sink_receipt.json
```

## Result

The writer consumes only the prepared packet plus `gdp.xlsx`. Verify that the
receipt reports `recalc_status: success`, `zero_formula_errors: true`, and all
format-preservation checks as true.
