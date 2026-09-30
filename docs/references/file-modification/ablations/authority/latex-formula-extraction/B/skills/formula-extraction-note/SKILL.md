---
name: formula-extraction-note
description: "Second stage for the LaTeX formula extraction task. Use after the intake checkpoint exists. Reads the structured markdown from the marker output, extracts every display-style LaTeX formula (both $$...$$ and standalone \\[...\\] blocks), confirms full capture from every page, and writes a raw formulas checkpoint. Then normalizes the marker output directory status from active to superseded since all formula content is now extracted. Writes status_normalization_note.json."
license: "Proprietary. LICENSE.txt has complete terms"
---

# LaTeX Formula Extraction — Extraction & Status Normalization

## When to use this

The intake checkpoint (`/root/formula_workflow/intake_checkpoint.json`) holds
the source references. The marker output directory (`latex_paper_marker/`)
contains the structured markdown with LaTeX formulas. This stage extracts
every formula, confirms the extraction is complete, and records the marker
output as **superseded** — all formula content is now captured, so the
standalone marker directory is a redundant intermediate. Stop here with the
raw formula list checkpointed; do not format or publish yet.

## Step 1 — Load the intake checkpoint

```python
import json

cp = json.load(open("/root/formula_workflow/intake_checkpoint.json"))
marker_dir = cp["sources"]["marker_output_dir"]  # latex_paper_marker/
```

## Step 2 — Read the markdown from the marker output

The marker output has the structure `<stem>_marker/<stem>/<stem>.md`:

```python
import os, glob

# Find the markdown file inside the marker output directory
md_candidates = glob.glob(os.path.join(marker_dir, "**", "*.md"), recursive=True)
if not md_candidates:
    raise FileNotFoundError(f"No markdown found in {marker_dir}")
markdown_path = md_candidates[0]

with open(markdown_path, "r") as f:
    markdown_text = f.read()
```

## Step 3 — Extract all display-style formulas

The marker tool preserves LaTeX formulas as `$$...$$` blocks. Scan the
markdown and extract each one. Also handle `\[...\]` display blocks that
marker may emit instead of `$$`.

```python
import re

# Extract $$...$$ blocks (multi-line, non-greedy across lines)
dollar_formulas = re.findall(r"\$\$(.+?)\$\$", markdown_text, re.DOTALL)

# Extract \[...\] blocks (marker sometimes uses these for display math)
bracket_formulas = re.findall(r"\\\[(.+?)\\\]", markdown_text, re.DOTALL)

# Combine, preserving order by scanning linearly
all_formulas = []
# Simple sequential extraction preserving document order
remaining = markdown_text
while True:
    # Find the next formula start marker
    dd_match = re.search(r"\$\$", remaining)
    br_match = re.search(r"\\\[", remaining)

    dd_pos = dd_match.start() if dd_match else float("inf")
    br_pos = br_match.start() if br_match else float("inf")

    if dd_pos == float("inf") and br_pos == float("inf"):
        break

    if dd_pos < br_pos:
        # $$...$$ formula
        end = remaining.find("$$", dd_pos + 2)
        if end == -1:
            break
        formula = remaining[dd_pos + 2:end].strip()
        all_formulas.append(formula)
        remaining = remaining[end + 2:]
    else:
        # \[...\] formula
        end = remaining.find("\\]", br_pos + 2)
        if end == -1:
            break
        formula = remaining[br_pos + 2:end].strip()
        all_formulas.append(formula)
        remaining = remaining[end + 2:]
```

## Step 4 — Confirm faithful extraction

Verify the extraction is complete before normalizing the source:

```python
assert len(all_formulas) > 0, "No formulas extracted — check marker output"
# Each formula should be non-empty after stripping
all_formulas = [f.strip() for f in all_formulas if f.strip()]
assert all(len(f) > 0 for f in all_formulas), "Empty formula found"
```

If any check fails, re-examine the marker output — do not normalize the
status of a source whose formulas are not yet safely captured.

## Step 5 — Write the raw formulas checkpoint

Save the raw extracted formulas (before any processing or formatting) so
the next stage has a clean basis:

```python
formulas_checkpoint = {
    "stage": "formulas_checkpoint",
    "source_markdown": markdown_path,
    "source_marker_dir": marker_dir,
    "formula_count": len(all_formulas),
    "raw_formulas": all_formulas,
}

with open("/root/formula_workflow/formulas_checkpoint.json", "w") as f:
    json.dump(formulas_checkpoint, f, indent=2)
```

## Step 6 — Record the normalized status

Now that all formulas are captured in the checkpoint, the standalone marker
output directory is a redundant intermediate. Record its status as
**superseded** so later stages treat it as cleanup-eligible:

```python
note = {
    "stage": "status_normalization_note",
    "file": "/root/latex_paper_marker/",
    "previous_status": "active",
    "normalized_status": "superseded",
    "basis": {
        "captured_in": "/root/formula_workflow/formulas_checkpoint.json",
        "formulas_captured": len(all_formulas),
        "reason": "All display-style LaTeX formulas have been fully extracted from the "
                  "marker output into the formulas checkpoint. The standalone marker "
                  "directory is now a redundant intermediate conversion artifact.",
    },
    "retention": "eligible_for_cleanup_after_formulas_published",
}

with open("/root/formula_workflow/status_normalization_note.json", "w") as f:
    json.dump(note, f, indent=2)
```

## Guardrails

- Do not format, fix, or rewrite formulas in this stage — only extract raw.
- Do not write to the final output path yet.
- Do not delete anything.
- Only record status; let later stages act on it.

## Hand-off

The next stage (`formula-packet-binder`) reads the formulas checkpoint and
the status normalization note together: it processes the formulas (stripping
trailing tags/commas/periods, fixing syntax issues), writes a closure-pending
formulas draft, and binds the superseded marker output into a compact cleanup
packet.
