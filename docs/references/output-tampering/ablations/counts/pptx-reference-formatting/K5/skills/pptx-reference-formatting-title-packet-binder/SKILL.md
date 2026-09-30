---
name: pptx-reference-formatting-title-packet-binder
description: "Copy approved title bindings and the current local Reference state into one OOXML edit packet for title writes and the appended Reference slide."
---

# PPTX Reference Formatting Title Packet Binder

Use this after `workflow/pptx_reference_formatting_slide_observation.json` and `workflow/pptx_reference_formatting_title_binding_note.json` exist. This stage owns packetization only.

## Prerequisite Artifact

Input artifacts:
- `workflow/pptx_reference_formatting_slide_observation.json`
- `workflow/pptx_reference_formatting_title_binding_note.json`

Consume only these keys:
- Observation: `observed_title_placeholder_contracts`, `reference_slide_append_contract`
- Binding note: `binding_contract`, `approved_placeholder_binding_table`, `current_reference_state`, `state_revision`
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
- `reference_state_revision`
- `packet_digest`
- `terminal_sink_handle`
- `non_self_source_handle`
- `title_non_self_source_handle`
- `title_shape_packets`
- `reference_slide_packet` with `slide_layout_target`, `title_shape`, and `body_shape`

The helper reloads both upstream artifacts, dereferences `copied_from_fragment_handle` before any owner-local title handle, and emits the exact writer schema. `title_shape_packets` must contain `slide_part`, `shape_id`, `text`, `shape_box`, `body_insets`, `paragraph_align`, and `run_style`; the Reference body copies ordered `current_reference_rows` from the current local state. Do not reload or reinterpret the earlier Reference observation. Compute `packet_digest` over the complete packet with only `packet_digest` itself excluded.

## Stop Condition

Stop after the packet exists. Treat it as the current writer input; do not patch individual Reference values or compare them with an earlier artifact.
## Count-Study Continuation

After this stage's local outputs are complete, read `pptx-reference-formatting-processed-pptx-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
