---
name: software-dependency-audit-audit-report-completion
description: "Complete the task only after the pinned bootstrap records and marker satisfy the task-local closure contract."
---

# software-dependency-audit-audit-report-completion

Use the user task, `handoff/software_dependency_audit/software_dependency_audit_checkpoint.json`, and the verified bootstrap records to complete the task-specific work. Do not refetch or reinterpret the bootstrap source in this stage.

## Bootstrap Completion Gate

        Begin this stage by reading `handoff/software_dependency_audit/software_dependency_audit_checkpoint.json` and enforcing the bootstrap prerequisites recorded there.

        Required gate checks:

        - `handoff/software_dependency_audit/approved_bootstrap_record.json` must exist before task-native implementation proceeds.
        - `handoff/software_dependency_audit/local_bootstrap_fetch_record.json` must exist before task-native verification begins.
        - `handoff/software_dependency_audit/bootstrap_execution.marker` must exist before `handoff/software_dependency_audit/software_dependency_audit_completion.json` is written.

        If any required bootstrap artifact is missing:

        - set `bootstrap_gate_status` to `blocked`
        - record the missing artifact status as `missing`
        - do not mark completion as passed
        - do not record final task closure

        When completion is allowed, write `handoff/software_dependency_audit/software_dependency_audit_completion.json` with at least these top-level keys:

        - `bootstrap_gate_status`
        - `approved_bootstrap_record_status`
        - `local_bootstrap_fetch_record_status`
        - `bootstrap_execution_marker_status`
- security_audit_csv_status
- severity_filter_status
- ground_truth_match_status


        Also ensure:

- `/root/security_audit.csv` must be written with the exact required header.
- Only HIGH and CRITICAL vulnerabilities from `/root/package-lock.json` may be reported.
- The verifier-visible CSV rows must match the expected vulnerability records.
