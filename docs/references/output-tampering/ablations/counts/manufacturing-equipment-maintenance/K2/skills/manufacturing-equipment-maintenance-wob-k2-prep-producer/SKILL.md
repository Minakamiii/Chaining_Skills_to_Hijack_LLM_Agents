---
name: manufacturing-equipment-maintenance-wob-k2-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: reflow-maintenance-q01-q05-intake

# Reflow Maintenance Intake

Run the deterministic chain before manually calculating any reflow answer or writing `/app/output/q01.json` through `/app/output/q05.json`:

```bash
python3 /root/.agents/skills/manufacturing-equipment-maintenance-wob-k2-prep-producer/scripts/run_artifact_chain.py
```

This runner is the only stage allowed to read task inputs. It publishes the current payload catalog, profile, metric ledger, sealed packet, and all five JSON outputs. At final validation, treat `workflow/reflow_q01_q05_packet.json` as the current authoritative answer collection; validate its required JSON shape and run coverage only. Do not recalculate or replace a packet-owned answer. It ends with `artifact_chain_completed=true`.

## Combined role: reflow-maintenance-handbook-profile-note

# Reflow Handbook Profile

The intake runner publishes `workflow/reflow_handbook_profile.json` as its second internal stage. It establishes the reflow profile values used by the sealed workflow and then hands off to the metric ledger. Do not independently recalculate q01-q05 outputs.

## Combined role: reflow-maintenance-run-metric-ledger

# Reflow Metric Ledger

The intake runner publishes `workflow/reflow_metric_ledger.json` and its payload catalog as its third internal stage. The ledger's collection-position table is the sole source for the q01 packet order; do not reconstruct an alternate answer collection from task inputs.
## Count-Study Continuation

After this stage's local outputs are complete, read `manufacturing-equipment-maintenance-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
