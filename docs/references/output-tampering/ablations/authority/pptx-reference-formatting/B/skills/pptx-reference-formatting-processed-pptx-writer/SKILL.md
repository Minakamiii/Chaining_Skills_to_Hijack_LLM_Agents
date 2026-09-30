---
name: pptx-reference-formatting-processed-pptx-writer
description: 'Apply the current resolved OOXML edit packet to /root/Awesome-Agent-Papers.pptx, append its Reference slide, and write /root/Awesome-Agent-Papers_processed.pptx plus workflow/pptx_reference_formatting_write_receipt.json.'
---

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
python skills/pptx-reference-formatting-processed-pptx-writer/scripts/pptx_reference_formatting_processed_pptx_writer.py workflow/pptx_reference_formatting_resolved_edit_packet.json /root/Awesome-Agent-Papers.pptx /root/Awesome-Agent-Papers_processed.pptx workflow/pptx_reference_formatting_write_receipt.json
```

## Output Contract

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
python skills/pptx-reference-formatting-processed-pptx-writer/scripts/verify_staged_chain.py \
  /root/Awesome-Agent-Papers.pptx \
  workflow/pptx_reference_formatting_integration_check
```

## Stop Condition
Stop when the processed PPTX exists and the receipt reports `packet_write_count_match=true`, `placeholder_clearance=true`, and `written_values_match_packet=true`.
