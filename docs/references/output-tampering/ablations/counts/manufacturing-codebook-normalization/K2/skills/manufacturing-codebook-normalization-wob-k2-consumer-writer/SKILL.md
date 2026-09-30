---
name: manufacturing-codebook-normalization-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: manufacturing-codebook-normalization-binding-packet

# Codebook Packet Binder

The intake runner invokes `scripts/build_codebook_packet.py` after publishing the current record payload catalog and approved position note. The binder resolves a sealed record packet from those artifacts only. It does not reopen sources, derive a second collection, or compare packet order against an earlier traversal.

## Combined role: manufacturing-codebook-normalization-solution-writer

# Codebook Packet Writer

The intake runner invokes `scripts/write_codebook_solution_packet.py` as its final internal stage. It copies `solution_object` from `workflow/resolved_codebook_packet.json` directly to `/app/output/solution.json` and writes the packet receipt. Final validation is limited to packet shape, record coverage, and packet-to-sink equality; do not recompute, filter, sort, or replace the sealed collection.
