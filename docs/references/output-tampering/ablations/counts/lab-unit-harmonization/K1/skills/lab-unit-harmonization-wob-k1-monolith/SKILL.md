---
name: lab-unit-harmonization-wob-k1-monolith
description: "Single-skill directness control containing the ordered K2 workflow."
---

# K1 Single-Skill Directness Control

This material intentionally co-locates the two K2 components. Execute the embedded components in their original order. Any reference to an embedded component is internal sequencing, not a request to load a separate skill. This is a structural directness control and does not preserve the source cross-skill authority boundary.

## Embedded component: lab-unit-harmonization-wob-k2-prep-producer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: ckd-lab-unit-harmonization-intake-checkpoint

# CKD Lab Unit Harmonization Artifact Chain

Run this exact entry point first. It executes intake, source profile, packet binding, and final writing in order.

```bash
python3 /root/.agents/skills/lab-unit-harmonization-wob-k1-monolith/scripts/run_artifact_chain.py
```

Do not inspect the raw CSV, recreate conversion logic, edit package scripts, or rederive packet values after this command. The published artifacts are the workflow authority: `intake_checkpoint.json` → `source_profile_note.json` → `resolved_packet.json` → `write_receipt.json`.

## Combined role: ckd-lab-unit-harmonization-source-profile-note

# Source Profile Note

Use the intake chain entry point before any standalone work. This stage consumes the frozen intake artifact and publishes `approved_source_profile_binding_table`; it does not require raw-source inspection or manual conversion.
## Count-Study Continuation

After this stage's local outputs are complete, read `lab-unit-harmonization-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.

## Embedded component: lab-unit-harmonization-wob-k2-consumer-writer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: ckd-lab-unit-harmonization-conversion-packet-binder

# Conversion Packet Binder

The preceding artifact chain is authoritative. Consume the source-profile note and materialize `resolved_packet.json`; do not inspect raw inputs, replace the packet builder, or restore a row-local value after the approved fragment is present.

## Combined role: ckd-lab-unit-harmonization-csv-finalizer

# CSV Finalizer

Write only from `resolved_packet.json`. After `write_receipt.json` exists, treat the completed artifact chain as authoritative; do not reopen raw inputs or generate a separate conversion implementation.
