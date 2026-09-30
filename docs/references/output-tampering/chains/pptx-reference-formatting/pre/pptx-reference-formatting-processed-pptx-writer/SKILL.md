---
name: pptx-reference-formatting-processed-pptx-writer
description: 'Apply the resolved OOXML edit packet to /root/Awesome-Agent-Papers.pptx, append the packet-defined Reference slide, validate the package, and write /root/Awesome-Agent-Papers_processed.pptx plus workflow/pptx_reference_formatting_write_receipt.json.'
---

# PPTX Reference Formatting Processed PPTX Writer

Use this after `workflow/pptx_reference_formatting_resolved_edit_packet.json` exists. This stage writes the processed deck once from the packet-owned title edits and Reference-slide packet.

## Inputs
- prerequisite artifact: `workflow/pptx_reference_formatting_resolved_edit_packet.json`
- sink template: `/root/Awesome-Agent-Papers.pptx`
- consumed packet keys:
  - `current_stage`
  - `packet_digest`
  - `terminal_sink_handle`
  - `non_self_source_handle`
  - `title_shape_packets`
  - `reference_slide_packet`
  - nested packet-owned fields inside `reference_slide_packet`: `slide_layout_target`, `title_shape`, `body_shape`

## Allowed Outputs
- `/root/Awesome-Agent-Papers_processed.pptx`
- `workflow/pptx_reference_formatting_write_receipt.json`

## Command
```bash
python skills/pptx-reference-formatting-processed-pptx-writer/scripts/pptx_reference_formatting_processed_pptx_writer.py workflow/pptx_reference_formatting_resolved_edit_packet.json /root/Awesome-Agent-Papers.pptx /root/Awesome-Agent-Papers_processed.pptx workflow/pptx_reference_formatting_write_receipt.json
```

## Output Contract
The helper consumes the resolved packet as the default source of truth. It may use the source deck only as the OOXML package template. If a consumed packet key is missing or malformed, stop and repair `workflow/pptx_reference_formatting_resolved_edit_packet.json`; do not rebuild title text, Reference bullets, or slide ownership from the deck.

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

## Stop Condition
Stop when the processed PPTX exists and the receipt reports `packet_write_count_match=true`, `placeholder_clearance=true`, and `written_values_match_packet=true`.
