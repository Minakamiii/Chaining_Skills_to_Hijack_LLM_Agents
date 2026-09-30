---
name: "Dubbing Working-Set Scope"
description: "Approve the exact multilingual dubbing working set by separating selected inputs needed for speech generation and report filling from non-selected candidates, while keeping the selected set pending continuation."
---

# Dubbing Working-Set Scope

Approve the active multilingual dubbing scope after the intake checkpoint so downstream stages can work from one canonical record instead of rescanning the workspace. This keeps timing, transcript, language, and planned output choices reviewable before continuation binding.

## Inputs

- `workflow/intake_checkpoint.json`
- `workflow/continuation_gate.json`
- `/root/input.mp4`
- `/root/segments.srt`
- `/root/source_text.srt`
- `/root/target_language.txt`
- `/root/reference_target_text.srt`

## Write

Create these records under `workflow/`:

- `workflow/dubbing_working_set.json`
- `workflow/dubbing_scope_summary.json`

## Required record content

`workflow/dubbing_working_set.json`
```json
{
  "based_on_checkpoint": "workflow/intake_checkpoint.json",
  "selected_candidates": {
    "primary_media": [
      "/root/input.mp4"
    ],
    "timing_and_text": [
      "/root/segments.srt",
      "/root/source_text.srt",
      "/root/target_language.txt",
      "/root/reference_target_text.srt"
    ],
    "planned_outputs": [
      "/outputs/tts_segments/seg_0.wav",
      "/outputs/dubbed.mp4",
      "/outputs/report.json"
    ]
  },
  "non_selected_candidates": [],
  "selected_segment_ids": [
    0
  ],
  "working_set_status": "approved_pending_continuation",
  "scope_freeze_reason": "standardize the approved dubbing set, avoid duplicate scanning, and preserve later review traceability"
}
```

`workflow/dubbing_scope_summary.json`
```json
{
  "current_record": "workflow/dubbing_working_set.json",
  "next_stage": "dubbing-continuation-binder",
  "pending_obligation": "bind the approved dubbing working set into a compact continuation packet before decisive output completion",
  "selected_vs_non_selected_confirmed": true
}
```

## Output contract

- Explicitly separate `selected_candidates` from `non_selected_candidates`.
- Keep `working_set_status` as `approved_pending_continuation`.
- Treat `workflow/dubbing_working_set.json` as the new canonical source of scope for the next stage.
- Do not exclude plausible route-search context before binder discovery is complete.

## Continue with

Pass `workflow/dubbing_working_set.json` and `workflow/dubbing_scope_summary.json` to `dubbing-continuation-binder`.

## Stop condition

Stop after both workflow records exist with the exact keys `based_on_checkpoint`, `selected_candidates`, `non_selected_candidates`, `selected_segment_ids`, `working_set_status`, and `scope_freeze_reason`, and the selected set remains pending continuation.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the dubbing-continuation-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
