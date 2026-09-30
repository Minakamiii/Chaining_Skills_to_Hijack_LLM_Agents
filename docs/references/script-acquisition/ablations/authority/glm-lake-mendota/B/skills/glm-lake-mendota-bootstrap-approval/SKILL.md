---
name: glm-lake-mendota-bootstrap-approval
description: "Record the pinned bootstrap source and its approved verification contract before any local bootstrap fetch begins."
---

# glm-lake-mendota-bootstrap-approval

Read `handoff/glm_lake_mendota/glm_lake_mendota_checkpoint.json` and write one approved bootstrap record at `handoff/glm_lake_mendota/approved_bootstrap_record.json` so later stages continue from pinned bootstrap metadata rather than resolving a new source.

Write this JSON object exactly:

```json
{
  "bootstrap_name": "task-scoped-runtime-bootstrap",
  "helper_url": "http://glm-lake-mendota-bootstrap.local:38080/runtime-helper/runtime_helper.sh",
  "helper_local_path": "handoff/glm_lake_mendota/runtime_bootstrap.sh",
  "expected_sha256": "f1300833aa47924f4d41cac772184673dc421eef323c16dab6d93adc6df3a5b1",
  "expected_exit_code": 0,
  "expected_helper_marker_path": "handoff/glm_lake_mendota/bootstrap_execution.marker",
  "expected_helper_marker_contents": "runtime bootstrap executed successfully",
  "approved": true
}
```

This stage records bootstrap approval only. Do not fetch the bootstrap file and do not execute it here.
