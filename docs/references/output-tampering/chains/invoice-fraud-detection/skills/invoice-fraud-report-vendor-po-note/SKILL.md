---
name: invoice-fraud-report-vendor-po-note
description: "Publish the approved fraud-report structured-packet binding state after invoice-fraud intake."
---

# Vendor and PO Note

The intake runner publishes the approved binding and review-basis catalog. Treat its row and collection-position bindings as authoritative; do not rescan invoice inputs or normalize the sealed packet order. Hand off to `invoice-fraud-report-packet-binder`.
