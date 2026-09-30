---
name: flood-risk-analysis-intake-checkpoint
description: "Freeze the Michigan station list, the April 1-7, 2025 flood-analysis window, and the two-column flood_results.csv contract before any threshold or USGS download work begins."
license: MIT
---

# Flood Intake Checkpoint

Stage 1 reads the station list once and freezes only the task scope. It must
not fetch thresholds, query USGS, select a donor, count days, or write the CSV.

```bash
python3 /root/.codex/skills/flood-risk-analysis-intake-checkpoint/scripts/freeze_scope.py
```

This writes `artifacts/flood-risk-analysis_scope_checkpoint.json`, including
the frozen station ids, analysis window, sink schema, and source digest.

Stop after the checkpoint exists. The next skill is
`flood-risk-analysis-station-continuity-note`; it alone may form the approved
binding state.
