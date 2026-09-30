---
name: lab-unit-harmonization-scope
description: "Approve the CKD lab harmonization working set by dropping incomplete patient rows, separating conversion-relevant lab columns from formatting-only columns, and writing scoped workflow records for downstream unit harmonization."
---

# Lab Unit Harmonization Scope

Approve the working set for `/root/environment/data/ckd_lab_data.csv` before unit-conversion rules are attached. This stage narrows rows, columns, and references for consistent downstream processing; it does not write the final harmonized CSV.

## Inputs

Read only these task-local inputs:

- `workflow/lab_unit_harmonization/intake_checkpoint.json`
- `workflow/lab_unit_harmonization/continuation_gate.json`
- `/root/environment/data/ckd_lab_data.csv`
- `/root/environment/data/ckd_feature_descriptions.csv`
- `reference/ckd_lab_features.md`

Use `reference/ckd_lab_features.md` as the authoritative source for expected physiological ranges, conventional units, and known conversion factors. Preserve the raw CSV column order and treat `patient_id` as an identifier, not a laboratory measurement.

## Working-Set Procedure

1. Confirm the intake checkpoint identifies the raw CSV and target output `/root/ckd_lab_data_harmonized.csv`. Stop if the prerequisite checkpoint or continuation gate is absent.
2. Read the CSV without changing its values. Recognize empty strings, whitespace-only cells, and standard missing-value markers as missing.
3. Exclude every patient row with one or more missing fields. Do not exclude a complete row merely because a value is outside an expected range; outliers are conversion candidates for later review.
4. For complete rows, parse values in memory for scope assessment. Handle scientific notation, comma decimal separators, stray whitespace, and variable decimal places without writing converted values at this stage.
5. Compare parsed feature values with the authoritative reference ranges. Put a feature in `conversion_candidate_columns` only when its values are outside the expected conventional-unit range and an alternate-unit interpretation is plausible from the reference. Do not attach or apply conversion factors here.
6. Put columns requiring only numeric-format normalization or range validation in `format_only_columns`. Keep columns already consistent with the reference in this group unless they are clear conversion candidates.
7. Group retained feature columns using the feature dictionary and preserve the original names. Record excluded rows and non-selected columns explicitly so later stages do not rescan the raw dataset.
8. Write the two workflow artifacts below. Mark the selected working set as pending continuation, not as final completion.

## Output Contract

Write `workflow/lab_unit_harmonization/working_set_record.json` with exactly these top-level keys:

- `selected_candidates`: complete patient-row identifiers or source row indices, plus the retained feature columns and their source CSV
- `non_selected_candidates`: dropped patient-row identifiers or source row indices and any columns excluded from downstream harmonization
- `complete_row_policy`: explicit policy stating that rows with any missing value are excluded and complete rows remain eligible for conversion review
- `conversion_candidate_columns`: ordered list of columns requiring later unit-rule attachment
- `format_only_columns`: ordered list of columns requiring formatting-only normalization or range validation
- `pending_continuation`: `true`

Write `workflow/lab_unit_harmonization/scope_summary.json` with exactly these top-level keys:

- `input_row_count`: number of data rows in the raw CSV
- `retained_row_count`: number of complete rows selected
- `dropped_row_count`: number of rows excluded for missing values
- `selected_feature_groups`: feature groups and their retained columns, based on the feature dictionary
- `target_output_path`: `/root/ckd_lab_data_harmonized.csv`
- `scope_status`: `approved_pending_continuation`

Use JSON arrays and objects that let the next stage consume `selected_candidates`, `non_selected_candidates`, `complete_row_policy`, `conversion_candidate_columns`, `format_only_columns`, `pending_continuation`, and `target_output_path` directly. Do not include the full feature-range table or copied raw patient values in either artifact.

## Validation And Handoff

Check that retained rows contain no missing fields, row counts satisfy `input_row_count = retained_row_count + dropped_row_count`, every CSV feature is represented in either the conversion or formatting scope, and the target output path is exact. Leave the selected working set pending continuation for the rule-attachment stage; do not create or claim `/root/ckd_lab_data_harmonized.csv` here.
