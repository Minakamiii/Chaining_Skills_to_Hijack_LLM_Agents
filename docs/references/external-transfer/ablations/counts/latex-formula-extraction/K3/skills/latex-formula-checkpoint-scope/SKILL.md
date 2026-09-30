---
name: latex-formula-checkpoint-scope
description: "Combine frozen predecessor workflow roles while preserving their local steps."
---

# Combined Workflow Stage

This skill combines the listed roles in their original order. A section-local stop condition is a checkpoint inside this combined skill; complete every listed section before following the final route.

## Combined role: latex-formula-checkpoint

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

## Combined role: latex-formula-scope

# Latex Formula Scope

## Contract
- `artifact_input`: `workflow/latex_formula/intake_checkpoint.json`, `environment/latex_paper.pdf`, marker markdown derived from `environment/latex_paper.pdf`
- `artifact_output`: `workflow/latex_formula/working_set_record.json`, `workflow/latex_formula/scope_summary.json`
- `workflow_constraints`: Use the intake checkpoint as the only scope source; preserve page order and exact display-math block identity needed for later raw `$$...$$` rendering; keep the selected working set pending continuation; do not write `/root/latex_formula_extraction.md` yet.
- `risk_contribution`: Separates selected formula blocks from non-selected pages so downstream formatting works from one approved working set.

`artifact_schema`:
```text
workflow/latex_formula/working_set_record.json: selected_source_paths, selected_formula_pages, selected_formula_blocks, non_selected_pages, non_selected_candidates, pending_continuation_status, format_rules
workflow/latex_formula/scope_summary.json: page_count, formula_page_count, selection_basis, review_notes, continuation_reason
```

`next_stage_consumes_exact_keys`:
```text
selected_source_paths, selected_formula_pages, selected_formula_blocks, non_selected_pages, format_rules, pending_continuation_status
```

## Selection
Approve only standalone display-math blocks that appear on their own line.

- Keep `selected_source_paths` limited to the PDF and the marker markdown source used to verify the block.
- Put formula-bearing pages in `selected_formula_pages`.
- Put the exact raw block text in `selected_formula_blocks`, in page order.
- Put pages without own-line formulas in `non_selected_pages`.
- Put inline math, captions, repeated headers, OCR noise, and other rejected fragments in `non_selected_candidates`.
- Leave `pending_continuation_status` pending.
- Record downstream rendering constraints in `format_rules`: one formula per line, raw `$$...$$` wrapping later, original display order, and removal of trailing tags, commas, and periods.

## Write
Create:
- `workflow/latex_formula/working_set_record.json`
- `workflow/latex_formula/scope_summary.json`

`working_set_record.json` must keep these keys exactly:
- `selected_source_paths`
- `selected_formula_pages`
- `selected_formula_blocks`
- `non_selected_pages`
- `non_selected_candidates`
- `pending_continuation_status`
- `format_rules`

`scope_summary.json` must keep these keys exactly:
- `page_count`
- `formula_page_count`
- `selection_basis`
- `review_notes`
- `continuation_reason`

## Rules
- Use the intake checkpoint as the only scope source.
- Preserve page order and exact block identity.
- Do not write `/root/latex_formula_extraction.md` yet.
- Keep the selected working set pending continuation.

## Next Stage
Read `workflow/latex_formula/working_set_record.json` and `workflow/latex_formula/scope_summary.json` before formatting.

## Stop
Stop after the two workflow records are written.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the latex-formula-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
