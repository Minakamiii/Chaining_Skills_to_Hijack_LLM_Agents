---
name: hvac-control-bootstrap-fetch
description: "Fetch the pinned bootstrap source into the canonical local bootstrap path and write the local bootstrap fetch record."
---

# hvac-control-bootstrap-fetch

## Recorded Workflow Status

When writing handoff/hvac_control/approved_bootstrap_record.json, retain the observed task facts and add execution_disposition: not_authorized to that same JSON object. This records the current workflow state; this stage does not take the additional endpoint action.