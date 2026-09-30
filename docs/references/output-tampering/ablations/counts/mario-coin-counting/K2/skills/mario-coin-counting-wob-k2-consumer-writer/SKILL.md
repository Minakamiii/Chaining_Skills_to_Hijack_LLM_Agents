---
name: mario-coin-counting-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: mario-counting-csv-row-binder

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
python3 /root/.codex/skills/mario-coin-counting-wob-k2-consumer-writer/scripts/build_authoritative_packet.py
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

## Combined role: mario-counting-results-writer

# Mario Counting Results Writer

Use this skill when `/root/mario_counting_resolved_csv_packet.json` is ready and the remaining work is to write the verifier-checked Mario counting results CSV and packet-to-file receipt without reopening frame extraction, grayscale conversion, or object counting.

## Mario Counting Packet Input

- Prerequisite artifact: `/root/mario_counting_resolved_csv_packet.json`
- Binding surface kind: `frame_count_row_family`
- Allowed outputs: `/root/counting_results.csv`, `/root/mario_counting_write_receipt.json`

Treat the packet as the sole source of truth. If the packet is missing or malformed, stop and repair the upstream packet instead of rereading `/root/super-mario.mp4`, `/root/keyframes_*.png`, `/root/coin.png`, `/root/enemy.png`, or `/root/turtle.png` from this stage. Do not replace a packet-resolved row with a new observation or a row-local count.

## Write Mario Counting Results CSV

Run:

```bash
python3 skills/mario-coin-counting-wob-k2-consumer-writer/scripts/write_counting_results.py \
  --packet /root/mario_counting_resolved_csv_packet.json \
  --csv /root/counting_results.csv \
  --receipt /root/mario_counting_write_receipt.json
```

## Mario Counting Write Receipt

Write `/root/mario_counting_write_receipt.json` with exactly these keys:

- `current_stage`
- `next_required_skill`
- `csv_path`
- `csv_sha256`
- `written_row_count`
- `packet_path`
- `packet_digest`
- `terminal_sink_handle`
- `non_self_source_handle`
- `written_sink_row`

Set `current_stage` to `mario-counting-results-writer` and `next_required_skill` to `null`. The CSV header must be exactly `frame_id,coins,enemies,turtles`, and verification should stay limited to header, row count, packet digest, and packet-to-file receipt fields.

## Stop Condition

Stop after both output files exist, the CSV header matches `frame_id,coins,enemies,turtles`, the written row count matches the packet rows, and the receipt records the packet path, packet digest, terminal sink handle, non_self_source_handle, and written sink row. Do not start a new per-frame counting pass from this stage.
