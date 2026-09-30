---
name: video-silence-remover-binder
description: "Package the approved video-silence working set into a local continuation packet before final video rendering and compression report closure. Use when the input video, removal-segment artifacts, and selected output paths are already approved and the final local render step should continue from a compact packet instead of rescanning the workspace."
---

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
python3 skills/video-silence-remover-binder/scripts/bind_video_silence_packet.py \
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
