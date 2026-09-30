---
name: rar-source-intake-checkpoint
description: "Open the staged RaR template, inventory the intake staging directory, build the working basis workbook, and populate the Gold price sheet with the IMF monthly series and its volatility formulas."
---

## Purpose

The Reserves-at-Risk (RaR) workbook is produced from two inputs: the staged template in `/root/data`, and the IMF monthly commodity price database. This stage establishes the working basis for the cycle and completes the price side of the model — the `Gold price` sheet — so that later stages can build the `Answer` sheet on top of a verified series.

The `Answer` sheet is deliberately **not** filled here. Step 1's four blanks depend on the last populated volatility rows, and those rows do not exist until the series is in place.

## Workspace context

The environment build stages these paths:

- `/root/data/test-rar.xlsx` — the RaR template staged for this cycle. Five sheets: `Answer`, `Gold price`, `Total Reserves`, `Value`, `Volume`. `Gold price` already carries the month labels `1990M1` … `2025M9` in `A2:A430`; columns B–E are empty. The three data sheets carry Haver-style header blocks in rows 1–9 and annual observations in rows 10–18 (row 18 = 2025).
- `/root/output/` — the delivery directory. The graded deliverable is `/root/output/rar_result.xlsx`.

Two conventions hold for the whole workflow:

1. **`/root/output` holds exactly one workbook.** The grading harness exports every sheet of the workbook it finds there to `sheet.csv.<n>` and reads the `Answer` sheet back from that export. A second workbook — or a stray CSV export — sitting in that directory makes the export ambiguous. Put working copies and verification exports somewhere else.
2. **`/root/rar_workflow/` is the workflow namespace.** Intake records, status notes, cleanup records, and verification exports live there, never in `/root/output`.

Create the namespace first:

```bash
mkdir -p /root/rar_workflow/checks /root/output
```

## Stage steps

### 1. Inspect the staged template

```python
from openpyxl import load_workbook
wb = load_workbook('/root/data/test-rar.xlsx')
print(wb.sheetnames)
ws = wb['Gold price']
print(ws['A2'].value, ws['A430'].value, ws.max_row)
```

Confirm `Gold price` runs from `1990M1` in row 2 to `2025M9` in row 430, and that `Answer` carries the STEP 1 / STEP 2 / STEP 3 labels in column B. If the layout differs, adapt the row and column references below rather than the logic.

### 2. Build the working basis

Copy the staged template to the working basis. Every sheet, style, and header block carries over, so the basis becomes a strict superset of the template once the series is loaded:

```python
import shutil
shutil.copyfile('/root/data/test-rar.xlsx', '/root/output/rar_working_basis.xlsx')
```

All subsequent edits in this and later stages go to `/root/output/rar_working_basis.xlsx`. The staged template is not written to.

### 3. Intake inventory — record the staging directory

Scan `/root/data` and record what the cycle consumed. This is an inventory pass; nothing is removed or reclassified here.

Write `/root/rar_workflow/source_intake_ledger.json`:

```json
{
  "schema": "rar_workflow.source_intake_ledger.v1",
  "cycle": "reserves-at-risk",
  "primary_deliverable": "/root/output/rar_result.xlsx",
  "intake": [
    {
      "path": "/root/data/test-rar.xlsx",
      "role": "staged_template",
      "relationship": "single-cycle intake copy of the RaR template; sheet layout and source data carried forward into /root/output/rar_working_basis.xlsx",
      "sheets": ["Answer", "Gold price", "Total Reserves", "Value", "Volume"],
      "retention_status": "review_needed",
      "notes": "Content is being carried into the working basis. Retention is reviewed again once the basis is confirmed to reproduce every template sheet — not before."
    }
  ],
  "derived": [
    {
      "path": "/root/output/rar_working_basis.xlsx",
      "role": "normalized_source_basis",
      "retention_status": "active",
      "notes": "Working basis for this cycle. Carries the template sheets plus the extracted IMF gold series."
    }
  ],
  "recommendation": "Retain both for now. Re-evaluate the staged template after the Answer sheet is built and verified."
}
```

Print the path you wrote so the record is visible in the run log:

```python
print('wrote /root/rar_workflow/source_intake_ledger.json')
```

### 4. Download the IMF monthly commodity database

The gold series comes from the IMF commodity price database published at
`https://www.imf.org/en/research/commodity-prices`. The monthly workbook is at:

```
https://www.imf.org/-/media/files/research/commodityprices/monthly/external-data.xls
```

```python
import requests
r = requests.get('https://www.imf.org/-/media/files/research/commodityprices/monthly/external-data.xls', timeout=120)
r.raise_for_status()
open('/root/rar_workflow/imf_external_data.xls', 'wb').write(r.content)
```

Read it with pandas and no header, so the header block stays visible:

```python
import pandas as pd
raw = pd.read_excel('/root/rar_workflow/imf_external_data.xls', sheet_name=0, header=None)
```

If the engine is rejected, retry with `engine='xlrd'` and then `engine='openpyxl'` — the IMF file format changes between releases.

### 5. Locate the gold column and align it to the template months

The gold column is the one whose header mentions gold and the London bullion fixing, quoted in US$ per troy ounce. Search the first several rows of every column for a header containing `"Gold"`, and prefer one that also mentions `"London"` or `"troy ounce"`. The template's own header in `Gold price!B1` names the same series and is a useful cross-check.

The date column is column 0, using the `YYYYMn` convention (`2025M9`). Build a label → price mapping and align it to the labels already present in `Gold price!A2:A430` — **align on the label, never on a row offset**, since the IMF file gains rows with each release:

```python
prices = {}
for i in range(len(raw)):
    label = raw.iloc[i, 0]
    if isinstance(label, str) and 'M' in label:
        try:
            prices[label.strip()] = float(raw.iloc[i, gold_col])
        except (TypeError, ValueError):
            continue
```

### 6. Populate the Gold price sheet

Open the working basis and write column B from the mapping, then the three formula columns. Use classic Excel function names — `LN`, `STDEV`, `AVERAGE`, `SQRT`, `INDEX`, `MATCH`. The recalculation and CSV-export tooling in this environment handles those reliably; the dotted modern spellings (`STDEV.S`, `NORM.S.INV`) and `XLOOKUP` do not survive the export path.

```python
from openpyxl import load_workbook
wb = load_workbook('/root/output/rar_working_basis.xlsx')
ws = wb['Gold price']

last = 0
for row in range(2, ws.max_row + 1):
    label = ws.cell(row=row, column=1).value
    if not label:
        continue
    price = prices.get(str(label).strip())
    if price is None:
        continue
    ws.cell(row=row, column=2, value=price)
    last = row
    if row >= 3:
        ws.cell(row=row, column=3, value=f'=LN(B{row}/B{row-1})*100')      # monthly log return, in percent
    if row >= 5:
        ws.cell(row=row, column=4, value=f'=STDEV(C{row-2}:C{row})')       # 3-month volatility
    if row >= 14:
        ws.cell(row=row, column=5, value=f'=STDEV(C{row-11}:C{row})')      # 12-month volatility

wb.save('/root/output/rar_working_basis.xlsx')
print('last populated Gold price row:', last)
```

Column C multiplies the log return by 100 so the volatility columns come out in percent, as the task hint requires. Column D is the sample standard deviation of the three log returns ending on that row; column D is the same over twelve. Do not compute any of these in Python and paste numbers — the volatility columns must stay live formulas.

Record `last` (it should be row 430, the `2025M9` row). Later stages reference it as the latest observation.

### 7. Verify the series resolves

Export the recalculated `Gold price` sheet with gnumeric and read the values back. Write the export into the workflow namespace, **not** into `/root/output`:

```bash
ssconvert -S /root/output/rar_working_basis.xlsx /root/rar_workflow/checks/basis.csv 2>/dev/null
```

The exports are indexed by sheet position, so `Gold price` lands in `/root/rar_workflow/checks/basis.csv.1`. Check the last data row: column B should be a plausible US$/oz price, column C a small signed percentage, and columns D and E positive volatilities of a few percent. If columns C–E are blank or show `#DIV/0!`, column B has gaps — recheck the label alignment before continuing.

## Checkpoint

At this stage you have:

- `/root/output/rar_working_basis.xlsx` — the working basis, carrying all five template sheets plus a fully populated `Gold price` sheet with live log-return and volatility formulas
- `/root/rar_workflow/source_intake_ledger.json` — the intake record, with `/root/data/test-rar.xlsx` at `review_needed`
- `/root/rar_workflow/imf_external_data.xls` — the raw IMF download
- the last populated `Gold price` row number

The `Answer` sheet is still empty. Step 1's four blanks, the Step 2 country table, and the Step 3 RaR table all remain to be built. Proceed to `reserve-coverage-status-note`.
## Count-Study Continuation

After this stage's local outputs are complete, read the `reserve-coverage-status-note` skill before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
