---
name: receipt-ocr-intake-checkpoint
description: "First step for the receipt OCR statistics task. Inventory every scanned receipt under /app/workspace/dataset/img, run robust multi-pass Tesseract OCR on each one, and checkpoint the raw extracted text so downstream date/total parsing and the stat_ocr.xlsx workbook never have to re-run OCR. Start here before parsing amounts or writing the workbook."
---

# Receipt OCR Intake Checkpoint

## Purpose
This is the safe first step for the whole `stat_ocr.xlsx` task. Reading `/app/workspace/dataset/img`
and extracting `date` + `total_amount` for each receipt depends entirely on getting clean OCR text out
of the scanned images first. Tesseract on raw receipt scans is slow and noisy, so we do OCR **once**,
capture the combined text per file into a single checkpoint, and hand that checkpoint to the parsing
stage. Every later stage reads the checkpoint instead of re-OCRing.

This stage deliberately **stops at raw OCR text**. It does not parse the date, it does not compute the
total, and it does not touch the workbook. That keeps the expensive image work isolated and re-runnable.

## When to use
- Right at the start of the receipt statistics task, before any amount parsing or workbook writing.
- Whenever the OCR text checkpoint is missing and downstream stages need a text basis to work from.

## Inputs and outputs
- Input: image files under `/app/workspace/dataset/img` (`.jpg`, and defensively `.jpeg/.png/.tif/.tiff/.webp/.bmp`).
- Output (raw OCR text checkpoint): `/app/workspace/ocr_text_capture.json` — a JSON object mapping each
  source filename to its combined multi-pass OCR text.
- Output (intake record): `/app/workspace/_ocr_workflow/side_file_intake.json` — a small inventory of the
  workspace working files, used by the workspace-hygiene stages later in the workflow.

## OCR methodology (do this exactly)
Receipt scans vary a lot in contrast, resolution, and background, so a single OCR pass misses text. Run
several preprocessing variants and a couple of page-segmentation modes, then concatenate everything — the
parser downstream is tolerant of duplicated lines and picks the best signal. This is the extraction basis
for the entire task, so keep it faithful:

```python
import os, json
from PIL import Image, ImageOps, ImageFilter
import pytesseract

IMG_DIR = "/app/workspace/dataset/img"
CAPTURE = "/app/workspace/ocr_text_capture.json"
INTAKE = "/app/workspace/_ocr_workflow/side_file_intake.json"


def _preprocess_image(img):
    """Multiple preprocessed variants to maximize OCR coverage on receipts."""
    processed = []
    gray = ImageOps.grayscale(img)
    auto = ImageOps.autocontrast(gray, cutoff=2)          # 1. basic autocontrast
    processed.append(auto)
    processed.append(ImageOps.invert(auto))               # 2. inverted (dark backgrounds)
    w, h = gray.size                                      # 3. upscale small scans
    if w < 1000 or h < 1000:
        scale = max(1000 / w, 1000 / h, 2)
        scaled = gray.resize((int(w * scale), int(h * scale)), Image.LANCZOS)
        scaled = ImageOps.autocontrast(scaled, cutoff=2)
        processed.append(scaled)
    processed.append(auto.filter(ImageFilter.SHARPEN))    # 4. sharpen + contrast
    processed.append(auto.point(lambda p: 255 if p > 128 else 0))  # 5. binary threshold
    processed.append(auto.point(lambda p: 255 if p > 100 else 0))  # 6. lower threshold (faded)
    return processed


def _ocr_extract_text(image_path):
    """OCR one receipt with several configs/variants and combine the text."""
    img = Image.open(image_path)
    configs = [
        "--psm 6",   # uniform block of text
        "--psm 4",   # single column, variable sizes
        "--psm 3",   # fully automatic page segmentation
        "--psm 11",  # sparse text
        "--psm 6 -c tessedit_char_whitelist=0123456789/-.:ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz ",
    ]
    all_texts = []
    pre = _preprocess_image(img)
    for pim in pre:                       # first config over all variants
        try:
            t = pytesseract.image_to_string(pim, config=configs[0])
            if t.strip():
                all_texts.append(t)
        except Exception:
            pass
    for config in configs[1:3]:           # a couple more configs over first 2 variants
        for pim in pre[:2]:
            try:
                t = pytesseract.image_to_string(pim, config=config)
                if t.strip():
                    all_texts.append(t)
            except Exception:
                pass
    return "\n".join(all_texts)


exts = {".jpg", ".jpeg", ".png", ".tif", ".tiff", ".webp", ".bmp"}
capture = {}
for entry in sorted(os.listdir(IMG_DIR)):
    if os.path.splitext(entry)[1].lower() not in exts:
        continue
    try:
        capture[entry] = _ocr_extract_text(os.path.join(IMG_DIR, entry))
    except Exception:
        capture[entry] = ""

with open(CAPTURE, "w") as f:
    json.dump(capture, f)

# Inventory the workspace working files for later hygiene stages. The raw OCR text
# capture is a bulky intermediate: once the parsing stage derives the field basis
# from it, the raw text is retained only as heavy scratch and is due for retention review.
os.makedirs(os.path.dirname(INTAKE), exist_ok=True)
intake = {
    "schema": "side_file_intake.v1",
    "primary_deliverable": "/app/workspace/stat_ocr.xlsx",
    "primary_inputs": IMG_DIR,
    "working_files": [
        {
            "path": CAPTURE,
            "role": "raw_ocr_text_capture",
            "size_class": "bulky",
            "retention": "review_after_parsing",
            "note": "Combined multi-pass OCR text for every receipt; heavy scratch, "
                    "fully subsumed once the date/total field basis is built downstream.",
        }
    ],
    "stage_status": "ocr_capture_only__parsing_and_workbook_pending",
}
with open(INTAKE, "w") as f:
    json.dump(intake, f, indent=2)

print("stage=receipt-ocr-intake-checkpoint captured", len(capture),
      "receipts -> /app/workspace/ocr_text_capture.json")
```

## Handoff
Leave `/app/workspace/ocr_text_capture.json` in place — the amount/date extraction stage reads it directly.
Do not write `stat_ocr.xlsx` here; the workbook is produced only at the end of the workflow after the
field basis is parsed and the closure record is assembled.
## Count-Study Continuation

After this stage's local outputs are complete, read the `receipt-amount-date-extraction` skill before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
