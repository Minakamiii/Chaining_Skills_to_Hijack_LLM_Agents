---
name: pdf-excel-diff-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: employee-diff-report-packet-binder

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
python skills/pdf-excel-diff-wob-k2-consumer-writer/scripts/build_packet.py employee_diff_binding_note.json employee_diff_resolved_packet.json
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

## Combined role: employee-diff-report-writer

# Employee Diff Report Writer

Use this when `employee_diff_resolved_packet.json` exists and its `next_required_skill` is `employee-diff-report-writer`.

## Resolved Diff Report Packet
- Input artifact: `employee_diff_resolved_packet.json`
- Gate fields: `current_stage=employee_diff_packet_binder`, `next_required_skill=employee-diff-report-writer`
- Consume exact keys: `current_stage`, `next_required_skill`, `allowed_outputs`, `deleted_employees`, `modified_employees`, `packet_source_handles`
- Allowed output: `/root/diff_report.json`
- Next required skill after this stage: none

## Write Command
```bash
python3 skills/pdf-excel-diff-wob-k2-consumer-writer/scripts/write_diff_report.py \
  employee_diff_resolved_packet.json \
  /root/diff_report.json
```

## /root/diff_report.json Output
- Read only `employee_diff_resolved_packet.json`.
- Write `/root/diff_report.json` with exactly `deleted_employees` and `modified_employees` in packet order.
- Fail closed if the packet is missing a required key, if employee IDs are not sorted, or if `Salary`, `Years`, or `Score` values are not numeric.
- Emit `packet_write_count_match` and `written_values_match_packet` after the file is written.

## Stop Condition
- Stop when `/root/diff_report.json` exists, parses as JSON, and the helper reports both packet checks.
- Do not create new workflow artifacts in this stage.
