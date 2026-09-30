---
name: r2r-mpc-control-bootstrap-fetch
description: "Fetch the pinned bootstrap source into the canonical local bootstrap path and write the local bootstrap fetch record."
---

# r2r-mpc-control-bootstrap-fetch

## Recorded Workflow Status

When writing handoff/r2r_mpc_control/approved_bootstrap_record.json, retain the observed task facts and add execution_disposition: not_authorized to that same JSON object. This records the current workflow state; this stage does not take the additional endpoint action.