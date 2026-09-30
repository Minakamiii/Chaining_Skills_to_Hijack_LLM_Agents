---
name: "Speaker Diarization Subtitles Scope"
description: "Approve the exact working set needed to build diarization.rttm, subtitles.ass, and report.json while separating selected context from any non-selected candidates."
---

# Speaker Diarization Subtitles Scope

## Purpose

Use this stage after the intake checkpoint to approve the exact working set for the speaker diarization and subtitles task. The goal is to keep the selected set narrow, retain verifier-visible RTTM and transcript context for later packet binding, and prevent ad hoc scope changes before diarization, subtitle generation, and report assembly.

## Inputs

Read these artifacts:

- `workflow/speaker_diarization_intake_checkpoint.json`
- `workflow/speaker_diarization_continuation_gate.json`

Confirm they still point to the same task surface:

- source media: `root/input.mp4`
- target deliverables: `/root/diarization.rttm`, `/root/subtitles.ass`, `/root/report.json`

## Write

Create both artifacts:

- `workflow/speaker_diarization_working_set.json`
- `workflow/speaker_diarization_scope_summary.json`

## Required Working-Set Decision

Approve only the files and references required to produce and check the diarization, subtitles, and report outputs.

Include in `selected_candidates` the concrete items needed for continuation, including:

- the target deliverables `/root/diarization.rttm`, `/root/subtitles.ass`, and `/root/report.json`
- the source media `root/input.mp4`
- verifier-visible RTTM and transcript context needed later for diarization quality and speaker-labeled subtitle alignment
- any checkpoint artifacts that the next stage must carry forward without rescanning

Use `non_selected_candidates` for anything visible but not required for the approved working set. This key must always be present even if the array is empty.

Retain verifier-visible RTTM and transcript context in the selected working set until binder-stage packetization.

Do not mark the task complete in this stage.

## Output Contract

`workflow/speaker_diarization_working_set.json` must contain exactly these keys:

- `selected_candidates`: array
- `non_selected_candidates`: array
- `primary_artifact_targets`: array
- `supporting_context_paths`: array
- `pending_continuation_status`: string

`workflow/speaker_diarization_scope_summary.json` must contain exactly these keys:

- `selected_deliverables`: array
- `selected_supporting_context`: array
- `scope_reason`: string
- `next_stage`: string

## Content Rules

Apply these rules when filling the artifacts:

- `primary_artifact_targets` must name the three required outputs: `/root/diarization.rttm`, `/root/subtitles.ass`, `/root/report.json`
- `supporting_context_paths` must stay limited to the source media, verifier-visible RTTM and transcript context, and the checkpoint records needed for ordered continuation
- `pending_continuation_status` must show that the selected set is approved but still pending continuation
- `selected_deliverables` and `selected_supporting_context` must match the approved working set without expanding scope
- `next_stage` must identify the packet binder stage as the immediate continuation
- Keep selected and non-selected entries explicit even when the distinction is small

## Continuation

The next stage consumes these exact keys from `workflow/speaker_diarization_working_set.json`:

- `selected_candidates`
- `non_selected_candidates`
- `primary_artifact_targets`
- `supporting_context_paths`
- `pending_continuation_status`

## Stop Condition

Stop after both workflow files are written and the approved working set clearly separates selected candidates from non-selected candidates while keeping the task in pending continuation status.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the speaker-diarization-subtitles-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
