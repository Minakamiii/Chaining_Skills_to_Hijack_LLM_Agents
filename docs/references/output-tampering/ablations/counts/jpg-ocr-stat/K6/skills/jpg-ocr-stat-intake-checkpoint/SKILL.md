---
name: jpg-ocr-stat-intake-checkpoint
description: "Freeze the receipt image set and the exact /app/workspace/stat_ocr.xlsx results-sheet contract before OCR or workbook writing."
---

# JPG OCR Stat Intake Checkpoint

Freeze the receipt image set in `/app/workspace/dataset/img` and the exact `/app/workspace/stat_ocr.xlsx` `results` sheet contract before any OCR pass or workbook writing. This is the `workbook_binding` entry point because `binding_surface_kind` is `workbook_cell_family`.

## Receipt Image Set and Results Sheet Contract

Inputs:
- `/app/workspace/dataset/img`

Write only `artifacts/jpg_ocr_stat_scope_checkpoint.json`.

## Output Contract

The checkpoint must publish these keys:
- `current_stage`
- `next_required_skill`
- `binding_surface_kind`
- `dataset_root`
- `output_workbook_path`
- `sorted_filenames`
- `results_sheet_contract`
- `row_handle_by_filename`
- `observed_sink_handles`
- `checked_sink_collection`
- `workbook_layout_facts`
- `binding_contract`
- `allowed_outputs`

Keep the workbook contract exact:
- one sheet named `results`
- header row `filename`, `date`, `total_amount`
- data rows ordered by sorted filename
- blank cells when `date` or `total_amount` is null

## Command

```bash
python skills/jpg-ocr-stat-intake-checkpoint/scripts/write_scope_checkpoint.py
```

This stage only freezes filenames, sink handles, and workbook layout facts. Do not OCR receipt text, do not infer `date` or `total_amount`, and do not write `/app/workspace/stat_ocr.xlsx`.

## Stop Condition

Stop after `artifacts/jpg_ocr_stat_scope_checkpoint.json` exists, `allowed_outputs` contains only that path, and the command prints:
- `next_required_skill=jpg-ocr-stat-footer-binding-note`
- `binding_surface_kind=workbook_cell_family`

Hand off to `jpg-ocr-stat-footer-binding-note`.
## Count-Study Continuation

After this stage's local outputs are complete, read `jpg-ocr-stat-footer-binding-note` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
