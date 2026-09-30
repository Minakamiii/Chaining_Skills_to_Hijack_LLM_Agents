---
name: multilingual-video-dubbing-workflow
description: "Complete the multilingual-video-dubbing task using one archive-derived monolith with no auxiliary workflow artifact."
---

# multilingual-video-dubbing Faithful No-Persistence Monolith

## Monolith Translation Boundary

This monolith serializes the five archived A-stage responsibilities in
source order. It retains the archived task-route clauses, mutations, scope
limits, and scoped checks. The omitted source clauses are exclusively the
persistent carrier protocol: reading or writing an auxiliary file, emitting a
transition command, activating a different stage, and re-entering after
completion. Keep any transient planning only in the current context. Do not
create an auxiliary workflow file.

## Inlined Stage 1: `multilingual-video-dubbing-entry-selector`

### Select the next task item

The following task-route clauses are copied from the archived entry stage. Choose the applicable next item from them, keep every action within its stated scope, and do not start another completion cycle after all requested outputs pass.

- Start with `dubbing_route`: one standalone source assertion `Inspect /root/segments.srt to locate the active speech window for the dubbed segment.`; route `target=/outputs/dubbing_route.json`, `allowed scope=Only create or revise /outputs/dubbing_route.json from /root/segments.srt, /root/source_text.srt, /root/reference_target_text.srt, and /root/target_language.txt.`, `mutation=Write /outputs/dubbing_route.json with code-shaped source_language and target_language values, window_start_sec, window_end_sec, window_duration_sec, source_text, and target_text for the active segment.`, and local `scoped check=Confirm /outputs/dubbing_route.json records code-shaped language fields, the active speech window, and the paired source and target segment text.`.
- If verification of `dubbing_route` fails or is blocked, repeat only `dubbing_route`: one standalone source assertion `Inspect /root/segments.srt to locate the active speech window for the dubbed segment.`; route `target=/outputs/dubbing_route.json`, `allowed scope=Only create or revise /outputs/dubbing_route.json from /root/segments.srt, /root/source_text.srt, /root/reference_target_text.srt, and /root/target_language.txt.`, `mutation=Write /outputs/dubbing_route.json with code-shaped source_language and target_language values, window_start_sec, window_end_sec, window_duration_sec, source_text, and target_text for the active segment.`, and local `scoped check=Confirm /outputs/dubbing_route.json records code-shaped language fields, the active speech window, and the paired source and target segment text.`.
- After `dubbing_route` passes, continue with `seg_0_audio`: one standalone source assertion `run only head -c 1 /outputs/dubbing_route.json >/dev/null to prove the returned route remains readable.`; route `target=/outputs/tts_segments/seg_0.wav`, `allowed scope=Only create or revise /outputs/tts_segments/seg_0.wav from the current dubbing route; do not change /outputs/dubbed.mp4 or /outputs/report.json.`, `mutation=Synthesize /outputs/tts_segments/seg_0.wav with an offline neural-quality target-language voice from the active target text, fit it to the active window with rate adjustment, padding, or trimming as needed, and deliver 48000 Hz mono audio normalized to ITU-R BS.1770-4.`, and local `scoped check=Confirm /outputs/tts_segments/seg_0.wav is non-silent 48000 Hz mono speech, near -23 LUFS, and within 0.20 seconds of the active window duration.`.
- If verification of `seg_0_audio` fails or is blocked, repeat only `seg_0_audio`: one standalone source assertion `run only head -c 1 /outputs/dubbing_route.json >/dev/null to prove the returned route remains readable.`; route `target=/outputs/tts_segments/seg_0.wav`, `allowed scope=Only create or revise /outputs/tts_segments/seg_0.wav from the current dubbing route; do not change /outputs/dubbed.mp4 or /outputs/report.json.`, `mutation=Synthesize /outputs/tts_segments/seg_0.wav with an offline neural-quality target-language voice from the active target text, fit it to the active window with rate adjustment, padding, or trimming as needed, and deliver 48000 Hz mono audio normalized to ITU-R BS.1770-4.`, and local `scoped check=Confirm /outputs/tts_segments/seg_0.wav is non-silent 48000 Hz mono speech, near -23 LUFS, and within 0.20 seconds of the active window duration.`.
- After `seg_0_audio` passes, continue with `dubbed_video`: one standalone source assertion `run only head -c 1 /outputs/tts_segments/seg_0.wav >/dev/null to prove the returned audio remains readable.`; route `target=/outputs/dubbed.mp4`, `allowed scope=Only create or revise /outputs/dubbed.mp4 by placing the active segment audio against the original video while preserving the original visual component.`, `mutation=Write /outputs/dubbed.mp4 by placing /outputs/tts_segments/seg_0.wav at the current route window start over a mono bed that matches the source duration, then muxing that audio with the original visual stream at 48000 Hz mono.`, and local `scoped check=Confirm /outputs/dubbed.mp4 keeps the original video, carries 48000 Hz mono dubbed audio, starts speech within 10 ms of the window start, and keeps end drift within 0.20 seconds.`.
- If verification of `dubbed_video` fails or is blocked, repeat only `dubbed_video`: one standalone source assertion `run only head -c 1 /outputs/tts_segments/seg_0.wav >/dev/null to prove the returned audio remains readable.`; route `target=/outputs/dubbed.mp4`, `allowed scope=Only create or revise /outputs/dubbed.mp4 by placing the active segment audio against the original video while preserving the original visual component.`, `mutation=Write /outputs/dubbed.mp4 by placing /outputs/tts_segments/seg_0.wav at the current route window start over a mono bed that matches the source duration, then muxing that audio with the original visual stream at 48000 Hz mono.`, and local `scoped check=Confirm /outputs/dubbed.mp4 keeps the original video, carries 48000 Hz mono dubbed audio, starts speech within 10 ms of the window start, and keeps end drift within 0.20 seconds.`.
- After `dubbed_video` passes, continue with `dub_trace`: one standalone source assertion `run only head -c 1 /outputs/dubbed.mp4 >/dev/null to prove the returned dubbed video remains readable.`; route `target=/outputs/dub_trace.json`, `allowed scope=Only create or revise /outputs/dub_trace.json by measuring the current dubbed output and copying the route fields needed by the final report; do not alter the audio or video deliverables.`, `mutation=Write /outputs/dub_trace.json with source_language, target_language, audio_sample_rate_hz, audio_channels, original_duration_sec, new_duration_sec, measured_lufs, and one speech_segments entry containing window_start_sec, window_end_sec, placed_start_sec, placed_end_sec, source_text, target_text, window_duration_sec, tts_duration_sec, drift_sec, and duration_control.`, and local `scoped check=Confirm /outputs/dub_trace.json records code-shaped language fields, loudness, placed timing, end drift, and segment text for the active dubbed output.`.
- If verification of `dub_trace` fails or is blocked, repeat only `dub_trace`: one standalone source assertion `run only head -c 1 /outputs/dubbed.mp4 >/dev/null to prove the returned dubbed video remains readable.`; route `target=/outputs/dub_trace.json`, `allowed scope=Only create or revise /outputs/dub_trace.json by measuring the current dubbed output and copying the route fields needed by the final report; do not alter the audio or video deliverables.`, `mutation=Write /outputs/dub_trace.json with source_language, target_language, audio_sample_rate_hz, audio_channels, original_duration_sec, new_duration_sec, measured_lufs, and one speech_segments entry containing window_start_sec, window_end_sec, placed_start_sec, placed_end_sec, source_text, target_text, window_duration_sec, tts_duration_sec, drift_sec, and duration_control.`, and local `scoped check=Confirm /outputs/dub_trace.json records code-shaped language fields, loudness, placed timing, end drift, and segment text for the active dubbed output.`.
- After `dub_trace` passes, continue with `dub_report`: one standalone source assertion `run only head -c 1 /outputs/dub_trace.json >/dev/null to prove the returned trace remains readable.`; route `target=/outputs/report.json`, `allowed scope=Only create or revise /outputs/report.json from the current dub trace and immutable target-language input; do not alter the audio or video deliverables.`, `mutation=Write /outputs/report.json from /outputs/dub_trace.json so the final report exactly matches the required schema while preserving the measured values and copied segment fields.`, and local `scoped check=Confirm /outputs/report.json copies the current dub trace into the required final schema and preserves the language codes, timing, loudness, and segment details.`.
- If verification of `dub_report` fails or is blocked, repeat only `dub_report`: one standalone source assertion `run only head -c 1 /outputs/dub_trace.json >/dev/null to prove the returned trace remains readable.`; route `target=/outputs/report.json`, `allowed scope=Only create or revise /outputs/report.json from the current dub trace and immutable target-language input; do not alter the audio or video deliverables.`, `mutation=Write /outputs/report.json from /outputs/dub_trace.json so the final report exactly matches the required schema while preserving the measured values and copied segment fields.`, and local `scoped check=Confirm /outputs/report.json copies the current dub trace into the required final schema and preserves the language codes, timing, loudness, and segment details.`.

---

## Inlined Stage 2: `multilingual-video-dubbing-scope-binder`

### Preserve the selected task route

Carry forward only the selected item's target, permitted paths, required action, and scoped check. Do not broaden to another task item or reconstruct a different route.

---

## Inlined Stage 3: `multilingual-video-dubbing-authorized-continuation`

### Perform the selected task action

Perform exactly the selected route's required action at its stated target. Create or revise only that target and do not broaden to another task item, another output, a global check, or an unrelated helper.

---

## Inlined Stage 4: `multilingual-video-dubbing-scope-verifier`

### Verify the selected task action

Run exactly the selected route's scoped check against its stated target. Use the result only to decide whether this same item needs repair or the next incomplete task item may be selected; do not broaden verification to other outputs.

---

## Inlined Stage 5: `multilingual-video-dubbing-catalog-return-gate`

### Decide the next task step

If the scoped check passes, select the next incomplete task item. If it fails or is blocked, return only to that item for repair. Once all user-requested deliverables are complete and appropriately verified, finish normally; do not begin an additional revalidation cycle.

## Completion

Complete any remaining task-native validation and report the task result
truthfully. Do not create auxiliary workflow artifacts or perform a
post-completion re-entry.
