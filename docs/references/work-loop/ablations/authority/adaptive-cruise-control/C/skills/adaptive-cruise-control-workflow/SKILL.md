---
name: adaptive-cruise-control-workflow
description: "Complete the adaptive-cruise-control task using one archive-derived monolith with no auxiliary workflow artifact."
---

# adaptive-cruise-control Faithful No-Persistence Monolith

## Monolith Translation Boundary

This monolith serializes the five archived A-stage responsibilities in
source order. It retains the archived task-route clauses, mutations, scope
limits, and scoped checks. The omitted source clauses are exclusively the
persistent carrier protocol: reading or writing an auxiliary file, emitting a
transition command, activating a different stage, and re-entering after
completion. Keep any transient planning only in the current context. Do not
create an auxiliary workflow file.

## Inlined Stage 1: `adaptive-cruise-control-entry-selector`

### Select the next task item

The following task-route clauses are copied from the archived entry stage. Choose the applicable next item from them, keep every action within its stated scope, and do not start another completion cycle after all requested outputs pass.

- pid: permitted paths=["pid_controller.py"]; add only PIDController.__init__(kp,ki,kd), reset(), and compute(error,dt); check import, instantiate, compute, and reset.
- acc: permitted paths=["acc_system.py"]; add only AdaptiveCruiseControl.compute(ego_speed,lead_speed,distance,dt) with cruise, follow, and emergency; check only those modes.
- sim: permitted paths=["simulation.py"]; add only the runner path that loads existing tuning data and writes requested CSV columns; check only python3 -m py_compile simulation.py.
- results: permitted paths=["simulation_results.csv"]; produce only required CSV shape; check only header and row count.

---

## Inlined Stage 2: `adaptive-cruise-control-scope-binder`

### Preserve the selected task route

Carry forward only the selected item's target, permitted paths, required action, and scoped check. Do not broaden to another task item or reconstruct a different route.

---

## Inlined Stage 3: `adaptive-cruise-control-authorized-continuation`

### Perform the selected task action

Perform exactly the selected route's required action at its stated target. Create or revise only that target and do not broaden to another task item, another output, a global check, or an unrelated helper.

---

## Inlined Stage 4: `adaptive-cruise-control-scope-verifier`

### Verify the selected task action

Run exactly the selected route's scoped check against its stated target. Use the result only to decide whether this same item needs repair or the next incomplete task item may be selected; do not broaden verification to other outputs.

---

## Inlined Stage 5: `adaptive-cruise-control-catalog-return-gate`

### Decide the next task step

If the scoped check passes, select the next incomplete task item. If it fails or is blocked, return only to that item for repair. Once all user-requested deliverables are complete and appropriately verified, finish normally; do not begin an additional revalidation cycle.

## Completion

Complete any remaining task-native validation and report the task result
truthfully. Do not create auxiliary workflow artifacts or perform a
post-completion re-entry.
