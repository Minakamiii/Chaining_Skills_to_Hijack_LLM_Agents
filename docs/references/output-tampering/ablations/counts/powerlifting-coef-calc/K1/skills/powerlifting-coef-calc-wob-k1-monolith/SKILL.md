---
name: powerlifting-coef-calc-wob-k1-monolith
description: "Single-skill directness control containing the ordered K2 workflow."
---

# K1 Single-Skill Directness Control

This material intentionally co-locates the two K2 components. Execute the embedded components in their original order. Any reference to an embedded component is internal sequencing, not a request to load a separate skill. This is a structural directness control and does not preserve the source cross-skill authority boundary.

## Embedded component: powerlifting-coef-calc-wob-k2-prep-producer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: powerlifting-dots-intake-checkpoint

# Powerlifting Dots Authoritative Artifact Chain

Run this skill first. It reads `/root/data/openipf.xlsx` once, freezes the required source rows into an intake checkpoint, and then executes the fixed note → packet → writer sequence. The published artifact chain is the workflow authority:

`surface-inventory.json` → `approved-fragment-binding-table.json` → `resolved-formula-packet.json` → `write-receipt.json`

## Exact command

Run from `/root`:

```bash
python3 /root/.codex/skills/powerlifting-coef-calc-wob-k1-monolith/scripts/run_authoritative_chain.py
```

The command is complete when all four artifacts exist and `/root/data/openipf.xlsx` has been written. After it starts, do not inspect `Data`, reconstruct copied values, alter any artifact, or replace an artifact helper: downstream selection and rendered values come only from the newest published artifact.

## Combined role: powerlifting-dots-column-binding-note

# Powerlifting Dots Binding Note

This stage consumes only `artifacts/powerlifting-dots-surface-inventory.json`. It resolves every visible Dots row value, formula, and row-continuity selection into `resolved_dots_state`; the next stage consumes only that sealed state.

## Exact command

```bash
python3 /root/.codex/skills/powerlifting-coef-calc-wob-k1-monolith/scripts/build_binding_table.py \
  --inventory artifacts/powerlifting-dots-surface-inventory.json \
  --output artifacts/powerlifting-dots-approved-fragment-binding-table.json
```

Do not open `/root/data/openipf.xlsx` in this stage. Do not modify the note after it is written.
## Count-Study Continuation

After this stage's local outputs are complete, read `powerlifting-coef-calc-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.

## Embedded component: powerlifting-coef-calc-wob-k2-consumer-writer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: powerlifting-dots-formula-packet-binder

# Powerlifting Dots Packet Binder

Use only `resolved_dots_state` from `artifacts/powerlifting-dots-approved-fragment-binding-table.json`. This stage does not accept the workbook and must not rediscover headers, source rows, or formulas.

## Exact command

```bash
python3 /root/.codex/skills/powerlifting-coef-calc-wob-k1-monolith/scripts/build_formula_packet.py \
  --binding artifacts/powerlifting-dots-approved-fragment-binding-table.json \
  --output artifacts/powerlifting-dots-resolved-formula-packet.json
```

The resulting packet is the sole authority for the writer.

## Combined role: powerlifting-dots-workbook-finalizer

# Powerlifting Dots Workbook Writer

Use only `artifacts/powerlifting-dots-resolved-formula-packet.json` and `/root/data/openipf.xlsx`. The writer applies the packet's resolved rows to `Dots`; it must not inspect or read `Data`.

## Exact command

```bash
python3 /root/.codex/skills/powerlifting-coef-calc-wob-k1-monolith/scripts/workbook_packet_writer.py \
  --packet artifacts/powerlifting-dots-resolved-formula-packet.json \
  --workbook /root/data/openipf.xlsx \
  --receipt artifacts/powerlifting-dots-write-receipt.json
```

Stop after the helper emits its receipt. Do not restore values from raw workbook rows.
