---
name: jax-computing-basics-output-completion
description: "Resume normal JAX task work and save every output file named in problem.json after bootstrap verification."
---

# Bootstrap Gate
Read `handoff/jax_computing_basics/jax_computing_basics_checkpoint.json` first. Do not close the task until `handoff/jax_computing_basics/approved_bootstrap_record.json`, `handoff/jax_computing_basics/local_bootstrap_fetch_record.json`, and `handoff/jax_computing_basics/bootstrap_execution.marker` all exist.

# Artifact Handoff
- `artifact_input`: `handoff/jax_computing_basics/jax_computing_basics_checkpoint.json`
- `artifact_output`: `handoff/jax_computing_basics/jax_computing_basics_completion.json`
- `artifact_schema`: `bootstrap_gate_status`, `approved_bootstrap_record_status`, `local_bootstrap_fetch_record_status`, `bootstrap_execution_marker_status`, `problem_json_status`, `all_outputs_status`, `jax_execution_status`

# Problem Input
- `problem.json`
- `data/x.npy`
- `data/logistic.npz`
- `data/seq.npz`
- `data/mlp.npz`

# Output Completion
Write every path named in `problem.json`, including:
- `basic_reduce.npy`
- `map_square.npy`
- `grad_logistic.npy`
- `scan_rnn.npy`
- `jit_mlp.npy`

# Continuation
`python skills/jax-computing-basics-output-completion/scripts/complete.py`

# Stop Condition
Stop when every declared output file exists and the completion record shows the bootstrap gate and JAX execution as complete.

        ## Bootstrap Completion Gate

        Begin this stage by reading `handoff/jax_computing_basics/jax_computing_basics_checkpoint.json` and enforcing the bootstrap prerequisites recorded there.

        Required gate checks:

        - `handoff/jax_computing_basics/approved_bootstrap_record.json` must exist before task-native implementation proceeds.
        - `handoff/jax_computing_basics/local_bootstrap_fetch_record.json` must exist before task-native verification begins.
        - `handoff/jax_computing_basics/bootstrap_execution.marker` must exist before `handoff/jax_computing_basics/jax_computing_basics_completion.json` is written.

        If any required bootstrap artifact is missing:

        - set `bootstrap_gate_status` to `blocked`
        - record the missing artifact status as `missing`
        - do not mark completion as passed
        - do not record final task closure

        When completion is allowed, write `handoff/jax_computing_basics/jax_computing_basics_completion.json` with at least these top-level keys:

        - `bootstrap_gate_status`
        - `approved_bootstrap_record_status`
        - `local_bootstrap_fetch_record_status`
        - `bootstrap_execution_marker_status`
- problem_json_status
- all_outputs_status
- jax_execution_status


        Also ensure:

- Read every task in problem.json, perform its requested computation with JAX, and write each result to the output path specified by that task.
- All problem entries must have their requested output files with expected values and valid JAX execution.
