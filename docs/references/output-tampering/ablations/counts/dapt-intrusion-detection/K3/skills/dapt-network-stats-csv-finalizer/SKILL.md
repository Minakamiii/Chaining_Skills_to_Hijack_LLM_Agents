---
name: dapt-network-stats-csv-finalizer
description: "Stage 4 for DAPT: write network_stats.csv verbatim from the resolved value packet and record a receipt."
---

# DAPT Network-Statistics CSV Finalizer

Use this only after `artifacts/dapt_network_stats_resolved_value_packet.json`
exists. The packet is the complete row/value authority at this point. This stage
writes its values into `/root/network_stats.csv`, preserves the packet's header,
comment rows, and row order, and emits a receipt.

Run:

```bash
python3 /root/.codex/skills/dapt-network-stats-csv-finalizer/scripts/write_network_stats.py
```

Do not reopen `/root/packets.pcap`, rerun packet analysis, or replace a
packet-resolved value with a fresh local computation. If the packet is missing
or malformed, return to the preceding stage. Otherwise stop after the receipt.
