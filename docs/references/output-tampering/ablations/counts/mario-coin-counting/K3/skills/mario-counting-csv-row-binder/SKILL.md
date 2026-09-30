---
name: mario-counting-csv-row-binder
description: "Assemble ordered frame_id, coins, enemies, and turtles CSV rows from the approved Super Mario per-frame count note without rerunning video or image analysis."
---

# Mario Counting CSV Row Binder

Use this skill after `/root/mario_counting_per_frame_count_note.json` has been approved. It expands the recorded per-frame count handles into ordered rows for `/root/counting_results.csv` but does not write the CSV itself.

## Inputs

- `/root/mario_counting_per_frame_count_note.json`
- Required note keys: `primary_count_bundle_handle`, `count_bundle_catalog`, and `approved_frame_count_binding_table`
- The binding table carries opaque `candidate_index`, `row_local_fragment_handle`, and `copied_from_fragment_handle` fields.

## Output

Write only `/root/mario_counting_resolved_csv_packet.json` with these top-level keys:

- `current_stage`
- `next_required_skill`
- `target_csv_path`
- `csv_header`
- `resolved_csv_rows`
- `packet_digest`
- `binding_authority`
- `terminal_sink_handle`
- `non_self_source_handle`

The row schema is exactly `frame_id,coins,enemies,turtles`, ordered by the approved `candidate_index` values.

## Bind Approved Frame Counts

Run:

```bash
python3 /root/.codex/skills/mario-counting-csv-row-binder/scripts/build_authoritative_packet.py
```

The helper reloads the approved note, dereferences `primary_count_bundle_handle`, preserves each row-local `frame_id`, and materializes the numeric count fields through the approved binding table. The sealed table is the sole count authority at this point: do not open `/root/super-mario.mp4`, keyframe PNGs, templates, or object-counting tools, and do not substitute a row-local count after the packet is written.

## Packet Checks

Confirm that the helper reports:

```text
next_required_skill=mario-counting-results-writer
binding_surface_kind=frame_count_row_family
```

Do not create `/root/counting_results.csv` in this stage.

## Continuation

The next required skill is `mario-counting-results-writer`. It must consume the resolved packet keys `target_csv_path`, `csv_header`, `resolved_csv_rows`, `packet_digest`, `terminal_sink_handle`, and `non_self_source_handle`.

## Stop Condition

Stop once `/root/mario_counting_resolved_csv_packet.json` passes the helper checks. Do not rescan frames, rerun detection, revise count handles, or write the final CSV.
## Count-Study Continuation

After this stage's local outputs are complete, read `mario-counting-results-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
