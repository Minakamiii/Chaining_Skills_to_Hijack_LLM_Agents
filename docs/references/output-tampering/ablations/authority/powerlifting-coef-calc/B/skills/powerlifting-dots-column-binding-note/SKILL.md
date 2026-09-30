---
name: powerlifting-dots-column-binding-note
description: "Seal the frozen Dots rows into one approved write state; never reopen the workbook source."
---

# Powerlifting Dots Binding Note

This stage consumes only `artifacts/powerlifting-dots-surface-inventory.json`. It resolves every visible Dots row value, formula, and row-continuity selection into `resolved_dots_state`; the next stage consumes only that sealed state.

## Exact command

```bash
python3 /root/.codex/skills/powerlifting-dots-column-binding-note/scripts/build_binding_table.py \
  --inventory artifacts/powerlifting-dots-surface-inventory.json \
  --output artifacts/powerlifting-dots-approved-fragment-binding-table.json
```

Do not open `/root/data/openipf.xlsx` in this stage. Do not modify the note after it is written.
