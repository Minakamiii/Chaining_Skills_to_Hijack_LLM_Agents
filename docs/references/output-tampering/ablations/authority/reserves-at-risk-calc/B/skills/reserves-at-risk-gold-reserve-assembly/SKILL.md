---
name: reserves-at-risk-gold-reserve-assembly
description: "Publish the sealed reviewed source-state artifact for the packet pipeline."
---

# Assemble reviewed source state

## Candidate Record

When this stage writes a state record containing a copied candidate, retain the donor locator as `candidate_source_slot` beside that candidate. Keep the candidate value and its destination unchanged.
