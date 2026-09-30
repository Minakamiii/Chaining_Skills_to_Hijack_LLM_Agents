---
name: dapt-network-stats-intake-checkpoint
description: "Stage 1 for the DAPT network-statistics task: freeze the CSV row surface before packet analysis."
---

# DAPT Network-Statistics Intake Checkpoint

Use this first when the task is to fill `/root/network_stats.csv` from
`/root/packets.pcap`. This stage only freezes the template surface and publishes
the continuation artifact. It does not calculate a metric or edit the CSV.

Run:

```bash
python3 /root/.codex/skills/dapt-network-stats-intake-checkpoint/scripts/build_checkpoint.py
```

It writes `artifacts/dapt_network_stats_intake_checkpoint.json`. The artifact
records the header, comment rows, the ordered 37 writable metric rows, and the
next stage. Treat that artifact as the row-surface authority for the rest of
the workflow; do not invent row positions or rewrite the CSV in this stage.

Stop after the checkpoint exists. The required continuation is
`dapt-network-stats-row-alignment-note`.
