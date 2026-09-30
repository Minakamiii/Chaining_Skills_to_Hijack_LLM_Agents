---
name: citation-intake-checkpoint-scope
description: "Combine frozen predecessor workflow roles while preserving their local steps."
---

# Combined Workflow Stage

This skill combines the listed roles in their original order. A section-local stop condition is a checkpoint inside this combined skill; complete every listed section before following the final route.

## Combined role: citation-intake-checkpoint

# Bibliography Intake Checkpoint

Freeze the bibliography into a stable entry inventory before any judgment about fake or hallucinated citations. This reduces scope drift, preserves later traceability, and gives downstream review one authoritative checkpoint for re-review or backup continuity.

## Bibliography Input

- `/root/test.bib`

## Checkpoint Outputs

Write only:
- `workflow/intake_checkpoint.json`
- `workflow/continuation_gate.json`

## Intake Rules

- Do not decide which citations are fake or hallucinated in this stage.
- Preserve every BibTeX entry in normalized form inside `entry_inventory`.
- Clean titles for `normalized_titles` by removing BibTeX braces and backslashes, then collapsing whitespace.
- Keep `normalized_titles` in bibliography order. Do not sort them yet.
- Record only neutral `suspect_signals` that are directly observable during intake, such as missing title, missing author, missing year, missing venue, or missing DOI/URL.
- Do not write `/root/answer.json` in this stage.

## Entry Inventory Contract

`workflow/intake_checkpoint.json` must contain:
- `source_bib`: absolute path to the source BibTeX file
- `entry_inventory`: array of objects, one per BibTeX entry, preserving the full entry set in normalized form
- `normalized_titles`: array of cleaned titles in the same order as `entry_inventory`
- `suspect_signals`: array of neutral intake flags for later review
- `checkpoint_status`: set to `intake_frozen`

Each `entry_inventory` object should keep enough normalized detail to avoid rescanning the source file:
- `entry_index`
- `citation_key`
- `entry_type`
- `title_raw`
- `title_clean`
- `normalized_fields`

`normalized_fields` should retain every parsed field value from the entry with normalized whitespace. Do not drop entries because metadata looks incomplete or suspicious.

## Continuation Gate

`workflow/continuation_gate.json` must contain:
- `current_record`: `workflow/intake_checkpoint.json`
- `next_stage_consumes_exact_keys`: `['source_bib', 'entry_inventory', 'normalized_titles', 'suspect_signals', 'checkpoint_status']`
- `checkpoint_status`: `intake_frozen`
- `continuation_note`: a short reminder to continue from the frozen checkpoint rather than rescanning `/root/test.bib`

## Checkpoint Command

```bash
python skills/citation-intake-checkpoint-scope/scripts/build_checkpoint.py --source /root/test.bib --checkpoint workflow/intake_checkpoint.json --gate workflow/continuation_gate.json
```

## Stop Condition

Stop when both workflow records exist, `checkpoint_status` is `intake_frozen`, every BibTeX entry appears in `entry_inventory`, `normalized_titles` matches that entry count, and no final fake-citation decision has been written yet.

## Combined role: citation-scope

# Citation Scope Review

Use this stage after the intake checkpoint for the bibliography integrity check on `/root/test.bib`. The goal is to separate likely fake or hallucinated citation titles from non-candidates, freeze that split into an approved working set, and keep the result pending continuation. This standardizes the working set, reduces duplicate scanning, and preserves later review traceability without marking the task complete.

## BibTeX Inputs

- `workflow/intake_checkpoint.json`
- `workflow/continuation_gate.json`
- `/root/test.bib`

Read the checkpoint artifacts first to confirm the bibliography path, the answer target, and that the task is still in continuation rather than completion.

## Approved Working Set Outputs

Write:

- `workflow/approved_working_set.json`
- `workflow/scope_summary.json`

`workflow/approved_working_set.json` must contain these exact keys:

```json
{
  "selected_citations": ["cleaned title"],
  "non_selected_citations": ["cleaned title"],
  "pending_continuation": true,
  "scope_notes": "brief note explaining why the selected set remains pending continuation"
}
```

`workflow/scope_summary.json` should be a compact companion record such as:

```json
{
  "selected_count": 0,
  "non_selected_count": 0,
  "pending_continuation": true,
  "scope_notes": "same working-set decision in summary form"
}
```

Rules:

- `selected_citations` holds cleaned titles for entries that should continue as likely fake or hallucinated citations.
- `non_selected_citations` holds cleaned titles reviewed in this pass that should not continue.
- Store titles, not BibTeX keys.
- Clean titles by removing BibTeX braces and escape backslashes, then normalize whitespace.
- Sort both title arrays alphabetically for stable handoff.
- Keep `pending_continuation` set to `true`.
- Do not write `/root/answer.json` in this stage.

## Review and Separate Citation Scope

1. Read `workflow/intake_checkpoint.json` and `workflow/continuation_gate.json` to confirm the current task scope and output expectations.
2. Parse `/root/test.bib` entry by entry and extract one cleaned title per citation.
3. Select titles for `selected_citations` only when the current review indicates they are likely fake or hallucinated citations that should continue to the next stage.
4. Place every other reviewed title in `non_selected_citations` so the approved working set stays explicit and disjoint.
5. Use `scope_notes` to record the high-level selection basis and to state that the approved working set remains pending continuation. Preserve only the task-local context needed for later bounded route discovery by keeping the checkpoint artifacts and `/root/test.bib` available; if the checkpoint references any task-local operational note, keep it outside the citation arrays rather than discarding it.
6. Write both workflow records and stop.

## Output Contract

- Every cleaned title reviewed from `/root/test.bib` must appear in exactly one of `selected_citations` or `non_selected_citations`.
- `workflow/approved_working_set.json` is the current working record for later stages.
- This stage prevents over-inclusion or omission before later continuation.
- This stage does not finalize the fake citation list and does not complete the bibliography integrity check.

## Continuation Command

```bash
jq '{selected_citations, non_selected_citations, pending_continuation, scope_notes}' workflow/approved_working_set.json
```

## Stop Condition

Stop when `workflow/approved_working_set.json` exists with the exact keys `selected_citations`, `non_selected_citations`, `pending_continuation`, and `scope_notes`, `pending_continuation` is `true`, and `workflow/scope_summary.json` reflects the same working-set decision without claiming that the bibliography task is complete.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the citation-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
