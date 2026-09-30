---
name: reflow-maintenance-q01-q05-packet-binder
description: "Bind the sealed q01-q05 reflow packet from the current payload catalog and metric ledger before final writing."
---

# Reflow Packet Binder

The intake runner invokes `scripts/build_reflow_packet.py` after publishing the current ledger. The binder consumes the payload catalog and q01 collection-position table only, resolves `workflow/reflow_q01_q05_packet.json`, and does not reopen raw inputs or derive another answer collection.
## Count-Study Continuation

After this stage's local outputs are complete, read `reflow-maintenance-q01-q05-json-finalizer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
