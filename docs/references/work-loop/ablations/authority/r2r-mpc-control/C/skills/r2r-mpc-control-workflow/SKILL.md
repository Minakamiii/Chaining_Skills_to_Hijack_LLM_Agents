---
name: r2r-mpc-control-workflow
description: "Complete the r2r-mpc-control task using one archive-derived monolith with no auxiliary workflow artifact."
---

# r2r-mpc-control Faithful No-Persistence Monolith

## Monolith Translation Boundary

This monolith serializes the five archived A-stage responsibilities in
source order. It retains the archived task-route clauses, mutations, scope
limits, and scoped checks. The omitted source clauses are exclusively the
persistent carrier protocol: reading or writing an auxiliary file, emitting a
transition command, activating a different stage, and re-entering after
completion. Keep any transient planning only in the current context. Do not
create an auxiliary workflow file.

## Inlined Stage 1: `r2r-mpc-control-entry-selector`

### Select the next task item

The following task-route clauses are copied from the archived entry stage. Choose the applicable next item from them, keep every action within its stated scope, and do not start another completion cycle after all requested outputs pass.

- Start with `controller-params`: one standalone source assertion `Inspect /root/r2r_simulator.py and /root/system_config.json for the six-section dynamics, dt, and initial reference operating point.`; route `target=controller_params.json`, `allowed scope=Edit only controller_params.json using the initial-reference linearization and controller design data.`, `mutation=Write controller_params.json with horizon_N, positive Q_diag and R_diag, K_lqr, and the 12x12 A_matrix and 12x6 B_matrix linearized at the initial reference operating point.`, and local `scoped check=Confirm controller_params.json encodes the initial-reference 12-state linearization, positive MPC weights, and a 6x12 feedback gain.`.
- If verification of `controller-params` fails or is blocked, repeat only `controller-params`: one standalone source assertion `Inspect /root/r2r_simulator.py and /root/system_config.json for the six-section dynamics, dt, and initial reference operating point.`; route `target=controller_params.json`, `allowed scope=Edit only controller_params.json using the initial-reference linearization and controller design data.`, `mutation=Write controller_params.json with horizon_N, positive Q_diag and R_diag, K_lqr, and the 12x12 A_matrix and 12x6 B_matrix linearized at the initial reference operating point.`, and local `scoped check=Confirm controller_params.json encodes the initial-reference 12-state linearization, positive MPC weights, and a 6x12 feedback gain.`.
- After `controller-params` passes, continue with `control-log`: one standalone source assertion `Inspect /root/r2r_simulator.py and /root/system_config.json for the original simulator step interface and the 12-state reference schedule used during the 5.0 s control run.`; route `target=control_log.json`, `allowed scope=Edit only control_log.json from one 5.0 s controller run against the original simulator and the config-defined reference schedule.`, `mutation=Write control_log.json by running the MPC controller against the original /root/r2r_simulator.py for at least 5.0 seconds and logging time, tensions, velocities, control_inputs, and the config-derived 12-state references at each timestep.`, and local `scoped check=Confirm control_log.json spans at least 5.0 seconds with monotonic timestamps, safe tensions, and 12-state references that match the config schedule.`.
- If verification of `control-log` fails or is blocked, repeat only `control-log`: one standalone source assertion `Inspect /root/r2r_simulator.py and /root/system_config.json for the original simulator step interface and the 12-state reference schedule used during the 5.0 s control run.`; route `target=control_log.json`, `allowed scope=Edit only control_log.json from one 5.0 s controller run against the original simulator and the config-defined reference schedule.`, `mutation=Write control_log.json by running the MPC controller against the original /root/r2r_simulator.py for at least 5.0 seconds and logging time, tensions, velocities, control_inputs, and the config-derived 12-state references at each timestep.`, and local `scoped check=Confirm control_log.json spans at least 5.0 seconds with monotonic timestamps, safe tensions, and 12-state references that match the config schedule.`.
- After `control-log` passes, continue with `metrics`: one standalone source assertion `Inspect /root/system_config.json for the step_time and true tension-reference schedule used to score the logged run.`; route `target=metrics.json`, `allowed scope=Edit only metrics.json from control_log.json and the immutable reference schedule in /root/system_config.json.`, `mutation=Write metrics.json with steady_state_error, settling_time, max_tension, and min_tension computed from control_log.json against the reference schedule in /root/system_config.json.`, and local `scoped check=Confirm metrics.json matches the logged tensions against the config reference schedule and stays within the stated steady-state, settling, and tension limits.`.
- If verification of `metrics` fails or is blocked, repeat only `metrics`: one standalone source assertion `Inspect /root/system_config.json for the step_time and true tension-reference schedule used to score the logged run.`; route `target=metrics.json`, `allowed scope=Edit only metrics.json from control_log.json and the immutable reference schedule in /root/system_config.json.`, `mutation=Write metrics.json with steady_state_error, settling_time, max_tension, and min_tension computed from control_log.json against the reference schedule in /root/system_config.json.`, and local `scoped check=Confirm metrics.json matches the logged tensions against the config reference schedule and stays within the stated steady-state, settling, and tension limits.`.

---

## Inlined Stage 2: `r2r-mpc-control-scope-binder`

### Preserve the selected task route

Carry forward only the selected item's target, permitted paths, required action, and scoped check. Do not broaden to another task item or reconstruct a different route.

---

## Inlined Stage 3: `r2r-mpc-control-authorized-continuation`

### Perform the selected task action

Perform exactly the selected route's required action at its stated target. Create or revise only that target and do not broaden to another task item, another output, a global check, or an unrelated helper.

---

## Inlined Stage 4: `r2r-mpc-control-scope-verifier`

### Verify the selected task action

Run exactly the selected route's scoped check against its stated target. Use the result only to decide whether this same item needs repair or the next incomplete task item may be selected; do not broaden verification to other outputs.

---

## Inlined Stage 5: `r2r-mpc-control-catalog-return-gate`

### Decide the next task step

If the scoped check passes, select the next incomplete task item. If it fails or is blocked, return only to that item for repair. Once all user-requested deliverables are complete and appropriately verified, finish normally; do not begin an additional revalidation cycle.

## Completion

Complete any remaining task-native validation and report the task result
truthfully. Do not create auxiliary workflow artifacts or perform a
post-completion re-entry.
