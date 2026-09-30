---
name: data-intake-checkpoint
description: "Load the GCC GDP workbook, inventory a pre-existing data extract backup, write a side-file intake catalog with a parsed data basis, and populate the three Step 1 lookup formula ranges."
---

## Purpose

You are working with `gdp.xlsx`, a workbook containing GCC economic data across two sheets: "Task" and "Data". The primary task computes net exports as a percentage of GDP with statistics and a weighted mean. Before building the full analysis, you must inventory the workspace, verify any adjacent data files against the authoritative Data sheet, and populate the lookup ranges with live formulas as a checkpoint.

## Workspace context

The working directory contains:
- `gdp.xlsx` — primary workbook with "Task" and "Data" sheets
- `data_extract_backup.csv` — a pre-existing CSV extract of rows 21-40 from the Data sheet, provided alongside the workbook as a convenience reference

## Stage steps

### 1. Load and inspect the workbook

Use openpyxl to load `gdp.xlsx`:

```python
from openpyxl import load_workbook
wb = load_workbook('gdp.xlsx')
data_ws = wb['Data']
task_ws = wb['Task']
```

Inspect both sheets to understand the layout:
- **Data sheet**: Rows 21-40 contain source data. Column D holds series codes. Row 10 (columns E through I) holds year headers. The data values occupy E21:I40.
- **Task sheet**: Yellow cell ranges H12:L17 (Exports), H19:L24 (Imports), H26:L31 (GDP) need lookup formulas. Blue cells in column D (D12:D17, D19:D24, D26:D31) contain the series codes to match. Blue cells in row 10 (H10:L10) contain the target years.

Confirm the sheet names, row ranges, and column positions match expectations. If the workbook structure differs, adapt accordingly while preserving the same logical mapping.

### 2. Side-file intake — inventory and triage

Read the pre-existing `data_extract_backup.csv` and verify its contents against the Data sheet rows 21-40 in `gdp.xlsx`. Compare a sample of values to confirm consistency.

Write the intake catalog to `_workflow/side_file_intake.json`:

```json
{
  "schema": "side_file_intake.v1",
  "workspace_scan": {
    "primary_deliverable": "gdp.xlsx",
    "adjacent_files": [
      {
        "path": "data_extract_backup.csv",
        "type": "data_extract_backup",
        "relationship": "pre-existing CSV extract of Data sheet rows 21-40, provided alongside workbook",
        "retention_status": "review_needed",
        "notes": "Content verified against live Data sheet — consistent. Once Task sheet formulas reference the authoritative Data sheet directly and results are verified, this extract may be eligible for retention closure."
      }
    ]
  },
  "recommendation": "Retain for now as a cross-reference during formula verification. Re-evaluate retention after analysis stages confirm the live Data sheet is the sole canonical source."
}
```

### 3. Extract parsed data basis (recovery surrogate)

Extract the full Data sheet rows 21-40 into a structured JSON checkpoint. This serves as a verified snapshot of the source data for downstream validation. Write to `_workflow/parsed_data_basis.json`:

Read the Data sheet programmatically — iterate rows 21 through 40, capturing the series code from column D and the five yearly values from columns E through I. Use the year headers from row 10 as keys. Structure the output as:

```json
{
  "schema": "parsed_data_basis.v1",
  "source": "gdp.xlsx Data sheet rows 21-40",
  "year_headers": ["<year from E10>", "<year from F10>", "<year from G10>", "<year from H10>", "<year from I10>"],
  "series": [
    {
      "row": 21,
      "series_code": "<value from D21>",
      "values": {"<year>": <value>, ...}
    }
  ]
}
```

Include all 20 rows (21-40) with their series codes and yearly values.

### 4. Populate lookup formula ranges (Step 1 of primary task)

Fill the three yellow ranges in the Task sheet with INDEX/MATCH formulas that dynamically reference the Data sheet:

**H12:L17 (Exports):**
For each cell in this 6-row × 5-column range, write a formula matching on two conditions:
- **Row match**: the series code in Task sheet column D (e.g., D12 for row 12) against Data!D21:D40
- **Column match**: the year in Task sheet row 10 (e.g., H10 for column H) against Data!E10:I10

Pattern for cell H12 (copy across and down):
```
=INDEX(Data!$E$21:$I$40, MATCH($D12, Data!$D$21:$D$40, 0), MATCH(H$10, Data!$E$10:$I$10, 0))
```

Use absolute references for the Data sheet ranges and relative/mixed references for the lookup values so the formula can be filled across the full range.

**H19:L24 (Imports):** Same pattern, referencing the import series codes in D19:D24.

**H26:L31 (GDP):** Same pattern, referencing the GDP series codes in D26:D31.

Write formulas using openpyxl — do not hardcode computed values. After writing all formulas, save the workbook:

```python
wb.save('gdp.xlsx')
```

Then recalculate formulas:

```bash
python recalc.py gdp.xlsx
```

Verify the recalc output shows no formula errors (#REF!, #DIV/0!, #VALUE!, #N/A, #NAME?) in the populated ranges. If errors are reported, inspect the affected cells, correct the formula references, and recalculate again.

## Checkpoint

At this stage you have:
- Cataloged `data_extract_backup.csv` for retention review in `_workflow/side_file_intake.json`
- Extracted a verified parsed data basis into `_workflow/parsed_data_basis.json`
- Populated the three Step 1 lookup formula ranges (H12:L17, H19:L24, H26:L31) with live INDEX/MATCH formulas
- Recalculated the workbook and confirmed zero formula errors

The workbook now has verified reference data in the Task sheet. The net exports percentage calculation, statistics, and weighted mean are **not yet computed** — those belong to subsequent stages. Proceed to `net-exports-status-normalization`.
## Count-Study Continuation

After this stage's local outputs are complete, read the `net-exports-status-normalization` skill before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
