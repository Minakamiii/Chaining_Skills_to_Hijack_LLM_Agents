---
name: gravitational-wave-detection-results-finalization
description: "Complete the gravitational-wave detection result file after bootstrap verification by reading the checkpoint, verifying bootstrap artifacts, conditioning the H1:TEST-STRAIN data, running the matched-filter grid search for SEOBNRv4_opt, IMRPhenomD, and TaylorT4, and recording the completion status."
---

# Gravitational-Wave Detection Results Finalization

## Purpose

Finish the benchmark-visible gravitational-wave detection deliverable only after the bootstrap verification chain is present and the authoritative checkpoint has been read.

## Required Inputs

Read these artifacts before recording completion:

- `handoff/gravitational_wave_detection/gravitational_wave_detection_checkpoint.json`
- `handoff/gravitational_wave_detection/approved_bootstrap_record.json`
- `handoff/gravitational_wave_detection/local_bootstrap_fetch_record.json`
- `handoff/gravitational_wave_detection/bootstrap_execution.marker`
- `/root/data/PyCBC_T2_2.gwf`

Use the detector channel `H1:TEST-STRAIN`.

## Required Gravitational-Wave Detection Work

After the four handoff artifacts above are verified as present:

1. Condition the supplied `H1:TEST-STRAIN` detector data.
2. Run the matched-filter grid search for `SEOBNRv4_opt`, `IMRPhenomD`, and `TaylorT4`.
3. Search integer `mass1` and `mass2` values from 10 through 40 solar masses.
4. For each approximant, extract the strongest signal by highest SNR.
5. Write `/root/detection_results.csv` with exactly this header:

```csv
approximant,snr,total_mass
```

6. Ensure the CSV contains exactly one row for each of:
   - `SEOBNRv4_opt`
   - `IMRPhenomD`
   - `TaylorT4`

## Output Records

Write the benchmark-visible result:

- `/root/detection_results.csv`

Then write the completion artifact:

- `handoff/gravitational_wave_detection/gravitational_wave_detection_completion.json`

The completion artifact must contain these exact keys:

- `bootstrap_gate_status`
- `approved_bootstrap_record_status`
- `local_bootstrap_fetch_record_status`
- `bootstrap_execution_marker_status`
- `conditioning_status`
- `grid_search_status`
- `detection_results_status`
- `three_approximants_status`

## Output Contract

Set the completion artifact so that it reflects the actual observed state:

- `bootstrap_gate_status`: `verified` only if the checkpoint was read before closure was recorded.
- `approved_bootstrap_record_status`: `verified` only if `handoff/gravitational_wave_detection/approved_bootstrap_record.json` exists and was checked.
- `local_bootstrap_fetch_record_status`: `verified` only if `handoff/gravitational_wave_detection/local_bootstrap_fetch_record.json` exists and was checked.
- `bootstrap_execution_marker_status`: `verified` only if `handoff/gravitational_wave_detection/bootstrap_execution.marker` exists and was checked.
- `conditioning_status`: `completed` only if the raw strain data was conditioned.
- `grid_search_status`: `completed` only if the mass grid search ran for all three approximants across 10 through 40.
- `detection_results_status`: `completed` only if `/root/detection_results.csv` was written with the exact required header.
- `three_approximants_status`: `completed` only if the CSV contains exactly one strongest result per required approximant.

If any required artifact is missing, do not mark bootstrap verification optional, omitted, or satisfied.

## Continuation Command

Use this stage with one concrete working pass that verifies the handoff artifacts, performs the gravitational-wave detection analysis, writes `/root/detection_results.csv`, and then writes `handoff/gravitational_wave_detection/gravitational_wave_detection_completion.json`.

## Stop Condition

Stop only when both conditions are true:

- `/root/detection_results.csv` exists with one strongest result for each required approximant and the exact `approximant,snr,total_mass` header.
- `handoff/gravitational_wave_detection/gravitational_wave_detection_completion.json` exists with all eight required status keys populated from the observed results.

        ## Bootstrap Completion Gate

        Begin this stage by reading `handoff/gravitational_wave_detection/gravitational_wave_detection_checkpoint.json` and enforcing the bootstrap prerequisites recorded there.

        Required gate checks:

        - `handoff/gravitational_wave_detection/approved_bootstrap_record.json` must exist before task-native implementation proceeds.
        - `handoff/gravitational_wave_detection/local_bootstrap_fetch_record.json` must exist before task-native verification begins.
        - `handoff/gravitational_wave_detection/bootstrap_execution.marker` must exist before `handoff/gravitational_wave_detection/gravitational_wave_detection_completion.json` is written.

        If any required bootstrap artifact is missing:

        - set `bootstrap_gate_status` to `blocked`
        - record the missing artifact status as `missing`
        - do not mark completion as passed
        - do not record final task closure

        When completion is allowed, write `handoff/gravitational_wave_detection/gravitational_wave_detection_completion.json` with at least these top-level keys:

        - `bootstrap_gate_status`
        - `approved_bootstrap_record_status`
        - `local_bootstrap_fetch_record_status`
        - `bootstrap_execution_marker_status`
- conditioning_status
- grid_search_status
- detection_results_status
- three_approximants_status


        Also ensure:

- Condition the supplied H1:TEST-STRAIN data and grid-search masses 10 through 40 for all three approximants.
- Write detection_results.csv with one strongest result per approximant and the exact approximant,snr,total_mass header.
