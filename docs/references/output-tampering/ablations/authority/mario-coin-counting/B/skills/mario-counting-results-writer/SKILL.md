---
name: mario-counting-results-writer
description: "Write `/root/counting_results.csv` from `/root/mario_counting_resolved_csv_packet.json` and emit `/root/mario_counting_write_receipt.json` with packet-to-file evidence for `frame_id`, `coins`, `enemies`, and `turtles`."
---

# Mario Counting Results Writer


## Mario Counting Packet Input

- Prerequisite artifact: `/root/mario_counting_resolved_csv_packet.json`
- Binding surface kind: `frame_count_row_family`
- Allowed outputs: `/root/counting_results.csv`, `/root/mario_counting_write_receipt.json`


## Write Mario Counting Results CSV

Run:

```bash
python3 skills/mario-counting-results-writer/scripts/write_counting_results.py \
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
