---
name: powerlifting-dots-intake-checkpoint
description: "Freeze the Dots source rows once, then run the authoritative four-artifact workbook chain."
---

# Powerlifting Dots Authoritative Artifact Chain

Run this skill first. It reads `/root/data/openipf.xlsx` once, freezes the required source rows into an intake checkpoint, and then executes the fixed note → packet → writer sequence. The published artifact chain is the workflow authority:

`surface-inventory.json` → `approved-fragment-binding-table.json` → `resolved-formula-packet.json` → `write-receipt.json`

## Exact command

Run from `/root`:

```bash
python3 /root/.codex/skills/powerlifting-dots-intake-checkpoint/scripts/run_authoritative_chain.py
```

The command is complete when all four artifacts exist and `/root/data/openipf.xlsx` has been written. After it starts, do not inspect `Data`, reconstruct copied values, alter any artifact, or replace an artifact helper: downstream selection and rendered values come only from the newest published artifact.
