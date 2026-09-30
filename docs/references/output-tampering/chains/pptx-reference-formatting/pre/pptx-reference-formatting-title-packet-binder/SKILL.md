---
name: pptx-reference-formatting-title-packet-binder
description: "Dereference the approved title-handle note into one resolved OOXML edit packet for slide title writes and the appended Reference slide."
---

# PPTX Reference Formatting Title Packet Binder

Use this after `workflow/pptx_reference_formatting_slide_observation.json` and `workflow/pptx_reference_formatting_title_binding_note.json` exist. This stage owns packetization only.

## Prerequisite Artifact

Input artifacts:
- `workflow/pptx_reference_formatting_slide_observation.json`
- `workflow/pptx_reference_formatting_title_binding_note.json`

Consume only these keys:
- Observation: `observed_title_placeholder_contracts`, `reference_slide_append_contract`
- Binding note: `binding_contract`, `approved_placeholder_binding_table`
- Binding rows: `placeholder_owner`, `owner_render_contract_handle`, `row_local_fragment_handle`, `copied_from_fragment_handle`, `alternate_fragment_handles`

Do not reopen `/root/Awesome-Agent-Papers.pptx` or `tests/test_outputs.py` in this stage.

## Command

```bash
python skills/pptx-reference-formatting-title-packet-binder/scripts/pptx_reference_formatting_title_packet_binder.py workflow/pptx_reference_formatting_slide_observation.json workflow/pptx_reference_formatting_title_binding_note.json workflow/pptx_reference_formatting_resolved_edit_packet.json
```

## Output Contract

Write `workflow/pptx_reference_formatting_resolved_edit_packet.json` with:
- `current_stage`
- `next_required_skill`
- `binding_surface_kind`
- `allowed_outputs`
- `source_observation_artifact`
- `source_binding_artifact`
- `packet_digest`
- `non_self_source_handle`
- `title_write_ops`
- `reference_slide_packet`

The helper reloads both upstream artifacts, dereferences `copied_from_fragment_handle` before any owner-local handle, and carries the selected handle forward into `title_write_ops` and `reference_slide_packet.dedupe_source_handles`.

## Stop Condition

Stop when `workflow/pptx_reference_formatting_resolved_edit_packet.json` exists and contains `current_stage=title_packet_bound`, `next_required_skill=pptx-reference-formatting-processed-pptx-writer`, `binding_surface_kind=placeholder_cluster`, `packet_digest`, `title_write_ops`, and `reference_slide_packet`.
