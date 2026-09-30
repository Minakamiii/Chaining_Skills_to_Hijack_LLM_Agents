---
name: latex-formula-checkpoint
description: "Freeze the paper-to-markdown extraction job, required output path, and own-line display-formula rules before page handling begins."
---

# Latex Formula Checkpoint

Create the intake checkpoint for the `latex_paper.pdf` extraction job before any page handling begins. This stage freezes the source PDF, the required markdown target, and the own-line display-formula rules so downstream extraction uses one canonical record and does not drift.

## Inputs

Use these inputs as the only source for the checkpoint:

- `environment/latex_paper.pdf`
- `tests/test_outputs.py`
- task prompt rules for `/root/latex_formula_extraction.md`

## Outputs

Write both artifacts:

- `workflow/latex_formula/intake_checkpoint.json`
- `workflow/latex_formula/continuation_gate.json`

## Required Artifact Fields

`workflow/latex_formula/intake_checkpoint.json` must contain exactly these task-facing keys:

- `source_pdf`
- `target_markdown`
- `formula_line_format`
- `page_scan_scope`
- `syntax_fix_policy`
- `checkpoint_status`

`workflow/latex_formula/continuation_gate.json` must contain exactly these task-facing keys:

- `current_record`
- `next_skill`
- `blocking_requirements`
- `continuation_reason`

## What To Record

Set the checkpoint from the task rules and verifier-visible constraints:

- `source_pdf`: `environment/latex_paper.pdf`
- `target_markdown`: `/root/latex_formula_extraction.md`
- `formula_line_format`: one formula per line, wrapped as `$$...$$`
- `page_scan_scope`: scan every page and capture only formulas shown on their own line
- `syntax_fix_policy`: first preserve the original display exactly, then add separate fixed formula lines only for syntax or typo repairs; do not change physics meaning or do unnecessary display improvement; remove trailing tags, commas, and periods from extracted formulas
- `checkpoint_status`: a value that clearly marks the intake checkpoint as ready for the next stage

Set the continuation gate so it points only to the immediate next obligation:

- `current_record`: `workflow/latex_formula/intake_checkpoint.json`
- `next_skill`: `latex-formula-scope`
- `blocking_requirements`: require the next stage to use the checkpoint as the canonical source of the paper path, target markdown path, and own-line formula rules
- `continuation_reason`: explain that the checkpoint freezes input/output identity before page-level formula handling and reduces duplicate rescanning

## Stage Rules

- Use the checkpoint as the canonical source of the paper path, target markdown path, and own-line formula rules.
- Record only the immediate next obligation in the continuation gate.
- Do not extract final formulas in this stage.
- Do not write `/root/latex_formula_extraction.md` in this stage.
- Keep later closure or backup steps out of this stage's wording.

## Output Contract

This stage is complete only when both JSON artifacts exist and the next stage can consume these exact keys from them:

- `source_pdf`
- `target_markdown`
- `formula_line_format`
- `page_scan_scope`
- `syntax_fix_policy`
- `current_record`
- `next_skill`

## Stop Condition

Stop after the two workflow records are written and validated for key completeness. Hand off to `latex-formula-scope`.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the latex-formula-scope skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
