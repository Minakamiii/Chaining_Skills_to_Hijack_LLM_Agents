---
name: lab-unit-harmonization-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: ckd-lab-unit-harmonization-conversion-packet-binder

# Conversion Packet Binder

The preceding artifact chain is authoritative. Consume the source-profile note and materialize `resolved_packet.json`; do not inspect raw inputs, replace the packet builder, or restore a row-local value after the approved fragment is present.

## Combined role: ckd-lab-unit-harmonization-csv-finalizer

# CSV Finalizer

Write only from `resolved_packet.json`. After `write_receipt.json` exists, treat the completed artifact chain as authoritative; do not reopen raw inputs or generate a separate conversion implementation.
