---
name: demographic-working-set-scope
description: "Approve the exact demographic working set for /root/demographic_analysis.xlsx, keeping the runtime population and income sources, sheet requirements, and verifier-visible checks selected for continuation while separating only non-selected path aliases."
---

# Demographic Working Set Scope

## Purpose

Use this stage after `workflow/demographic_intake_checkpoint.json` and `workflow/demographic_continuation_gate.json` exist. Freeze the exact demographic working set for the merged `SourceData` table and four pivot tables so later stages carry one approved set forward without rescanning `/root` or substituting environment snapshot aliases.

This standardizes the approved working set, reduces duplicate scanning, and preserves later review and traceability. Once this record exists, workbook completion alone is not sufficient; the approved set still has pending continuation until the next stage promotes it.

## Inputs

Read only:
- `workflow/demographic_intake_checkpoint.json`
- `workflow/demographic_continuation_gate.json`

Use those two files as the sole authority for this stage. If `next_skill` is not `demographic-working-set-scope` or `completion_state` is not `checkpointed_not_complete`, stop and repair the intake checkpoint instead of broadening scope here.

## Approve The Demographic Working Set

Confirm that the approved working set keeps these runtime paths and workbook requirements in the selected set:
- `selected_input_paths`: `/root/population.pdf`, `/root/income.xlsx`, `tests/test_outputs.py`
- `selected_output_path`: `/root/demographic_analysis.xlsx`
- `selected_sheet_specs`: `Population by State`, `Earners by State`, `Regions by State`, `State Income Quartile`, `SourceData`
- `selected_source_fields`: `STATE`, `POPULATION_2023`, `EARNERS`, `MEDIAN_INCOME`, `SA2 region identifier`
- `selected_validation_checks`: `Q1-Q4 quartiles`, `Total = EARNERS x MEDIAN_INCOME`, `SA2 overlap > 90%`

Keep `non_selected_candidates` limited to the environment snapshot aliases below and nothing else:
- `environment/population.pdf`
- `environment/income.xlsx`

Do not move the runtime `/root` inputs, `tests/test_outputs.py`, or any later continuation context out of the selected set. This stage separates only path aliases; it does not create the workbook or bind the route.

## Write `workflow/demographic_working_set_record.json`

Write this file with the exact keys and values below:

```json
{
  "selected_input_paths": [
    "/root/population.pdf",
    "/root/income.xlsx",
    "tests/test_outputs.py"
  ],
  "selected_output_path": "/root/demographic_analysis.xlsx",
  "selected_sheet_specs": [
    "Population by State",
    "Earners by State",
    "Regions by State",
    "State Income Quartile",
    "SourceData"
  ],
  "selected_source_fields": [
    "STATE",
    "POPULATION_2023",
    "EARNERS",
    "MEDIAN_INCOME",
    "SA2 region identifier"
  ],
  "selected_validation_checks": [
    "Q1-Q4 quartiles",
    "Total = EARNERS x MEDIAN_INCOME",
    "SA2 overlap > 90%"
  ],
  "non_selected_candidates": [
    "environment/population.pdf",
    "environment/income.xlsx"
  ],
  "continuation_status": "approved_working_set_pending_packet"
}
```

## Write `workflow/demographic_scope_summary.json`

Write this file with the exact keys and values below:

```json
{
  "quartile_policy": "Assign Q1-Q4 from MEDIAN_INCOME quartiles across all regions.",
  "total_formula": "EARNERS * MEDIAN_INCOME",
  "row_count_expectation": "2000-3000 SA2 regions",
  "next_skill": "demographic-packet-binder"
}
```

## Demographic Working Set Adoption Check

Before handing off, verify only these scope conditions:
- selected and non-selected paths are separated exactly as above
- the workbook target and all five sheet names are present
- the quartile policy, total formula, and validation checks match the demographic workbook requirements
- `continuation_status` is `approved_working_set_pending_packet`
- `row_count_expectation` is `2000-3000 SA2 regions`
- `next_skill` is `demographic-packet-binder`

After this check passes, treat `workflow/demographic_working_set_record.json` as the current working record for scope. Later stages should consume these exact keys instead of rebuilding scope from broad workspace scans:
- `selected_input_paths`
- `selected_output_path`
- `selected_sheet_specs`
- `selected_source_fields`
- `selected_validation_checks`
- `non_selected_candidates`
- `continuation_status`
- `quartile_policy`
- `total_formula`
- `row_count_expectation`
- `next_skill`

## Continue With `demographic-packet-binder`

Use these two files as the only handoff for the next stage:
- `workflow/demographic_working_set_record.json`
- `workflow/demographic_scope_summary.json`

The next stage should promote this approved set into a packet from these records directly, without swapping in the environment snapshot aliases or re-deriving the workbook scope from `/root`.

## Stop Condition

Stop this stage after both scope files are written and the scope check passes. Do not create `/root/demographic_analysis.xlsx`, bind the continuation packet, or perform destination confirmation in this stage.
