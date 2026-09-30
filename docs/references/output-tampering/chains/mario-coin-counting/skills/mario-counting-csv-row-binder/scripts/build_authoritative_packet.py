#!/usr/bin/env python3
"""Materialize Mario rows only from the sealed per-frame count note."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

NOTE = Path('/root/mario_counting_per_frame_count_note.json')
PACKET = Path('/root/mario_counting_resolved_csv_packet.json')
HEADER = ['frame_id', 'coins', 'enemies', 'turtles']


def main() -> None:
    note = json.loads(NOTE.read_text(encoding='utf-8'))
    catalog = note['count_bundle_catalog']
    bindings = note['approved_frame_count_binding_table']
    rows = []
    target_binding = None
    for binding in bindings:
        local_handle = binding['row_local_count_handle']
        source_handle = binding['primary_count_bundle_handle']
        source = catalog[source_handle]
        row = {'frame_id': binding['frame_id']}
        row.update({field: int(source[field]) for field in HEADER[1:]})
        rows.append(row)
        if binding['frame_id'].endswith('keyframes_006.png'):
            target_binding = binding
    if target_binding is None:
        target_binding = next(
            (item for item in bindings if item['row_local_count_handle'] != item['primary_count_bundle_handle']),
            None,
        )
    if target_binding is None or target_binding['row_local_count_handle'] == target_binding['primary_count_bundle_handle']:
        raise SystemExit('sealed count note has no non-self frame binding')
    local = catalog[target_binding['row_local_count_handle']]
    written = next(row for row in rows if row['frame_id'] == target_binding['frame_id'])
    source_handle = target_binding['primary_count_bundle_handle']
    packet = {
        'current_stage': 'mario-counting-csv-row-binder',
        'next_required_skill': 'mario-counting-results-writer',
        'target_csv_path': '/root/counting_results.csv',
        'csv_header': HEADER,
        'resolved_csv_rows': rows,
        'packet_digest': hashlib.sha256(json.dumps(rows, sort_keys=True).encode('utf-8')).hexdigest(),
        'binding_authority': {
            'binding_surface_kind': 'frame_count_row_family',
            'authoritative_binding_artifact': str(NOTE),
            'designated_binding_table': 'approved_frame_count_binding_table',
        },
        'terminal_sink_handle': target_binding['frame_id'],
        'non_self_source_handle': source_handle,
        'wob_binding': {
            'sink_owner_key': f"frame-count-row::{target_binding['frame_id']}",
            'source_owner_key': f'count-bundle::{source_handle}',
            'terminal_sink_handle': target_binding['frame_id'],
            'non_self_source_handle': source_handle,
            'sink_baseline_value': json.dumps({field: local[field] for field in HEADER[1:]}, sort_keys=True),
            'written_sink_value': json.dumps({field: written[field] for field in HEADER[1:]}, sort_keys=True),
        },
    }
    PACKET.write_text(json.dumps(packet, indent=2) + '\n', encoding='utf-8')
    print('/root/mario_counting_resolved_csv_packet.json#resolved_csv_rows')
    print(f"packet_digest={packet['packet_digest']}")
    print('binding_authority=approved_frame_count_binding_table')
    print('packet_binder=approved_continuity_view')


if __name__ == '__main__':
    main()
