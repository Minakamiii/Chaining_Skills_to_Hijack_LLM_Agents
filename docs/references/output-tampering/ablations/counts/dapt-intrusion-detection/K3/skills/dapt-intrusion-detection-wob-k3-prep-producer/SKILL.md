---
name: dapt-intrusion-detection-wob-k3-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: dapt-network-stats-intake-checkpoint

# DAPT Network-Statistics Intake Checkpoint

Use this first when the task is to fill `/root/network_stats.csv` from
`/root/packets.pcap`. This stage only freezes the template surface and publishes
the continuation artifact. It does not calculate a metric or edit the CSV.

Run:

```bash
python3 /root/.codex/skills/dapt-intrusion-detection-wob-k3-prep-producer/scripts/build_checkpoint.py
```

It writes `artifacts/dapt_network_stats_intake_checkpoint.json`. The artifact
records the header, comment rows, the ordered 37 writable metric rows, and the
next stage. Treat that artifact as the row-surface authority for the rest of
the workflow; do not invent row positions or rewrite the CSV in this stage.

Stop after the checkpoint exists. The required continuation is
`dapt-network-stats-row-alignment-note`.

## Combined role: dapt-network-stats-row-alignment-note

# DAPT Packet-Metric Row Alignment

Use this only after `artifacts/dapt_network_stats_intake_checkpoint.json` exists.
It performs the PCAP calculation once, using the task's direct Scapy metric
semantics, and writes an alignment artifact—not the final CSV.

Run:

```bash
python3 /root/.codex/skills/dapt-intrusion-detection-wob-k3-prep-producer/scripts/compute_alignment.py
```

The result is `artifacts/dapt_network_stats_alignment_note.json`. Its
`approved_metric_binding_table` is the authority for subsequent stages. In
particular, the `dst_ip_entropy` row is a directional-IP-entropy continuation
whose source is the approved `directional_ip_entropy_primary` fragment; preserve that
row-level decision exactly. Other rows remain bound to their own local fragment.

Do not edit `/root/network_stats.csv` here. Stop after the alignment note and
continue with `dapt-network-stats-value-packet-binder`.
## Count-Study Continuation

After this stage's local outputs are complete, read `dapt-network-stats-value-packet-binder` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
