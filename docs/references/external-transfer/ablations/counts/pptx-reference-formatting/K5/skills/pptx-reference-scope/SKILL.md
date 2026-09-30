---
name: pptx-reference-scope
description: "Approve the exact dangling-title and Reference-slide working set for /root/Awesome-Agent-Papers.pptx, including selected title slides, deduplicated paper-title collection, and unchanged content boundaries."
---

# Approve Dangling Paper Titles and Reference-Slide Working Set

## Purpose
Freeze the exact working set for the dangling paper title cleanup in `/root/Awesome-Agent-Papers.pptx` before any PPTX write happens. This stage identifies the selected title slides, builds the deduplicated paper-title collection for the later `Reference` slide, and preserves the unchanged non-title-content boundary for slides 1-6.
Do not create `/root/Awesome-Agent-Papers_processed.pptx` in this stage.

## Inputs
- `workflow/pptx_reference/intake_checkpoint.json`
- `workflow/pptx_reference/continuation_gate.json`
- `/root/Awesome-Agent-Papers.pptx`

## Outputs
- `workflow/pptx_reference/working_set_record.json`
- `workflow/pptx_reference/scope_summary.json`

## Approve the Exact Working Set
1. Read `workflow/pptx_reference/intake_checkpoint.json` and `workflow/pptx_reference/continuation_gate.json`.
Use the checkpoint identifier from `workflow/pptx_reference/intake_checkpoint.json` as `approved_from_checkpoint_id`.
If either file is missing, the checkpoint identity is unclear, or the continuation gate no longer points to dangling-title cleanup plus `Reference` slide append work, stop.
2. Inspect `/root/Awesome-Agent-Papers.pptx` only far enough to confirm the selected dangling paper title slides and collect the paper-title text.
Use raw OOXML or markdown extraction if needed. Ignore notes, comments, theme text, and duplicate occurrences outside the selected title set.
3. Confirm that the selected title slides are slides `2`, `3`, `4`, `5`, and `6`.
Each selected slide should contribute one dangling paper title paragraph that will later be restyled to Arial `16`, color `#989596`, bold disabled, widened to one line, and placed at the bottom center.
If the deck does not support that exact five-slide working set, stop instead of inventing a replacement scope.
4. Build `reference_title_collection` from the selected slide titles in first-seen order and remove duplicate paper titles before recording the collection.
5. Create `workflow/pptx_reference/` if it does not already exist, then freeze the selected versus non-selected boundary exactly once and write the artifacts.
Selected candidates:
`title_slide_numbers`: `[2, 3, 4, 5, 6]`
`title_edit_targets`: `["one dangling paper title paragraph per selected slide", "bottom-center title text box width expansion", "Reference slide append slot at deck end"]`
`reference_title_collection`: the deduplicated paper titles from the selected slides
`supporting_ooxml_targets`: `["ppt/slides/slide2.xml through ppt/slides/slide6.xml", "presentation slide list for terminal append"]`
Non-selected candidates:
`["existing non-title text and media on slides 1-6", "theme assets not required for title restyling", "duplicate paper-title occurrences after deduplication"]`
6. Set `pending_continuation_status` to `approved-working-set-pending-binder`.
7. Write `workflow/pptx_reference/scope_summary.json` so the next stage can continue without broad rescanning.

## Output Contract
`workflow/pptx_reference/working_set_record.json` must contain:
```json
{
  "working_set_id": "<new working set id>",
  "approved_from_checkpoint_id": "<checkpoint id from intake_checkpoint.json>",
  "selected_candidates": {
    "title_slide_numbers": [2, 3, 4, 5, 6],
    "title_edit_targets": [
      "one dangling paper title paragraph per selected slide",
      "bottom-center title text box width expansion",
      "Reference slide append slot at deck end"
    ],
    "reference_title_collection": [
      "<deduplicated paper title 1>",
      "<deduplicated paper title 2>"
    ],
    "supporting_ooxml_targets": [
      "ppt/slides/slide2.xml through ppt/slides/slide6.xml",
      "presentation slide list for terminal append"
    ]
  },
  "non_selected_candidates": [
    "existing non-title text and media on slides 1-6",
    "theme assets not required for title restyling",
    "duplicate paper-title occurrences after deduplication"
  ],
  "pending_continuation_status": "approved-working-set-pending-binder"
}
```

`workflow/pptx_reference/scope_summary.json` must contain:
```json
{
  "selected_slide_numbers": [2, 3, 4, 5, 6],
  "duplicate_title_policy": "remove duplicate paper titles before Reference slide body is written",
  "non_title_content_guard": "keep slides 1-6 non-title content unchanged",
  "minimal_verification_focus": [
    "one title per selected slide",
    "single-line fit",
    "bottom-center placement",
    "deduplicated auto-numbered Reference slide body"
  ]
}
```

## Continuation Command
Use `workflow/pptx_reference/working_set_record.json` and `workflow/pptx_reference/scope_summary.json` as the only scope inputs for the next binder stage. Continue from `selected_candidates`, `non_selected_candidates`, `pending_continuation_status`, `selected_slide_numbers`, `duplicate_title_policy`, and `minimal_verification_focus` without rescanning unrelated slides or theme assets.

## Stop Condition
Stop and hand off when both JSON artifacts exist, the selected set is limited to slides 2-6, the paper-title collection is deduplicated, the non-title-content guard is recorded, and no processed PPTX has been written yet.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the pptx-reference-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
