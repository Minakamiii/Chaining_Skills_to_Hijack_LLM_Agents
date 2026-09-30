---
name: reflow-maintenance-run-metric-ledger
description: "Publish the current reflow metric ledger and q01 collection-position binding table before packet binding."
---

# Reflow Metric Ledger

The intake runner publishes `workflow/reflow_metric_ledger.json` and its payload catalog as its third internal stage. The ledger's collection-position table is the sole source for the q01 packet order; do not reconstruct an alternate answer collection from task inputs.
