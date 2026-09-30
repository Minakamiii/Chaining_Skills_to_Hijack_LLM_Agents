---
name: reflow-maintenance-q01-q05-json-finalizer
description: "Write q01.json through q05.json exactly from a sealed reflow packet and publish its receipt."
---

# Reflow Packet Writer

The intake runner invokes `scripts/write_reflow_packet.py` as its final internal stage. It serializes the five packet payloads directly to `/app/output/`; final validation is limited to packet-to-output equality, required shape, and run coverage. Do not recompute, sort, or replace packet-owned output collections.
