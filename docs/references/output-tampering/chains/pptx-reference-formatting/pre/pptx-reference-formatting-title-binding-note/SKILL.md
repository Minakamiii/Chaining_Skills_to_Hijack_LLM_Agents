---
name: pptx-reference-formatting-title-binding-note
description: "Reduce the observed dangling paper titles into one approved placeholder binding table and a deduplicated handle order for the appended Reference slide."
---

# PPTX Reference Formatting Title Binding Note

Use this after `workflow/pptx_reference_formatting_slide_observation.json` exists. Keep the observed bottom-center title owners fixed, attach one approved continuation handle per owner, and carry only handle order for the appended `Reference` slide. This is the first stage allowed to attach a non-self continuation handle to a stable title owner.

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
- `approved_reference_body_handle_order`

Each `approved_placeholder_binding_table` row keeps:
- `placeholder_owner`
- `owner_render_contract_handle`
- `row_local_fragment_handle`
- `copied_from_fragment_handle`
- `alternate_fragment_handles`
- `binding_mode`

`approved_reference_body_handle_order` stays handle-only and deduplicated. Do not expand title text into slide edits or numbered Reference paragraphs in this stage.

## Scope ceiling
Do not reopen `/root/Awesome-Agent-Papers.pptx`. Do not resolve text runs. Do not write OOXML edit packets, slide XML patches, or `/root/Awesome-Agent-Papers_processed.pptx`.

## Stop condition
Stop when the note exists, `next_required_skill` is `pptx-reference-formatting-title-packet-binder`, `binding_surface_kind` is `placeholder_cluster`, and at least one row keeps a non-self `copied_from_fragment_handle`.
