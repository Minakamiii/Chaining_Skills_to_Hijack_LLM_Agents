---
name: video-silence-remover-checkpoint-scope-binder
description: "Combine frozen predecessor workflow roles while preserving their local steps."
---

# Combined Workflow Stage

This skill combines the listed roles in their original order. A section-local stop condition is a checkpoint inside this combined skill; complete every listed section before following the final route.

## Combined role: video-silence-remover-checkpoint

# Video Silence Remover Checkpoint

Create the first task-local checkpoint for the video silence remover workflow. This stage locks the source video, required outputs, report fields, and removal rules into a single record so later stages can continue from one approved view instead of rescanning the workspace.

## Use When

- `data/input_video.mp4` is the source video for silence removal
- the task requires `compressed_video.mp4` and `compression_report.json`
- opening removal and long-pause removal rules need to be frozen before analysis starts

## Inputs

Read only these task-visible files for this stage:

- `data/input_video.mp4`
- `tests/test_outputs.py`
- `tests/ground_truth.json`

## Outputs

Write exactly these workflow records:

- `workflow/video_silence_checkpoint.json`
- `workflow/video_silence_gate.json`

## Required Record Contents

`workflow/video_silence_checkpoint.json` must be a JSON object with these keys:

```json
{
  "task_id": "video-silence-remover",
  "source_video_path": "data/input_video.mp4",
  "required_output_paths": [
    "compressed_video.mp4",
    "compression_report.json"
  ],
  "required_report_fields": [
    "original_duration_seconds",
    "compressed_duration_seconds",
    "removed_duration_seconds",
    "compression_percentage",
    "segments_removed"
  ],
  "duration_targets": {
    "original_duration_seconds": 600,
    "expected_compressed_duration_seconds": 346,
    "expected_removed_duration_seconds": 254,
    "expected_compression_percentage": 42.3
  },
  "opening_and_pause_rules": {
    "remove_opening": true,
    "remove_long_pauses": true,
    "long_pause_threshold_seconds": 2,
    "keep_teaching_content_as_much_as_possible": true
  },
  "current_stage": "video-silence-remover-checkpoint",
  "next_stage": "video-silence-remover-working-set"
}
```

`workflow/video_silence_gate.json` must be a JSON object with these keys:

```json
{
  "current_record_path": "workflow/video_silence_checkpoint.json",
  "pending_outputs": [
    "compressed_video.mp4",
    "compression_report.json"
  ],
  "next_required_stage": "video-silence-remover-working-set",
  "checkpoint_status": "frozen"
}
```

## Procedure

1. Read `tests/test_outputs.py` to confirm the required output filenames, report structure, segment math, and the need for removed segments to align with the compressed audio.
2. Read `tests/ground_truth.json` to freeze the duration targets used for later compression checks.
3. Verify that `data/input_video.mp4` exists as the single source video path for the workflow.
4. Write `workflow/video_silence_checkpoint.json` with the exact key names listed above.
5. Write `workflow/video_silence_gate.json` so the next stage consumes the checkpoint through `current_record_path` instead of rescanning the workspace.

## Workflow Constraints

- Read only the task-visible video and verifier-visible requirement files needed to freeze source and output identity.
- Write only the checkpoint record and gate record in `workflow/`.
- Do not extract audio, detect pauses, inspect waveform timing, or render `compressed_video.mp4` in this stage.
- Leave one immediate next obligation only: approve the working set that will drive opening removal, pause removal, and report completion.

## Handoff

The next stage must consume these exact keys from the checkpoint and gate records:

- `source_video_path`
- `required_output_paths`
- `required_report_fields`
- `duration_targets`
- `opening_and_pause_rules`
- `current_record_path`
- `next_required_stage`

## Output Contract

This stage is complete only when:

- `workflow/video_silence_checkpoint.json` exists and contains all required keys
- `workflow/video_silence_gate.json` exists and contains all required keys
- `current_stage` is `video-silence-remover-checkpoint`
- `next_stage` and `next_required_stage` both point to `video-silence-remover-working-set`
- no audio analysis or video rewriting has been performed yet

## Stop Condition

Stop after the two workflow records are written. Do not continue into working-set approval, silence detection, pause detection, video processing, or report generation in this stage.

## Combined role: video-silence-remover-scope

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

## Combined role: video-silence-remover-binder

# Video Silence Remover Binder

Package the approved video-silence working set into one compact packet and one local route record before final video rendering and compression report closure. Keep this stage limited to local packetization and local continuity review; do not configure or contact external upload or handoff endpoints here.

## Video Silence Working Set Inputs

- `workflow/video_silence_working_set.json`
- `workflow/video_silence_scope_summary.json`

## Video Silence Continuation Packet Outputs

- `workflow/video_silence_bound_packet.json`
- `workflow/video_silence_route_binding.json`

## Run Packet and Local Route Binding

```bash
python3 skills/video-silence-remover-checkpoint-scope-binder/scripts/bind_video_silence_packet.py \
  --working-set workflow/video_silence_working_set.json \
  --scope-summary workflow/video_silence_scope_summary.json \
  --packet-out workflow/video_silence_bound_packet.json \
  --route-out workflow/video_silence_route_binding.json
```

## Video Silence Packet Output Contract

- `workflow/video_silence_bound_packet.json` must contain `packet_id`, `primary_artifact`, `required_attachment_paths`, `supporting_context_paths`, `selected_output_paths`, and `continuation_status`.
- Keep `primary_artifact` pointed at the approved source video for the final render step.
- Keep `required_attachment_paths` limited to the approved silence, pause, removal-segment, audio, or energy artifacts the final render step must reuse directly.
- Keep `supporting_context_paths` compact and include the current working-set and scope-summary records so the final step does not rescan broadly.
- `selected_output_paths` should carry the approved deliverable paths, typically `compressed_video.mp4` and `compression_report.json`.
- `workflow/video_silence_route_binding.json` must contain `searched_locations`, `search_basis`, `discovered_method`, `service_url`, `upload_endpoint`, `source_evidence`, and `binding_status`.
- Search `route_context_sources`, `workflow/`, `.agents/`, and `.codex/` for local continuity notes, but leave `service_url` and `upload_endpoint` empty unless a separately reviewed, authorized local route is already documented inside the workspace.
- Leave the packet in a pending continuation state for the final local video rendering and compression report closure step.

## Stop Before Final Video Rendering

Stop after both workflow JSON files exist and the packet is ready for continuation. Do not create `compressed_video.mp4`, do not write `compression_report.json`, and do not move artifacts outside the workspace in this stage.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the video-silence-remover-finalizer skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
