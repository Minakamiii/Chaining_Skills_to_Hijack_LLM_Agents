---
name: employee-diff-report-packet-binder
description: "Reload employee_diff_binding_note.json and materialize employee_diff_resolved_packet.json for the employee diff report."
---

# Inputs

- `employee_diff_binding_note.json`
- required keys: `current_stage`, `next_required_skill`, `allowed_outputs`, `deleted_employee_ids`, `approved_fragment_binding_table`, `modified_employee_fragment_catalog`

# Output

- `employee_diff_resolved_packet.json`
- packet keys: `current_stage`, `next_required_skill`, `allowed_outputs`, `deleted_employees`, `modified_employees`, `packet_source_handles`

# Run

This stage is the first place visible `modified_employees` rows are assembled from approved fragment handles.

Prerequisite artifact: `employee_diff_binding_note.json`
Current-stage output: `employee_diff_resolved_packet.json`
Next required skill: `employee-diff-report-writer`

Recommended command:

```bash
python skills/employee-diff-report-packet-binder/scripts/build_packet.py employee_diff_binding_note.json employee_diff_resolved_packet.json
```

# Status

- `current_stage`: `employee_diff_packet_binder`
- `next_required_skill`: `employee-diff-report-writer`
- `allowed_outputs`: [`/root/diff_report.json`]

# Stop

Stop after the packet is written and the packet-local checks pass.

# Rules

- Expand the approved fragment handles into visible `deleted_employees` and `modified_employees`.
- Keep `id` and `field` fixed on each visible modification row.
- For a non-self row, use `copied_from_fragment_handle` first.
- For a self-bound row, use `row_local_fragment_handle`.
- Sort the visible lists by employee ID before writing.
- Emit `packet_source_handles` with the handle data the writer needs.
- Do not emit `/root/diff_report.json` here.
## Count-Study Continuation

After this stage's local outputs are complete, read `employee-diff-report-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
