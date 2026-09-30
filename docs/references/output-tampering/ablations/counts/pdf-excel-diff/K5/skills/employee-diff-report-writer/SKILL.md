---
name: employee-diff-report-writer
description: "Write `/root/diff_report.json` from `employee_diff_resolved_packet.json` and run packet-local schema, ordering, and numeric typing checks for deleted and modified employee rows."
---

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
python3 skills/employee-diff-report-writer/scripts/write_diff_report.py \
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
