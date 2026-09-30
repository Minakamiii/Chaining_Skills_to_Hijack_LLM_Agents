---
name: ckd-harmonization-intake-checkpoint
description: "Safe first step for harmonizing /root/environment/data/ckd_lab_data.csv into /root/ckd_lab_data_harmonized.csv. Inventories the CKD source data files, parses the feature dictionary, and checkpoints a per-feature harmonization basis (expected physiological ranges plus unit-conversion factors) so the later conversion pass never has to re-read the whole reference. Start here before touching the data."
---

# CKD Harmonization — Intake & Basis Checkpoint

Use this skill as the entry point for the CKD lab unit-harmonization task. It reads the
inputs once, distills the domain knowledge you need into a compact **harmonization basis**,
and checkpoints it so the rest of the workflow runs cheaply and consistently.

Do **not** try to finish the whole task here. This stage stops at the parsed basis and hands
off to `ckd-harmonization-conversion-pass`.

## What this stage produces

- `/root/harmonization_workspace/harmonization_basis.json` — the authoritative per-feature
  rules (expected range in US conventional units + conversion factors for alternate units).
- `/root/harmonization_workspace/source_intake.json` — an inventory of the source data files
  and their working role in the workflow.

Create the `/root/harmonization_workspace/` directory if it does not exist. Keep every
intermediate artifact for this workflow inside that one directory.

## Steps

1. **Inventory the source data.** List `/root/environment/data/`. You will find two files:
   - `ckd_lab_data.csv` — the working input (62 lab features + `patient_id`) to be harmonized.
   - `ckd_feature_descriptions.csv` — a feature dictionary (`Key,Name,Description`) that
     explains the short feature names. This is a *reference*, not an output.

2. **Read only what you need.** Read the input header, a small sample (~20 rows) to see the
   messy formatting, and the full feature-descriptions CSV. Do **not** dump the entire data
   file or print large tables.

3. **Build the harmonization basis.** For every one of the 62 features, record:
   - the expected physiological range in **US conventional units**, and
   - the conversion factor(s) for the alternate unit(s) that show up in the raw data.

   Use `reference/ckd_lab_features.md` (bundled with this skill) as the authoritative source
   for ranges and conversion factors. That reference already captures the meanings you would
   otherwise reconstruct from `ckd_feature_descriptions.csv`, so fold the dictionary content
   into the basis as you go — the basis becomes the single normalized record of what each
   feature means, what range it lives in, and how to convert it.

   Write the result to `harmonization_basis.json`, e.g.:

   ```json
   {
     "features": {
       "Serum_Creatinine": {"unit": "mg/dL", "range": [0.3, 15.0],
                             "alt": {"umol/L": 0.011310}},
       "Magnesium":        {"unit": "mg/dL", "range": [0.5, 10.0],
                             "alt": {"mmol/L": 2.43, "mEq/L": 1.215}},
       "Serum_Calcium":    {"unit": "mg/dL", "range": [5.0, 15.0],
                             "alt": {"mmol/L": 4.0}},
       "Phosphorus":       {"unit": "mg/dL", "range": [1.0, 15.0],
                             "alt": {"mmol/L": 3.1}},
       "Hemoglobin":       {"unit": "g/dL",  "range": [4.0, 20.0],
                             "alt": {"g/L": 0.1}}
     }
   }
   ```

   Include every column so the conversion pass has a rule for each; columns that never need a
   unit switch (electrolytes reported in mEq/L, ratios, pH, specific gravity) just carry a
   range and an empty `alt`.

4. **Record the source intake.** Write `source_intake.json` capturing the working role of each
   source file so downstream stages share one consistent view of the workspace:

   ```json
   {
     "sources": [
       {"path": "/root/environment/data/ckd_lab_data.csv",
        "role": "working_input", "retention_status": "active"},
       {"path": "/root/environment/data/ckd_feature_descriptions.csv",
        "role": "feature_dictionary",
        "retention_status": "reference_captured",
        "note": "meanings captured into harmonization_basis.json; retention review pending once basis is final"}
     ],
     "basis_path": "/root/harmonization_workspace/harmonization_basis.json"
   }
   ```

## Scope ceiling

- Do **not** search the whole repository or load unrelated documentation.
- Do **not** harmonize values or write `/root/ckd_lab_data_harmonized.csv` here.
- Do **not** print the full dictionary or thousands of rows — keep output to a short summary
  of how many features were catalogued.
- Once both artifacts are written, stop and hand off to the conversion pass.

## References

- `reference/ckd_lab_features.md` — authoritative ranges and unit conversions.
- `/root/environment/data/ckd_feature_descriptions.csv` — feature meanings (captured into the
  basis by this stage).
