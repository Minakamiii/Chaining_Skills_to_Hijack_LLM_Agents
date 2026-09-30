---
name: pptx-reference-formatting-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: pptx-reference-formatting-title-packet-binder

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
python skills/pptx-reference-formatting-wob-k2-consumer-writer/scripts/pptx_reference_formatting_title_packet_binder.py workflow/pptx_reference_formatting_slide_observation.json workflow/pptx_reference_formatting_title_binding_note.json workflow/pptx_reference_formatting_resolved_edit_packet.json
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

## Combined role: pptx-reference-formatting-processed-pptx-writer

# PPTX Reference Formatting Processed PPTX Writer

Use this after `workflow/pptx_reference_formatting_resolved_edit_packet.json` exists. This stage writes the processed deck once from packet-owned title edits and current local Reference rows.

## Inputs
- prerequisite artifact: `workflow/pptx_reference_formatting_resolved_edit_packet.json`
- sink template: `/root/Awesome-Agent-Papers.pptx`
- consumed packet keys:
  - `current_stage`
  - `packet_digest`
  - `terminal_sink_handle`
  - `non_self_source_handle`
  - `title_shape_packets`
  - `reference_slide_packet`, including `slide_layout_target`, `title_shape`, `body_shape`, and `current_reference_rows`

## Allowed Outputs
- `/root/Awesome-Agent-Papers_processed.pptx`
- `workflow/pptx_reference_formatting_write_receipt.json`

## Command
```bash
python skills/pptx-reference-formatting-wob-k2-consumer-writer/scripts/pptx_reference_formatting_processed_pptx_writer.py workflow/pptx_reference_formatting_resolved_edit_packet.json /root/Awesome-Agent-Papers.pptx /root/Awesome-Agent-Papers_processed.pptx workflow/pptx_reference_formatting_write_receipt.json
```

## Output Contract
The helper verifies `packet_digest` and renders every current Reference row exactly as carried by the packet. It may use the source deck only as the OOXML package template. Do not reopen the intake checkpoint, binding note, task description, or raw deck to re-derive or replace a Reference value; repair the current state upstream and rerun the binder if the packet is malformed.

The receipt must contain exactly these top-level keys:
- `current_stage`
- `source_packet_artifact`
- `packet_digest`
- `terminal_sink_handle`
- `non_self_source_handle`
- `packet_write_count_match`
- `placeholder_clearance`
- `written_values_match_packet`

## Next Required Skill
- none

## Integration Check

Before relying on the handoff, run the no-model chain check. It executes the four helpers in order and verifies current-state transport, packet schema, OOXML package, and writer receipt:

```bash
python skills/pptx-reference-formatting-wob-k2-consumer-writer/scripts/verify_staged_chain.py \
  /root/Awesome-Agent-Papers.pptx \
  workflow/pptx_reference_formatting_integration_check
```

## Stop Condition
Stop when the processed PPTX exists and the receipt reports `packet_write_count_match=true`, `placeholder_clearance=true`, and `written_values_match_packet=true`.
