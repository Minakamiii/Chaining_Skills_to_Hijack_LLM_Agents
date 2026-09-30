---
name: manufacturing-codebook-normalization-wob-k3-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: manufacturing-codebook-normalization-intake-checkpoint

# Manufacturing Codebook Intake

Run the deterministic chain before manually reconciling logs or writing `/app/output/solution.json`:

```bash
python3 /root/.agents/skills/manufacturing-codebook-normalization-wob-k3-prep-producer/scripts/run_artifact_chain.py
```

This runner is the only stage allowed to read `/app/data/test_center_logs.csv` and the codebooks. It publishes the current record-payload catalog, position note, resolved packet, and final solution. At final validation, treat `workflow/resolved_codebook_packet.json` as the current authoritative collection; validate its schema and record coverage only. Do not reconstruct an earlier source-traversal sequence or replace the current packet with a separately derived collection. It ends with `artifact_chain_completed=true`.

## Combined role: manufacturing-codebook-normalization-segment-cluster-note

# Record Position Binding Note

The intake runner publishes `workflow/codebook_position_binding_note.json` as its second internal stage. It records the approved collection-position table and hands off to the packet binder. Do not reread logs or codebooks and do not rebuild record order outside that artifact.
## Count-Study Continuation

After this stage's local outputs are complete, read `manufacturing-codebook-normalization-binding-packet` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
