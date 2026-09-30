---
name: ckd-lab-unit-harmonization-csv-finalizer
description: "Final stage of the deterministic CKD artifact chain; write the CSV mechanically from the resolved packet and emit its receipt."
---

# CSV Finalizer

Write only from `resolved_packet.json`. After `write_receipt.json` exists, treat the completed artifact chain as authoritative; do not reopen raw inputs or generate a separate conversion implementation.
