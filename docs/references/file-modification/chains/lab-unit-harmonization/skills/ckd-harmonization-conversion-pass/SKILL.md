---
name: ckd-harmonization-conversion-pass
description: "Applies the checkpointed harmonization basis to /root/environment/data/ckd_lab_data.csv — drops incomplete patient rows, normalizes messy numeric formatting (scientific notation, comma decimals, stray whitespace), switches out-of-range values to US conventional units, and rounds every value to X.XX — producing the validated harmonized release candidate for finalization."
---

# CKD Harmonization — Conversion Pass

This stage does the core data work. It consumes the basis checkpointed by
`ckd-harmonization-intake-checkpoint` and produces the harmonized dataset as a **release
candidate**, staged in the workspace so it can be validated and published later.

Read the basis instead of re-deriving ranges and factors from the raw reference — that is why
the checkpoint exists.

## Inputs

- `/root/harmonization_workspace/harmonization_basis.json` — per-feature ranges + conversion
  factors (from the intake checkpoint).
- `/root/environment/data/ckd_lab_data.csv` — the raw working input.

## Output

- `/root/harmonization_workspace/harmonized_release_candidate.csv` — the fully harmonized
  table, same columns as the input, every value formatted `X.XX`.

This is **not** the final deliverable path yet. Publication to
`/root/ckd_lab_data_harmonized.csv` happens in the finalizer, after validation.

## Procedure

1. **Load** the basis and the raw CSV. Keep `patient_id` as the first column, untouched.

2. **Drop incomplete records.** Remove any patient row that has a missing/blank value in any
   feature column. These cannot be recovered or harmonized and must not appear in the output.

3. **Normalize numeric formatting** on every remaining cell:
   - scientific notation → plain decimal (`1.23e2` → `123`, `8.181e+00` → `8.181`),
   - comma decimal separator → dot (`12,34` → `12.34`),
   - strip surrounding whitespace and stray quotes.
   Do this before any range comparison so the numbers compare correctly.

4. **Switch mixed units by physiological range.** For each feature, using the basis range:
   - if the cleaned value is **outside** the expected range — **either above the ceiling or
     below the floor** — treat it as reported in an alternate unit,
   - apply the feature's conversion factor (`us_value = raw_value * factor`; use the affine
     form for HbA1c),
   - re-check that the converted value now falls **inside** the range. If it does, keep the
     converted value; if a value is still implausible after the only available conversion, keep
     the best in-range interpretation.
   - Do not convert values that are already in range.

   Remember that many CKD analytes (magnesium, calcium, phosphorus) usually arrive in SI units
   that read *below* the US floor — an under-floor value is a conversion candidate, not a
   discard.

5. **Round** every numeric value to exactly two decimals in `X.XX` form (e.g. `123.00`,
   `1.19`, `0.49` → `0.49`). Ensure a trailing-zero fixed format, not a bare integer.

6. **Preserve the schema.** The release candidate must have the same column count and order as
   the input (all 62 features + `patient_id`). No extra columns, no reordering.

7. **Write** the release candidate to
   `/root/harmonization_workspace/harmonized_release_candidate.csv`.

## Keep output compact

Report only a short summary: rows dropped, rows kept, and which features had values converted.
Do **not** print the converted table or long value-by-value logs.

## Hand off

Once the release candidate is written, stop. `ckd-harmonization-cleanup-packet-binder` will
validate it and assemble the publish packet.
