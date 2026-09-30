# CKD Lab Features — Ranges and Unit Conversions

Authoritative reference for harmonizing `ckd_lab_data.csv` into **US conventional units**.

## How to use this file

For each feature you have:

- an **expected physiological range** in US conventional units, and
- one or more **alternate units** with a **multiply factor** that converts an alternate-unit
  value into the US unit (`us_value = raw_value * factor`).

Detection rule: a cleaned numeric value that falls **outside** the expected range — whether it
is **above the ceiling or below the floor** — is a strong signal that it was reported in an
alternate unit. Apply the matching factor, then confirm the converted value now lands inside
the range. Both directions matter: several analytes (magnesium, calcium, phosphorus) most often
arrive in SI units that read *below* the US floor before conversion.

Columns not listed as needing conversion still get a range so out-of-range junk is caught, but
their `alt` set is empty (mEq/L electrolytes, ratios, pH, specific gravity, and counts whose SI
and US numbers coincide).

## Feature table

| Feature | US unit | Expected range | Alternate unit → multiply factor |
|---|---|---|---|
| Serum_Creatinine | mg/dL | 0.3 – 15.0 | µmol/L → 0.011310 |
| BUN | mg/dL | 5 – 150 | mmol/L (urea) → 2.80 |
| eGFR | mL/min/1.73m² | 3 – 150 | — |
| Cystatin_C | mg/L | 0.4 – 8.0 | — |
| BUN_Creatinine_Ratio | ratio | 3 – 40 | — |
| Sodium | mEq/L | 115 – 160 | — (= mmol/L) |
| Potassium | mEq/L | 2.0 – 8.0 | — (= mmol/L) |
| Chloride | mEq/L | 75 – 125 | — (= mmol/L) |
| Bicarbonate | mEq/L | 8 – 45 | — (= mmol/L) |
| Anion_Gap | mEq/L | 3 – 30 | — |
| Magnesium | mg/dL | 0.5 – 10.0 | mmol/L → 2.43 ; mEq/L → 1.215 |
| Serum_Calcium | mg/dL | 5.0 – 15.0 | mmol/L → 4.0 |
| Ionized_Calcium | mg/dL | 3.0 – 7.0 | mmol/L → 4.0 |
| Phosphorus | mg/dL | 1.0 – 15.0 | mmol/L → 3.1 |
| Intact_PTH | pg/mL | 5 – 2500 | pmol/L → 9.43 |
| Vitamin_D_25OH | ng/mL | 4 – 120 | nmol/L → 0.4008 |
| Vitamin_D_1_25OH | pg/mL | 5 – 150 | pmol/L → 0.4167 |
| Alkaline_Phosphatase | U/L | 20 – 2000 | — |
| Hemoglobin | g/dL | 4.0 – 20.0 | g/L → 0.1 |
| Hematocrit | % | 12 – 60 | proportion → 100 |
| RBC_Count | 10^6/µL | 2.0 – 7.5 | — (= 10^12/L) |
| WBC_Count | 10^3/µL | 1.0 – 50.0 | — (= 10^9/L) |
| Platelet_Count | 10^3/µL | 10 – 1000 | — (= 10^9/L) |
| Serum_Iron | µg/dL | 15 – 350 | µmol/L → 5.587 |
| TIBC | µg/dL | 150 – 650 | µmol/L → 5.587 |
| Transferrin_Saturation | % | 3 – 95 | — |
| Ferritin | ng/mL | 3 – 3000 | — (= µg/L) |
| Reticulocyte_Count | % | 0.2 – 15.0 | — |
| Total_Bilirubin | mg/dL | 0.1 – 25.0 | µmol/L → 0.05848 |
| Direct_Bilirubin | mg/dL | 0.0 – 15.0 | µmol/L → 0.05848 |
| Albumin_Serum | g/dL | 1.5 – 6.0 | g/L → 0.1 |
| Total_Protein | g/dL | 3.0 – 10.0 | g/L → 0.1 |
| Prealbumin | mg/dL | 5 – 45 | mg/L → 0.1 |
| CRP | mg/L | 0 – 350 | mg/dL → 10.0 |
| Total_Cholesterol | mg/dL | 80 – 400 | mmol/L → 38.67 |
| LDL_Cholesterol | mg/dL | 20 – 300 | mmol/L → 38.67 |
| HDL_Cholesterol | mg/dL | 10 – 130 | mmol/L → 38.67 |
| Triglycerides | mg/dL | 20 – 1200 | mmol/L → 88.57 |
| Non_HDL_Cholesterol | mg/dL | 30 – 380 | mmol/L → 38.67 |
| Glucose | mg/dL | 40 – 700 | mmol/L → 18.0 |
| HbA1c | % | 3.5 – 18.0 | mmol/mol → (×0.0915 + 2.15) |
| Fructosamine | µmol/L | 100 – 700 | — |
| Uric_Acid | mg/dL | 1.0 – 20.0 | µmol/L → 0.01681 |
| Urine_Albumin | mg/L | 0 – 5000 | — |
| Urine_Creatinine | mg/dL | 10 – 400 | mmol/L → 11.31 |
| Albumin_to_Creatinine_Ratio_Urine | mg/g | 0 – 6000 | mg/mmol → 8.84 |
| Protein_to_Creatinine_Ratio_Urine | mg/g | 0 – 20000 | mg/mmol → 8.84 |
| Urine_Protein | mg/dL | 0 – 1000 | — |
| Urine_pH | — | 4.5 – 8.5 | — |
| Urine_Specific_Gravity | — | 1.001 – 1.040 | — |
| BNP | pg/mL | 0 – 5000 | — (= ng/L) |
| NT_proBNP | pg/mL | 0 – 35000 | — (= ng/L) |
| Troponin_I | ng/mL | 0 – 50 | ng/L → 0.001 |
| Troponin_T | ng/mL | 0 – 10 | ng/L → 0.001 |
| Free_T4 | ng/dL | 0.2 – 6.0 | pmol/L → 0.07770 |
| Free_T3 | pg/mL | 1.0 – 6.0 | pmol/L → 0.6510 |
| pH_Arterial | — | 6.8 – 7.8 | — |
| pCO2_Arterial | mmHg | 10 – 100 | kPa → 7.5 |
| pO2_Arterial | mmHg | 30 – 150 | kPa → 7.5 |
| Lactate | mmol/L | 0.3 – 20.0 | mg/dL → 0.1110 |
| Beta2_Microglobulin | mg/L | 0.5 – 60 | — |
| Aluminum | µg/L | 1 – 250 | µmol/L → 26.98 |

## Notes on the HbA1c conversion

HbA1c has an affine (not multiplicative) SI relationship. IFCC `mmol/mol` converts to NGSP `%`
with `pct = 0.0915 * mmol_mol + 2.15`. Apply this form rather than a single factor when an
HbA1c value reads far above the `%` range (e.g. a raw value in the 20–140 band).

## Ranges that most often need a below-floor conversion

These commonly arrive in SI units that read *below* the US floor; treat an under-floor value as
a conversion candidate first, not as a discard:

- Magnesium (mmol/L ≈ 0.4–0.9 → ×2.43 lands in mg/dL)
- Serum_Calcium / Ionized_Calcium (mmol/L → ×4.0)
- Phosphorus (mmol/L ≈ 0.8–1.6 → ×3.1)
- Hemoglobin / Albumin / Total_Protein (g/L → ×0.1 for above-ceiling values)
