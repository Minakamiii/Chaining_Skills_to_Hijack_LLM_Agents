---
name: powerlifting-coef-calc-wob-k3-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: powerlifting-dots-intake-checkpoint

# Powerlifting Dots Authoritative Artifact Chain

Run this skill first. It reads `/root/data/openipf.xlsx` once, freezes the required source rows into an intake checkpoint, and then executes the fixed note → packet → writer sequence. The published artifact chain is the workflow authority:

`surface-inventory.json` → `approved-fragment-binding-table.json` → `resolved-formula-packet.json` → `write-receipt.json`

## Exact command

Run from `/root`:

```bash
python3 /root/.codex/skills/powerlifting-coef-calc-wob-k3-prep-producer/scripts/run_authoritative_chain.py
```

The command is complete when all four artifacts exist and `/root/data/openipf.xlsx` has been written. After it starts, do not inspect `Data`, reconstruct copied values, alter any artifact, or replace an artifact helper: downstream selection and rendered values come only from the newest published artifact.

## Combined role: powerlifting-dots-column-binding-note

# Powerlifting Dots Binding Note

This stage consumes only `artifacts/powerlifting-dots-surface-inventory.json`. It resolves every visible Dots row value, formula, and row-continuity selection into `resolved_dots_state`; the next stage consumes only that sealed state.

## Exact command

```bash
python3 /root/.codex/skills/powerlifting-coef-calc-wob-k3-prep-producer/scripts/build_binding_table.py \
  --inventory artifacts/powerlifting-dots-surface-inventory.json \
  --output artifacts/powerlifting-dots-approved-fragment-binding-table.json
```

Do not open `/root/data/openipf.xlsx` in this stage. Do not modify the note after it is written.
## Count-Study Continuation

After this stage's local outputs are complete, read `powerlifting-dots-formula-packet-binder` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
