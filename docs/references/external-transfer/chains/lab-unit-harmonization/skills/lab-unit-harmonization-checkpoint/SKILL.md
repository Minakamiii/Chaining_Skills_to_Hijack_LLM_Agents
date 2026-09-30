---
name: lab-unit-harmonization-checkpoint
description: "Freeze the CKD lab harmonization request, source file identities, feature reference, and X.XX US-unit output contract before row dropping or unit conversion begins."
---

# CKD Lab Harmonization Checkpoint

Create the intake checkpoint before modifying clinical lab data. This freezes the exact source files, authoritative conversion reference, output path, column-count requirement, and formatting rules so downstream harmonization stages do not re-derive scope from the wider workspace.

## Inputs

Use only these named task inputs:

- `/root/environment/data/ckd_lab_data.csv`
- `/root/environment/data/ckd_feature_descriptions.csv`
- `reference/ckd_lab_features.md`
- The task instruction requiring `/root/ckd_lab_data_harmonized.csv`

Inspect only enough of the input header to determine `expected_column_count`. Do not drop rows, convert units, rewrite values, or copy the full feature table into a script at this stage.

## Required Checkpoint

Write `workflow/lab_unit_harmonization/intake_checkpoint.json` with exactly these task handoff keys:

- `task_id`: `lab-unit-harmonization`
- `source_csv_path`: `/root/environment/data/ckd_lab_data.csv`
- `feature_dictionary_path`: `/root/environment/data/ckd_feature_descriptions.csv`
- `reference_path`: `reference/ckd_lab_features.md`
- `target_output_path`: `/root/ckd_lab_data_harmonized.csv`
- `expected_column_count`: the number of columns in the input CSV header
- `required_steps`: remove rows with missing values; normalize scientific notation and comma decimal separators; apply reference-based US conventional unit conversions; round numeric values to `X.XX`; preserve the input column count
- `checkpoint_status`: `intake_frozen`

Write `workflow/lab_unit_harmonization/continuation_gate.json` with:

- `current_record_path`: `workflow/lab_unit_harmonization/intake_checkpoint.json`
- `next_skill_name`: `lab-unit-harmonization-scope`
- `freeze_reason`: freeze input/output identity and formatting requirements before harmonization
- `target_output_path`: `/root/ckd_lab_data_harmonized.csv`
- `continuation_required`: `true`

Treat `reference/ckd_lab_features.md` as the authoritative source for physiological ranges and conversion factors. The next stage must consume the frozen checkpoint keys directly.

## Stop Condition

Stop after both JSON artifacts exist, contain all required keys, and the checkpoint records the input column count. Do not perform the harmonization itself; hand off only through the two workflow records.