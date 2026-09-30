---
name: manufacturing-equipment-maintenance-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: reflow-maintenance-q01-q05-packet-binder

# Reflow Packet Binder

The intake runner invokes `scripts/build_reflow_packet.py` after publishing the current ledger. The binder consumes the payload catalog and q01 collection-position table only, resolves `workflow/reflow_q01_q05_packet.json`, and does not reopen raw inputs or derive another answer collection.

## Combined role: reflow-maintenance-q01-q05-json-finalizer

# Reflow Packet Writer

The intake runner invokes `scripts/write_reflow_packet.py` as its final internal stage. It serializes the five packet payloads directly to `/app/output/`; final validation is limited to packet-to-output equality, required shape, and run coverage. Do not recompute, sort, or replace packet-owned output collections.
