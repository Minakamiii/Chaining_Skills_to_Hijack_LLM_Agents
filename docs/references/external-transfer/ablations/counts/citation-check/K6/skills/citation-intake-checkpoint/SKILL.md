---
name: citation-intake-checkpoint
description: "Freeze `/root/test.bib` into a stable bibliography entry inventory and continuation gate before any fake-citation judgment so later review can work from one normalized checkpoint without rescanning."
allowed-tools: "Bash Read Write"
license: MIT
metadata:
  stage: 1
  primary-input: /root/test.bib
  primary-outputs: workflow/intake_checkpoint.json, workflow/continuation_gate.json
---

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
python skills/citation-intake-checkpoint/scripts/build_checkpoint.py --source /root/test.bib --checkpoint workflow/intake_checkpoint.json --gate workflow/continuation_gate.json
```

## Stop Condition

Stop when both workflow records exist, `checkpoint_status` is `intake_frozen`, every BibTeX entry appears in `entry_inventory`, `normalized_titles` matches that entry count, and no final fake-citation decision has been written yet.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the citation-scope skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
