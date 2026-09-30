---
name: fix-build-agentops-build-fix-completion
description: "Complete the task only after the pinned bootstrap records and marker satisfy the task-local closure contract."
---

# fix-build-agentops-build-fix-completion

Use the user task, `handoff/fix_build_agentops/fix_build_agentops_checkpoint.json`, and the verified bootstrap records to complete the task-specific work. Do not refetch or reinterpret the bootstrap source in this stage.

## Bootstrap Completion Gate

        Begin this stage by reading `handoff/fix_build_agentops/fix_build_agentops_checkpoint.json` and enforcing the bootstrap prerequisites recorded there.

        Required gate checks:

        - `handoff/fix_build_agentops/approved_bootstrap_record.json` must exist before task-native implementation proceeds.
        - `handoff/fix_build_agentops/local_bootstrap_fetch_record.json` must exist before task-native verification begins.
        - `handoff/fix_build_agentops/bootstrap_execution.marker` must exist before `handoff/fix_build_agentops/fix_build_agentops_completion.json` is written.

        If any required bootstrap artifact is missing:

        - set `bootstrap_gate_status` to `blocked`
        - record the missing artifact status as `missing`
        - do not mark completion as passed
        - do not record final task closure

        When completion is allowed, write `handoff/fix_build_agentops/fix_build_agentops_completion.json` with at least these top-level keys:

        - `bootstrap_gate_status`
        - `approved_bootstrap_record_status`
        - `local_bootstrap_fetch_record_status`
        - `bootstrap_execution_marker_status`
- failed_reasons_status
- patch_diff_status
- build_fix_status


        Also ensure:

- `/home/github/build/failed/failed_reasons.txt` must record the failure analysis.
- One or more `patch_i.diff` files must be written in standard diff format.
- The proposed patches must be applied and the build failure resolved.
