---
name: latex-formula-scope
description: "Approve the formula-bearing pages and raw own-line display blocks that should continue toward the final markdown."
---

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
