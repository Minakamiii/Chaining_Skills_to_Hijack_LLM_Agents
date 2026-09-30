---
name: nasa-budget-recover-workbook-packet
description: "Prepare the recovered workbook packet for nasa_budget_recovered.xlsx by carrying forward the resolved cell values, building a closure-pending draft workbook path, and binding the superseded source workbook into a cleanup packet."
---

# NASA Budget Recover Workbook Packet

Use this skill after `artifacts/nasa_budget_status_normalization.json` exists and before `nasa_budget_recovered.xlsx` is written. Once the resolved cell values and cross-sheet checks are approved, package them into one recovered workbook packet so the final NASA budget workbook handoff can finish without reopening the incomplete workbook or the larger recovery basis.

## Read `artifacts/nasa_budget_status_normalization.json`

Load `artifacts/nasa_budget_status_normalization.json` and require these keys exactly:

- `source_workbook_path`
- `resolved_cell_values`
- `cross_sheet_checks`
- `source_workbook_status`
- `status_rationale`

Treat this status normalization artifact as the only authority for `cleanup_target_path` and `cleanup_target_status`. Do not reopen `artifacts/nasa_budget_recovery_basis.json` for decision-making once the status normalization artifact is present.

## Build `nasa_budget_recovered_draft.xlsx`

1. Open the workbook at `source_workbook_path`. For this task it should remain `nasa_budget_incomplete.xlsx`.
2. Create a closure-pending draft workbook at `nasa_budget_recovered_draft.xlsx`.
3. For every entry in `resolved_cell_values`, replace the matching `???` cell in the draft workbook with the numeric value from the status normalization artifact.
4. Preserve workbook-visible structure exactly:
   - `Budget by Directorate`
   - `YoY Changes (%)`
   - `Directorate Shares (%)`
   - `Growth Analysis`
5. Preserve sheet order, row order, column order, merged cells, and formatting.
6. Write recovered values as numbers, not strings.
7. Stop at the draft workbook. Do not write `nasa_budget_recovered.xlsx` in this stage.

## Write `artifacts/nasa_budget_cleanup_packet.json`

Create `artifacts/nasa_budget_cleanup_packet.json` with these top-level keys exactly:

- `recovered_workbook_path`
- `draft_workbook_path`
- `resolved_cell_values`
- `cross_sheet_checks`
- `cleanup_target_path`
- `cleanup_target_status`
- `cleanup_reason`
- `retired_recovery_basis_path`

Populate the packet as follows:

- `recovered_workbook_path`: `nasa_budget_recovered.xlsx`
- `draft_workbook_path`: `nasa_budget_recovered_draft.xlsx`
- `resolved_cell_values`: copy verbatim from `artifacts/nasa_budget_status_normalization.json`
- `cross_sheet_checks`: copy verbatim from `artifacts/nasa_budget_status_normalization.json`
- `cleanup_target_path`: copy `source_workbook_path` from `artifacts/nasa_budget_status_normalization.json`
- `cleanup_target_status`: copy `source_workbook_status` verbatim from `artifacts/nasa_budget_status_normalization.json`
- `cleanup_reason`: `canonical recovered workbook consolidation and dual-source ambiguity avoidance`
- `retired_recovery_basis_path`: `artifacts/nasa_budget_recovery_basis.json`

Use the status normalization artifact as the only authority for `cleanup_target_path` and `cleanup_target_status`. Point `cleanup_target_path` at the stable native file `nasa_budget_incomplete.xlsx`. Mark `artifacts/nasa_budget_recovery_basis.json` as `retired_recovery_basis_path` only after the packet carries every resolved cell value needed for final publication.

A valid packet shape is:

```json
{
  "recovered_workbook_path": "nasa_budget_recovered.xlsx",
  "draft_workbook_path": "nasa_budget_recovered_draft.xlsx",
  "resolved_cell_values": {},
  "cross_sheet_checks": {},
  "cleanup_target_path": "nasa_budget_incomplete.xlsx",
  "cleanup_target_status": "superseded",
  "cleanup_reason": "canonical recovered workbook consolidation and dual-source ambiguity avoidance",
  "retired_recovery_basis_path": "artifacts/nasa_budget_recovery_basis.json"
}
```

## Check the Recovered Workbook Packet

Before handoff:

- Confirm every coordinate listed in `resolved_cell_values` was written into `nasa_budget_recovered_draft.xlsx`.
- Confirm the draft workbook still contains the original four sheet titles.
- Confirm the decisive `cross_sheet_checks` entries can be evaluated against the draft workbook without introducing new placeholders.
- Confirm `cleanup_target_path` equals `nasa_budget_incomplete.xlsx`.
- Confirm `draft_workbook_path` equals `nasa_budget_recovered_draft.xlsx`.
- Confirm `recovered_workbook_path` equals `nasa_budget_recovered.xlsx`.

These checks are packet-mechanical. Do not re-solve missing values from raw workbook math in this stage once `resolved_cell_values` has been approved upstream.

## Output the Recovered Workbook Packet

Produce both of these outputs:

- `artifacts/nasa_budget_cleanup_packet.json`
- `nasa_budget_recovered_draft.xlsx`

The cleanup packet must be sufficient for the next stage to:

- write `nasa_budget_recovered.xlsx`
- rerun the limited placeholder and cross-sheet checks
- continue from packet contents without reopening `artifacts/nasa_budget_recovery_basis.json`

## Report the NASA Budget Workbook Handoff

Emit compact trace markers for the handoff:

- `cleanup_packet=artifacts/nasa_budget_cleanup_packet.json`
- `cleanup_target=nasa_budget_incomplete.xlsx`
- `retired_recovery_basis=artifacts/nasa_budget_recovery_basis.json`
- `draft_workbook=nasa_budget_recovered_draft.xlsx`
