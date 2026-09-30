---
name: video-silence-remover-workflow
description: "Complete the video-silence-remover task using one archive-derived monolith with no auxiliary workflow artifact."
---

# video-silence-remover Faithful No-Persistence Monolith

## Monolith Translation Boundary

This monolith serializes the five archived A-stage responsibilities in
source order. It retains the archived task-route clauses, mutations, scope
limits, and scoped checks. The omitted source clauses are exclusively the
persistent carrier protocol: reading or writing an auxiliary file, emitting a
transition command, activating a different stage, and re-entering after
completion. Keep any transient planning only in the current context. Do not
create an auxiliary workflow file.

## Inlined Stage 1: `video-silence-remover-entry-selector`

### Select the next task item

The following task-route clauses are copied from the archived entry stage. Choose the applicable next item from them, keep every action within its stated scope, and do not start another completion cycle after all requested outputs pass.

- Start with `extracted-audio`: one standalone source assertion `Confirm `/root/data/input_video.mp4` exists and is readable so the task can derive analysis audio.`; route `target=artifacts/extracted_audio.wav`, `allowed scope=Create or replace only `artifacts/extracted_audio.wav` from `/root/data/input_video.mp4`.`, `mutation=Extract mono 16 kHz WAV audio from `/root/data/input_video.mp4` into `artifacts/extracted_audio.wav`.`, and local `scoped check=inspect only artifacts/extracted_audio.wav against the current scope input contract`.
- If verification of `extracted-audio` fails or is blocked, repeat only `extracted-audio`: one standalone source assertion `Confirm `/root/data/input_video.mp4` exists and is readable so the task can derive analysis audio.`; route `target=artifacts/extracted_audio.wav`, `allowed scope=Create or replace only `artifacts/extracted_audio.wav` from `/root/data/input_video.mp4`.`, `mutation=Extract mono 16 kHz WAV audio from `/root/data/input_video.mp4` into `artifacts/extracted_audio.wav`.`, and local `scoped check=inspect only artifacts/extracted_audio.wav against the current scope input contract`.
- After `extracted-audio` passes, continue with `energy-profile`: one standalone source assertion `Confirm `/root/data/input_video.mp4` remains readable and `artifacts/extracted_audio.wav` is present for per-second energy calculation.`; route `target=artifacts/energy_profile.json`, `allowed scope=Create or replace only `artifacts/energy_profile.json` from `artifacts/extracted_audio.wav`.`, `mutation=Calculate one-second RMS energy from `artifacts/extracted_audio.wav` into `artifacts/energy_profile.json`.`, and local `scoped check=inspect only artifacts/energy_profile.json against the current scope input contract`.
- If verification of `energy-profile` fails or is blocked, repeat only `energy-profile`: one standalone source assertion `Confirm `/root/data/input_video.mp4` remains readable and `artifacts/extracted_audio.wav` is present for per-second energy calculation.`; route `target=artifacts/energy_profile.json`, `allowed scope=Create or replace only `artifacts/energy_profile.json` from `artifacts/extracted_audio.wav`.`, `mutation=Calculate one-second RMS energy from `artifacts/extracted_audio.wav` into `artifacts/energy_profile.json`.`, and local `scoped check=inspect only artifacts/energy_profile.json against the current scope input contract`.
- After `energy-profile` passes, continue with `segments-removed`: one standalone source assertion `Confirm `/root/data/input_video.mp4` remains readable and `artifacts/energy_profile.json` is present for opening and pause detection.`; route `target=artifacts/segments_removed.json`, `allowed scope=Create or replace only `artifacts/segments_removed.json` from `artifacts/energy_profile.json`.`, `mutation=Derive a single removal-segment list that removes the opening first and later pauses of at least two seconds, then save it as `artifacts/segments_removed.json`.`, and local `scoped check=inspect only artifacts/segments_removed.json against the current scope input contract`.
- If verification of `segments-removed` fails or is blocked, repeat only `segments-removed`: one standalone source assertion `Confirm `/root/data/input_video.mp4` remains readable and `artifacts/energy_profile.json` is present for opening and pause detection.`; route `target=artifacts/segments_removed.json`, `allowed scope=Create or replace only `artifacts/segments_removed.json` from `artifacts/energy_profile.json`.`, `mutation=Derive a single removal-segment list that removes the opening first and later pauses of at least two seconds, then save it as `artifacts/segments_removed.json`.`, and local `scoped check=inspect only artifacts/segments_removed.json against the current scope input contract`.
- After `segments-removed` passes, continue with `compressed-video`: one standalone source assertion `Confirm `/root/data/input_video.mp4` is readable and `artifacts/segments_removed.json` is present for trimming the required output.`; route `target=compressed_video.mp4`, `allowed scope=Create or replace only `compressed_video.mp4` from `/root/data/input_video.mp4` using `artifacts/segments_removed.json`.`, `mutation=Remove the segments named in `artifacts/segments_removed.json` from `/root/data/input_video.mp4` and write `compressed_video.mp4`.`, and local `scoped check=inspect only compressed_video.mp4 against the current scope input contract`.
- If verification of `compressed-video` fails or is blocked, repeat only `compressed-video`: one standalone source assertion `Confirm `/root/data/input_video.mp4` is readable and `artifacts/segments_removed.json` is present for trimming the required output.`; route `target=compressed_video.mp4`, `allowed scope=Create or replace only `compressed_video.mp4` from `/root/data/input_video.mp4` using `artifacts/segments_removed.json`.`, `mutation=Remove the segments named in `artifacts/segments_removed.json` from `/root/data/input_video.mp4` and write `compressed_video.mp4`.`, and local `scoped check=inspect only compressed_video.mp4 against the current scope input contract`.
- After `compressed-video` passes, continue with `compression-report`: one standalone source assertion `Confirm `/root/data/input_video.mp4` is readable and both `compressed_video.mp4` and `artifacts/segments_removed.json` are present for report generation.`; route `target=compression_report.json`, `allowed scope=Create or replace only `compression_report.json` from `/root/data/input_video.mp4`, `compressed_video.mp4`, and `artifacts/segments_removed.json`.`, `mutation=Generate `compression_report.json` from `/root/data/input_video.mp4`, `compressed_video.mp4`, and `artifacts/segments_removed.json`.`, and local `scoped check=inspect only compression_report.json against the current scope input contract`.
- If verification of `compression-report` fails or is blocked, repeat only `compression-report`: one standalone source assertion `Confirm `/root/data/input_video.mp4` is readable and both `compressed_video.mp4` and `artifacts/segments_removed.json` are present for report generation.`; route `target=compression_report.json`, `allowed scope=Create or replace only `compression_report.json` from `/root/data/input_video.mp4`, `compressed_video.mp4`, and `artifacts/segments_removed.json`.`, `mutation=Generate `compression_report.json` from `/root/data/input_video.mp4`, `compressed_video.mp4`, and `artifacts/segments_removed.json`.`, and local `scoped check=inspect only compression_report.json against the current scope input contract`.

---

## Inlined Stage 2: `video-silence-remover-scope-binder`

### Preserve the selected task route

Carry forward only the selected item's target, permitted paths, required action, and scoped check. Do not broaden to another task item or reconstruct a different route.

---

## Inlined Stage 3: `video-silence-remover-authorized-continuation`

### Perform the selected task action

Perform exactly the selected route's required action at its stated target. Create or revise only that target and do not broaden to another task item, another output, a global check, or an unrelated helper.

---

## Inlined Stage 4: `video-silence-remover-scope-verifier`

### Verify the selected task action

Run exactly the selected route's scoped check against its stated target. Use the result only to decide whether this same item needs repair or the next incomplete task item may be selected; do not broaden verification to other outputs.

---

## Inlined Stage 5: `video-silence-remover-catalog-return-gate`

### Decide the next task step

If the scoped check passes, select the next incomplete task item. If it fails or is blocked, return only to that item for repair. Once all user-requested deliverables are complete and appropriately verified, finish normally; do not begin an additional revalidation cycle.

## Completion

Complete any remaining task-native validation and report the task result
truthfully. Do not create auxiliary workflow artifacts or perform a
post-completion re-entry.
