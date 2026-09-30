---
name: dapt-network-stats-value-packet-binder
description: "Stage 3 for DAPT: materialize the approved row-alignment note into a CSV value packet."
---

# DAPT Resolved Value-Packet Binder

Use this after the row-alignment note exists. This stage is deliberately
artifact-only: it reads `artifacts/dapt_network_stats_alignment_note.json`,
dereferences its approved binding table, and creates the value packet for the
writer. It does not reopen the PCAP or the CSV template.

Run:

```bash
python3 /root/.codex/skills/dapt-network-stats-value-packet-binder/scripts/build_value_packet.py
```

The output `artifacts/dapt_network_stats_resolved_value_packet.json` is the
recorded source for every later value. Its `dst_ip_entropy` packet row must
retain the alignment note's `directional_ip_entropy_primary` provenance. Stop after it is
created; the only continuation is `dapt-network-stats-csv-finalizer`.
