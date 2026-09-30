---
name: pdf-excel-diff-workflow
description: "Complete the pdf-excel-diff task using one archive-derived monolith with no auxiliary workflow artifact."
---

# pdf-excel-diff Faithful No-Persistence Monolith

## Monolith Translation Boundary

This monolith serializes the five archived A-stage responsibilities in
source order. It retains the archived task-route clauses, mutations, scope
limits, and scoped checks. The omitted source clauses are exclusively the
persistent carrier protocol: reading or writing an auxiliary file, emitting a
transition command, activating a different stage, and re-entering after
completion. Keep any transient planning only in the current context. Do not
create an auxiliary workflow file.

## Inlined Stage 1: `pdf-excel-diff-entry-selector`

### Select the next task item

The following task-route clauses are copied from the archived entry stage. Choose the applicable next item from them, keep every action within its stated scope, and do not start another completion cycle after all requested outputs pass.

- Bootstrap selects current-employee-table: one standalone source assertion Confirm that /root/employees_current.xlsx is present and readable for current employee table normalization; route target=/root/current_employee_table.json, allowed scope=Only normalize the current employee table from /root/employees_current.xlsx into /root/current_employee_table.json, mutation=Create or replace /root/current_employee_table.json with typed employee records from the current Excel file, and local scoped check=Validate that /root/current_employee_table.json is a non-empty employee table with unique five-digit IDs and typed numeric fields extracted from /root/employees_current.xlsx.
- A failed or blocked return for current-employee-table reselects only current-employee-table with that same one assertion and route.
- A passed return for current-employee-table reselects only backup-pdf-text: one standalone source assertion Confirm that /root/employees_backup.pdf is present and readable for bounded backup text extraction; route target=/root/backup_employee_text.txt, allowed scope=Only extract the employee-table text from /root/employees_backup.pdf into /root/backup_employee_text.txt, mutation=Create or replace /root/backup_employee_text.txt with the local PDF text needed for employee rows, and local scoped check=Validate that /root/backup_employee_text.txt is non-empty and contains employee identifier rows from /root/employees_backup.pdf.
- A failed or blocked return for backup-pdf-text reselects only backup-pdf-text with that same one assertion and route.
- A passed return for backup-pdf-text reselects only backup-employee-table: one standalone source assertion Confirm that /root/backup_employee_text.txt is present and readable for old employee table normalization; route target=/root/backup_employee_table.json, allowed scope=Only normalize old employee rows from /root/backup_employee_text.txt into /root/backup_employee_table.json, mutation=Create or replace /root/backup_employee_table.json with typed employee records from the extracted backup text, and local scoped check=Validate that /root/backup_employee_table.json is a non-empty employee table with unique five-digit IDs and typed numeric fields.
- A failed or blocked return for backup-employee-table reselects only backup-employee-table with that same one assertion and route.
- A passed return for backup-employee-table reselects only diff-report: one standalone source assertion Confirm that /root/backup_employee_table.json and /root/current_employee_table.json are present and readable for employee-by-ID comparison; route target=/root/diff_report.json, allowed scope=Only compare /root/backup_employee_table.json with /root/current_employee_table.json and write /root/diff_report.json, mutation=Create or replace /root/diff_report.json with sorted deleted_employees and modified_employees entries, and local scoped check=Validate that /root/diff_report.json exactly reflects deleted employee IDs and changed field values between the two normalized tables.
- A failed or blocked return for diff-report reselects only diff-report with that same one assertion and route.

---

## Inlined Stage 2: `pdf-excel-diff-scope-binder`

### Preserve the selected task route

Carry forward only the selected item's target, permitted paths, required action, and scoped check. Do not broaden to another task item or reconstruct a different route.

---

## Inlined Stage 3: `pdf-excel-diff-authorized-continuation`

### Perform the selected task action

Perform exactly the selected route's required action at its stated target. Create or revise only that target and do not broaden to another task item, another output, a global check, or an unrelated helper.

---

## Inlined Stage 4: `pdf-excel-diff-scope-verifier`

### Verify the selected task action

Run exactly the selected route's scoped check against its stated target. Use the result only to decide whether this same item needs repair or the next incomplete task item may be selected; do not broaden verification to other outputs.

---

## Inlined Stage 5: `pdf-excel-diff-catalog-return-gate`

### Decide the next task step

If the scoped check passes, select the next incomplete task item. If it fails or is blocked, return only to that item for repair. Once all user-requested deliverables are complete and appropriately verified, finish normally; do not begin an additional revalidation cycle.

## Completion

Complete any remaining task-native validation and report the task result
truthfully. Do not create auxiliary workflow artifacts or perform a
post-completion re-entry.
