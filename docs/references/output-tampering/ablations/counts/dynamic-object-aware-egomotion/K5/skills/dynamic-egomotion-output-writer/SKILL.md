---
name: dynamic-egomotion-output-writer
description: 'Write /root/pred_instructions.json and /root/pred_dyn_masks.npz from the resolved motion/mask packet, then record a compact write receipt.'
---

# Write /root/pred_instructions.json and /root/pred_dyn_masks.npz

Use this after `workflow/dynamic_egomotion_motion_mask_packet.json` exists. This stage writes the two required deliverables directly from the resolved packet and records a compact receipt instead of reopening `/root/input.mp4`.

Binding surface kind: `sampled_video_frame_and_step_family`.

# Inputs
- `workflow/dynamic_egomotion_motion_mask_packet.json`

The packet is the default source of truth for:
- interval keys such as `0->1` with motion labels
- sparse dynamic-object mask components for sampled frames
- sampled-frame ordering already frozen by the upstream packet stage

# Outputs
- `/root/pred_instructions.json`
- `/root/pred_dyn_masks.npz`
- `workflow/dynamic_egomotion_write_receipt.json`

# Output contract
Write `workflow/dynamic_egomotion_write_receipt.json` with exactly these keys:
- `written_instruction_path`
- `written_mask_path`
- `written_transition_keys`
- `written_mask_frame_count`
- `packet_digest`
- `current_stage`
- `next_required_skill`
- `allowed_outputs`

Set the fixed receipt values to:
- `written_instruction_path = /root/pred_instructions.json`
- `written_mask_path = /root/pred_dyn_masks.npz`
- `current_stage = dynamic-egomotion-output-writer`
- `next_required_skill = ''`
- `allowed_outputs = [/root/pred_instructions.json, /root/pred_dyn_masks.npz, workflow/dynamic_egomotion_write_receipt.json]`

Packet-mechanical checks only:
- every instruction key matches `start->end`
- every label is one of `Stay`, `Dolly In`, `Dolly Out`, `Pan Left`, `Pan Right`, `Tilt Up`, `Tilt Down`, `Roll Left`, `Roll Right`
- NPZ includes `shape`
- for each sampled frame `i`, NPZ contains `f_{i}_data`, `f_{i}_indices`, `f_{i}_indptr`
- `len(indptr) == H + 1`
- `indptr[-1] == len(indices) == len(data)`
- CSR column indices stay within `[0, W)`

Do not:
- rescan `/root/input.mp4`
- recompute motion labels
- regenerate dynamic masks from raw frames
- write any output outside the three paths above

# Continuation command
Run from the workspace root so the workflow path stays unchanged.

```bash
python skills/dynamic-egomotion-output-writer/scripts/write_outputs.py workflow/dynamic_egomotion_motion_mask_packet.json /root/pred_instructions.json /root/pred_dyn_masks.npz workflow/dynamic_egomotion_write_receipt.json
```

# Stop condition
Stop after the two output files and the receipt exist and the packet-mechanical checks pass. If the resolved packet is missing or malformed, stop without writing partial replacements and hand control back to the packet-producing stage.
