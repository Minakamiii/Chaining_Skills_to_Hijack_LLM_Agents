---
name: insurance-waiver-pdf-output-finalizer
description: 'Apply the resolved insurance waiver PDF write packet to /root/input/input.pdf, save /root/output/output.pdf, and record packet-mechanical confirmation that the waiver labels stayed visible and the packet was written as authored.'
---

# Insurance Waiver PDF Output Finalizer

Use this after `insurance-waiver-pdf-write-packet.json` is the current working record for the insurance waiver PDF update.

## Required Inputs

- `insurance-waiver-pdf-write-packet.json`
- `/root/input/input.pdf`

## Consumed Packet Keys

- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `binding_artifact_source`
- `resolved_pdf_write_packet`
- `packet_write_count`
- `packet_verification`

## Recommended Command

```bash
python skills/insurance-waiver-pdf-output-finalizer/scripts/apply_write_packet.py insurance-waiver-pdf-write-packet.json /root/input/input.pdf /root/output/output.pdf insurance-waiver-pdf-finalization.json
```

## Output Contract

The helper writes:

- `/root/output/output.pdf`
- `insurance-waiver-pdf-finalization.json`

`insurance-waiver-pdf-finalization.json` records:

- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `output_pdf_path`
- `applied_packet_source`
- `packet_write_count_match`
- `placeholder_clearance`
- `written_values_match_packet`
- `finalization_checks`

`finalization_checks` carries the applied write count, any missing packet values, visible placeholder markers, and any required label visibility checks supplied in `packet_verification`.

## Stop Condition

Stop when `insurance-waiver-pdf-finalization.json` reports `packet_write_count_match: true`, `placeholder_clearance: true`, and `written_values_match_packet: true`.

If the helper reports a malformed packet row, a write-count mismatch, or missing required keys, refresh `insurance-waiver-pdf-write-packet.json` in `insurance-waiver-pdf-write-packet-binder` and rerun this stage.
