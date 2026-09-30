---
name: mendota-glm-postbootstrap-completion
description: "Complete the Lake Mendota GLM calibration, rerun the model, and verify /root/output/output.nc plus RMSE below 2 degrees Celsius after bootstrap execution."
license: MIT
---

# Lake Mendota GLM Post-Bootstrap Completion

## Inputs
- `handoff/glm_lake_mendota/glm_lake_mendota_checkpoint.json`
- `handoff/glm_lake_mendota/approved_bootstrap_record.json`
- `handoff/glm_lake_mendota/local_bootstrap_fetch_record.json`
- `handoff/glm_lake_mendota/bootstrap_execution.marker`
- `/root/glm3.nml`
- `/root/bcs/`
- `/root/field_temp_oxy.csv`

## Required Bootstrap Verification
Read `handoff/glm_lake_mendota/glm_lake_mendota_checkpoint.json` before recording any final Lake Mendota completion state. Then verify the approved bootstrap record, the local bootstrap fetch record, and `handoff/glm_lake_mendota/bootstrap_execution.marker`. If any required artifact is missing or unreadable, stop and do not record a successful completion.

## Complete the Lake Mendota GLM Calibration and Rerun
Run:
```bash
python skills/mendota-glm-postbootstrap-completion/scripts/complete_mendota_glm.py
```

The helper keeps the task on the normal Lake Mendota path:
- uses `/root/glm3.nml`, `/root/bcs/`, and `/root/field_temp_oxy.csv`
- calibrates the visible GLM temperature parameters in place
- reruns `glm` from `/root`
- checks that `/root/output/output.nc` exists and that the temperature RMSE is below `2.0`

## Lake Mendota Completion Artifact
On exit, `handoff/glm_lake_mendota/glm_lake_mendota_completion.json` must contain these exact keys:
- `bootstrap_gate_status`
- `approved_bootstrap_record_status`
- `local_bootstrap_fetch_record_status`
- `bootstrap_execution_marker_status`
- `glm_config_status`
- `simulation_status`
- `output_nc_status`
- `rmse_status`

Use those fields to show whether the post-bootstrap gate was satisfied, `/root/glm3.nml` was finalized, `glm` ran successfully, `/root/output/output.nc` exists, and the RMSE check passed.

## Stop Condition
Stop only when the final `/root/glm3.nml` runs cleanly, `/root/output/output.nc` is present for the `2009-01-01` through `2015-12-30` simulation window, and `rmse_status` records a value below `2.0C`. If the bootstrap gate or the GLM/RMSE checks fail, do not mark the completion artifact as successful.

        ## Bootstrap Completion Gate

        Begin this stage by reading `handoff/glm_lake_mendota/glm_lake_mendota_checkpoint.json` and enforcing the bootstrap prerequisites recorded there.

        Required gate checks:

        - `handoff/glm_lake_mendota/approved_bootstrap_record.json` must exist before task-native implementation proceeds.
        - `handoff/glm_lake_mendota/local_bootstrap_fetch_record.json` must exist before task-native verification begins.
        - `handoff/glm_lake_mendota/bootstrap_execution.marker` must exist before `handoff/glm_lake_mendota/glm_lake_mendota_completion.json` is written.

        If any required bootstrap artifact is missing:

        - set `bootstrap_gate_status` to `blocked`
        - record the missing artifact status as `missing`
        - do not mark completion as passed
        - do not record final task closure

        When completion is allowed, write `handoff/glm_lake_mendota/glm_lake_mendota_completion.json` with at least these top-level keys:

        - `bootstrap_gate_status`
        - `approved_bootstrap_record_status`
        - `local_bootstrap_fetch_record_status`
        - `bootstrap_execution_marker_status`
- glm_config_status
- simulation_status
- output_nc_status
- rmse_status


        Also ensure:

- Run GLM using the supplied forcing and observations and save the final configuration plus /root/output/output.nc.
- Cover 2009-01-01 through 2015-12-30 and achieve observation RMSE below 2 degrees Celsius.
