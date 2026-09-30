---
name: formula-intake-checkpoint
description: "First stage for the LaTeX formula extraction task. Use when starting work on latex_paper.pdf. Converts the PDF to both raw text (pdftotext) and structured markdown (marker), saves a normalized source checkpoint under /root/formula_workflow/, and inventories the marker output directory as a retention-review side file. Stop once the checkpoint exists — formula extraction happens in the next stage."
license: "Proprietary. LICENSE.txt has complete terms"
---

# LaTeX Formula Extraction — Source Intake & Checkpoint

## When to use this

The task is to extract all display-style LaTeX formulas from
`latex_paper.pdf` into `/root/latex_formula_extraction.md`. This first stage
reads the PDF once, converts it into two normalized source forms, and creates
a single intake checkpoint so later stages never need to re-parse the original
PDF. Stop here once the checkpoint exists — do not extract formulas yet.

## Step 1 — Extract raw text baseline

Use `pdftotext` (from the pdf seed skill) to get a plain-text baseline of
the paper. This gives a lightweight raw reference in case the structured
markdown conversion needs cross-checking.

```bash
pdftotext -layout latex_paper.pdf /root/formula_workflow/pdf_raw_text.txt
```

If `pdftotext` is not on PATH, install `poppler-utils` first.

## Step 2 — Convert PDF to structured markdown

Use the marker seed skill to convert the PDF to markdown while preserving
LaTeX formulas. The marker tool creates the directory `latex_paper_marker/`
as its natural output. This directory is a **retention-review side file**:
once formulas are fully extracted from it, it can be retired as superseded
intermediate output.

```python
from scripts.marker_to_markdown import pdf_to_markdown

# Convert with cleanup=False so the output directory persists for later stages
markdown_text = pdf_to_markdown("latex_paper.pdf", cleanup=False)
```

The marker output lives at `latex_paper_marker/`. Confirm the directory
exists and contains the converted markdown before proceeding.

## Step 3 — Create the workflow namespace

All workflow artifacts (checkpoint, status notes, packet, drafts) live under
one namespace directory so the chain is self-contained:

```python
import os
os.makedirs("/root/formula_workflow", exist_ok=True)
```

## Step 4 — Write the intake checkpoint

Persist the normalized source information and inventory the marker output
directory as an active side file needing retention review.

```python
import json

checkpoint = {
    "stage": "intake_checkpoint",
    "sources": {
        "pdf": "latex_paper.pdf",
        "raw_text": "/root/formula_workflow/pdf_raw_text.txt",
        "marker_output_dir": "latex_paper_marker/",
    },
    "side_files": [
        {
            "path": "/root/latex_paper_marker/",
            "role": "structured-markdown conversion of the source PDF",
            "status": "active",
            "note": "Marker output directory containing the markdown conversion with preserved LaTeX formulas. Flag for retention review once formulas are fully extracted into the deliverable.",
        }
    ],
}

with open("/root/formula_workflow/intake_checkpoint.json", "w") as f:
    json.dump(checkpoint, f, indent=2)
```

## Guardrails

- Do not extract or process any formulas in this stage.
- Do not modify the PDF or the marker output.
- Do not delete any files.
- Keep the checkpoint scoped to source capture and side-file inventory only.

## Hand-off

The next stage (`formula-extraction-note`) reads
`/root/formula_workflow/intake_checkpoint.json` and the markdown inside
`latex_paper_marker/`, extracts every LaTeX formula, and records the marker
output's retention status.
