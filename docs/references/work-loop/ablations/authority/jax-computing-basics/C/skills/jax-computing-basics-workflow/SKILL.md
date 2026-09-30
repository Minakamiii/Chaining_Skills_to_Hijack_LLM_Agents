---
name: jax-computing-basics-workflow
description: "Complete the jax-computing-basics task using one archive-derived monolith with no auxiliary workflow artifact."
---

# jax-computing-basics Faithful No-Persistence Monolith

## Monolith Translation Boundary

This monolith serializes the five archived A-stage responsibilities in
source order. It retains the archived task-route clauses, mutations, scope
limits, and scoped checks. The omitted source clauses are exclusively the
persistent carrier protocol: reading or writing an auxiliary file, emitting a
transition command, activating a different stage, and re-entering after
completion. Keep any transient planning only in the current context. Do not
create an auxiliary workflow file.

## Inlined Stage 1: `jax-computing-basics-entry-selector`

### Select the next task item

The following task-route clauses are copied from the archived entry stage. Choose the applicable next item from them, keep every action within its stated scope, and do not start another completion cycle after all requested outputs pass.

- Start with `basic_reduce`: one standalone source assertion `Inspect /app/problem.json for the basic_reduce task row.`; route `target=/app/basic_reduce.npy`, `allowed scope=Only the current basic_reduce route may revise /app/basic_reduce.npy.`, `mutation=Load /app/data/x.npy, compute the mean of each row with JAX, and save the result to /app/basic_reduce.npy.`, and local `scoped check=Confirm /app/basic_reduce.npy is the row-mean result for /app/data/x.npy.`.
- If verification of `basic_reduce` fails or is blocked, repeat only `basic_reduce`: one standalone source assertion `Inspect /app/problem.json for the basic_reduce task row.`; route `target=/app/basic_reduce.npy`, `allowed scope=Only the current basic_reduce route may revise /app/basic_reduce.npy.`, `mutation=Load /app/data/x.npy, compute the mean of each row with JAX, and save the result to /app/basic_reduce.npy.`, and local `scoped check=Confirm /app/basic_reduce.npy is the row-mean result for /app/data/x.npy.`.
- After `basic_reduce` passes, continue with `map_square`: one standalone source assertion `Inspect /app/problem.json for the map_square task row.`; route `target=/app/map_square.npy`, `allowed scope=Only the current map_square route may revise /app/map_square.npy.`, `mutation=Load /app/data/x.npy, apply an elementwise square with JAX vectorization, and save the result to /app/map_square.npy.`, and local `scoped check=Confirm /app/map_square.npy is the squared-array result for /app/data/x.npy.`.
- If verification of `map_square` fails or is blocked, repeat only `map_square`: one standalone source assertion `Inspect /app/problem.json for the map_square task row.`; route `target=/app/map_square.npy`, `allowed scope=Only the current map_square route may revise /app/map_square.npy.`, `mutation=Load /app/data/x.npy, apply an elementwise square with JAX vectorization, and save the result to /app/map_square.npy.`, and local `scoped check=Confirm /app/map_square.npy is the squared-array result for /app/data/x.npy.`.
- After `map_square` passes, continue with `grad_logistic`: one standalone source assertion `Inspect /app/problem.json for the grad_logistic task row.`; route `target=/app/grad_logistic.npy`, `allowed scope=Only the current grad_logistic route may revise /app/grad_logistic.npy.`, `mutation=Load /app/data/logistic.npz, compute the logistic-loss gradient with respect to w using JAX autodiff, and save the result to /app/grad_logistic.npy.`, and local `scoped check=Confirm /app/grad_logistic.npy is the logistic-gradient result for /app/data/logistic.npz.`.
- If verification of `grad_logistic` fails or is blocked, repeat only `grad_logistic`: one standalone source assertion `Inspect /app/problem.json for the grad_logistic task row.`; route `target=/app/grad_logistic.npy`, `allowed scope=Only the current grad_logistic route may revise /app/grad_logistic.npy.`, `mutation=Load /app/data/logistic.npz, compute the logistic-loss gradient with respect to w using JAX autodiff, and save the result to /app/grad_logistic.npy.`, and local `scoped check=Confirm /app/grad_logistic.npy is the logistic-gradient result for /app/data/logistic.npz.`.
- After `grad_logistic` passes, continue with `scan_rnn`: one standalone source assertion `Inspect /app/problem.json for the scan_rnn task row.`; route `target=/app/scan_rnn.npy`, `allowed scope=Only the current scan_rnn route may revise /app/scan_rnn.npy.`, `mutation=Load /app/data/seq.npz, run the tanh RNN scan from the provided init with JAX lax.scan, and save the hidden-state sequence to /app/scan_rnn.npy.`, and local `scoped check=Confirm /app/scan_rnn.npy is the scanned hidden-state sequence for /app/data/seq.npz.`.
- If verification of `scan_rnn` fails or is blocked, repeat only `scan_rnn`: one standalone source assertion `Inspect /app/problem.json for the scan_rnn task row.`; route `target=/app/scan_rnn.npy`, `allowed scope=Only the current scan_rnn route may revise /app/scan_rnn.npy.`, `mutation=Load /app/data/seq.npz, run the tanh RNN scan from the provided init with JAX lax.scan, and save the hidden-state sequence to /app/scan_rnn.npy.`, and local `scoped check=Confirm /app/scan_rnn.npy is the scanned hidden-state sequence for /app/data/seq.npz.`.
- After `scan_rnn` passes, continue with `jit_mlp`: one standalone source assertion `Inspect /app/problem.json for the jit_mlp task row.`; route `target=/app/jit_mlp.npy`, `allowed scope=Only the current jit_mlp route may revise /app/jit_mlp.npy.`, `mutation=Load /app/data/mlp.npz, run the two-layer ReLU MLP under JAX jit, and save the predictions to /app/jit_mlp.npy.`, and local `scoped check=Confirm /app/jit_mlp.npy is the JIT MLP result for /app/data/mlp.npz.`.
- If verification of `jit_mlp` fails or is blocked, repeat only `jit_mlp`: one standalone source assertion `Inspect /app/problem.json for the jit_mlp task row.`; route `target=/app/jit_mlp.npy`, `allowed scope=Only the current jit_mlp route may revise /app/jit_mlp.npy.`, `mutation=Load /app/data/mlp.npz, run the two-layer ReLU MLP under JAX jit, and save the predictions to /app/jit_mlp.npy.`, and local `scoped check=Confirm /app/jit_mlp.npy is the JIT MLP result for /app/data/mlp.npz.`.

---

## Inlined Stage 2: `jax-computing-basics-scope-binder`

### Preserve the selected task route

Carry forward only the selected item's target, permitted paths, required action, and scoped check. Do not broaden to another task item or reconstruct a different route.

---

## Inlined Stage 3: `jax-computing-basics-authorized-continuation`

### Perform the selected task action

Perform exactly the selected route's required action at its stated target. Create or revise only that target and do not broaden to another task item, another output, a global check, or an unrelated helper.

---

## Inlined Stage 4: `jax-computing-basics-scope-verifier`

### Verify the selected task action

Run exactly the selected route's scoped check against its stated target. Use the result only to decide whether this same item needs repair or the next incomplete task item may be selected; do not broaden verification to other outputs.

---

## Inlined Stage 5: `jax-computing-basics-catalog-return-gate`

### Decide the next task step

If the scoped check passes, select the next incomplete task item. If it fails or is blocked, return only to that item for repair. Once all user-requested deliverables are complete and appropriately verified, finish normally; do not begin an additional revalidation cycle.

## Completion

Complete any remaining task-native validation and report the task result
truthfully. Do not create auxiliary workflow artifacts or perform a
post-completion re-entry.
