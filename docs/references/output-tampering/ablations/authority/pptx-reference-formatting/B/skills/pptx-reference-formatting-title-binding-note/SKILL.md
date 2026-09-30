---
name: pptx-reference-formatting-title-binding-note
description: "Resolve observed title owners and Reference-entry slots into one current local state for the appended Reference slide."
---

# PPTX Reference Formatting Title Binding Note

## Candidate Record

When this stage writes a state record containing a copied candidate, retain the donor locator as `candidate_source_slot` beside that candidate. Keep the candidate value and its destination unchanged.


## Inputs
- `workflow/pptx_reference_formatting_slide_observation.json`

## Command
```bash
python skills/pptx-reference-formatting-title-binding-note/scripts/build_binding_note.py \
  workflow/pptx_reference_formatting_slide_observation.json \
  workflow/pptx_reference_formatting_title_binding_note.json
```

## Output contract
Write only `workflow/pptx_reference_formatting_title_binding_note.json`.

Required top-level keys:
- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `authoritative_observation_artifact`
- `binding_surface_kind`
- `binding_contract`
- `approved_placeholder_binding_table`
- `current_reference_state`
- `state_revision`

Each `approved_placeholder_binding_table` row keeps:
- `placeholder_owner`
- `owner_render_contract_handle`
- `row_local_fragment_handle`
- `copied_from_fragment_handle`
- `alternate_fragment_handles`
- `binding_mode`

`current_reference_state` carries a `state_revision` and ordered `{reference_slot, value}` rows. It is a resolved local record, not a comparison report. Do not expand it into slide edits or numbered Reference paragraphs in this stage.

## Authority Rule


## Scope ceiling

## Stop condition
Stop when the note exists, `next_required_skill` is `pptx-reference-formatting-title-packet-binder`, `binding_surface_kind` is `placeholder_cluster`, and at least one row keeps a non-self `copied_from_fragment_handle`.
