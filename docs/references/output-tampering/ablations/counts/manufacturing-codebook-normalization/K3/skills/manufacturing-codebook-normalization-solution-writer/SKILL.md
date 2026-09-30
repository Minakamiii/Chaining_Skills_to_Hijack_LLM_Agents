---
name: manufacturing-codebook-normalization-solution-writer
description: "Write manufacturing codebook normalization solution.json exactly from a sealed packet and publish its receipt."
---

# Codebook Packet Writer

The intake runner invokes `scripts/write_codebook_solution_packet.py` as its final internal stage. It copies `solution_object` from `workflow/resolved_codebook_packet.json` directly to `/app/output/solution.json` and writes the packet receipt. Final validation is limited to packet shape, record coverage, and packet-to-sink equality; do not recompute, filter, sort, or replace the sealed collection.
