---
name: manufacturing-codebook-normalization-binding-packet
description: "Bind the sealed manufacturing normalization packet from approved record positions before the solution writer."
---

# Codebook Packet Binder

The intake runner invokes `scripts/build_codebook_packet.py` after publishing the current record payload catalog and approved position note. The binder resolves a sealed record packet from those artifacts only. It does not reopen sources, derive a second collection, or compare packet order against an earlier traversal.
## Count-Study Continuation

After this stage's local outputs are complete, read `manufacturing-codebook-normalization-solution-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
