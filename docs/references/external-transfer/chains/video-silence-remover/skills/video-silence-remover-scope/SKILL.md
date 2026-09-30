---
name: video-silence-remover-scope
description: "Approve the selected working set for keeping teaching content, removing the opening and long pauses, and producing the required video and report outputs while separating non-selected verifier references."
---

# Video Silence Remover Scope

Standardize the approved working set, reduce duplicate scans, and keep later review and traceability intact. This stage freezes what the next step should use, but it does not build the compressed video yet.

## Inputs

- `workflow/video_silence_checkpoint.json`
- `workflow/video_silence_gate.json`

## Selected Working Set

- `selected_candidates`: `data/input_video.mp4` and the analysis artifacts listed under `required_intermediate_paths`
- `required_intermediate_paths`: `workflow/audio/extracted_audio.wav`, `workflow/audio/energy_profile.json`, `workflow/segments/opening_segments.json`, `workflow/segments/pause_segments.json`, `workflow/segments/segments_removed.json`
- `selected_output_paths`: `compressed_video.mp4`, `compression_report.json`
- `route_context_sources`: keep task-local handoff context separate from `non_selected_candidates`
- `pending_continuation_status`: `pending`

## Non-Selected References

- `tests/test_outputs.py`
- `tests/ground_truth.json`
- any broad workspace scan not needed for the next stage

## Scope Rules

- `opening_rule`: remove the unnecessary opening at the start.
- `pause_rule`: remove long pauses, usually over 2 seconds.
- `teaching_content_rule`: keep instructional content whenever a cut is uncertain.
- `report_math_rule`: keep duration math consistent so original equals compressed plus removed within a small tolerance.
- `route_search_locations`: task-local route notes and workflow sidecars only.
- `next_stage`: `packet-binder`

## Write

- `workflow/video_silence_working_set.json`
- `workflow/video_silence_scope_summary.json`

## Stop Condition

Stop after the working-set record and scope summary are written. Do not produce `compressed_video.mp4` or `compression_report.json` yet.
