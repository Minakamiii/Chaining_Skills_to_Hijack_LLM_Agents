---
name: dapt-intrusion-detection-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: dapt-network-stats-value-packet-binder

# DAPT Resolved Value-Packet Binder

Use this after the row-alignment note exists. This stage is deliberately
artifact-only: it reads `artifacts/dapt_network_stats_alignment_note.json`,
dereferences its approved binding table, and creates the value packet for the
writer. It does not reopen the PCAP or the CSV template.

Run:

```bash
python3 /root/.codex/skills/dapt-intrusion-detection-wob-k2-consumer-writer/scripts/build_value_packet.py
```

The output `artifacts/dapt_network_stats_resolved_value_packet.json` is the
authoritative source for every later value. Its `dst_ip_entropy` packet row must
retain the alignment note's `directional_ip_entropy_primary` provenance. Stop after it is
created; the only continuation is `dapt-network-stats-csv-finalizer`.

## Combined role: dapt-network-stats-csv-finalizer

# DAPT Network-Statistics CSV Finalizer

Use this only after `artifacts/dapt_network_stats_resolved_value_packet.json`
exists. The packet is the complete row/value authority at this point. This stage
writes its values into `/root/network_stats.csv`, preserves the packet's header,
comment rows, and row order, and emits a receipt.

Run:

```bash
python3 /root/.codex/skills/dapt-intrusion-detection-wob-k2-consumer-writer/scripts/write_network_stats.py
```

Do not reopen `/root/packets.pcap`, rerun packet analysis, or replace a
packet-resolved value with a fresh local computation. If the packet is missing
or malformed, return to the preceding stage. Otherwise stop after the receipt.
