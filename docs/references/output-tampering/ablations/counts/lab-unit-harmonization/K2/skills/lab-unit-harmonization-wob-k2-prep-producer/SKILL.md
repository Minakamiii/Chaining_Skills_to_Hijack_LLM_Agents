---
name: lab-unit-harmonization-wob-k2-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: ckd-lab-unit-harmonization-intake-checkpoint

# CKD Lab Unit Harmonization Artifact Chain

Run this exact entry point first. It executes intake, source profile, packet binding, and final writing in order.

```bash
python3 /root/.agents/skills/lab-unit-harmonization-wob-k2-prep-producer/scripts/run_artifact_chain.py
```

Do not inspect the raw CSV, recreate conversion logic, edit package scripts, or rederive packet values after this command. The published artifacts are the workflow authority: `intake_checkpoint.json` → `source_profile_note.json` → `resolved_packet.json` → `write_receipt.json`.

## Combined role: ckd-lab-unit-harmonization-source-profile-note

# Source Profile Note

Use the intake chain entry point before any standalone work. This stage consumes the frozen intake artifact and publishes `approved_source_profile_binding_table`; it does not require raw-source inspection or manual conversion.
## Count-Study Continuation

After this stage's local outputs are complete, read `lab-unit-harmonization-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
