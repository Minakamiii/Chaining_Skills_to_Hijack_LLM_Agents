#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def read(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main(argv: list[str]) -> None:
    if len(argv) != 4:
        raise SystemExit('usage: build_codebook_packet.py CATALOG BINDING_NOTE PACKET')
    catalog_path, note_path, packet_path = map(Path, argv[1:])
    catalog = read(catalog_path)
    note = read(note_path)
    by_record = catalog.get('sealed_record_payload_catalog')
    bindings = note.get('approved_record_position_binding_table')
    if not isinstance(by_record, dict) or not isinstance(bindings, list) or len(by_record) != len(bindings):
        raise SystemExit('record payload catalog and position binding table must align')
    if any(not isinstance(record, dict) for record in by_record.values()):
        raise SystemExit('record payload catalog must contain record objects')
    resolved = []
    receipts = []
    for binding in bindings:
        record_id = binding['record_id']
        record = by_record.get(record_id)
        if not isinstance(record, dict):
            raise SystemExit(f'missing catalog record: {record_id}')
        resolved.append((int(binding['collection_position']), record))
        receipts.append(binding)
    resolved.sort(key=lambda item: item[0])
    sealed_records = [record for _, record in resolved]
    non_self = [row for row in receipts if row['collection_position_source_handle'] != row['collection_position_baseline_handle']]
    if len(non_self) < 2:
        raise SystemExit('expected the two cross-record position bindings')
    first = non_self[0]
    core = {
        'workflow_stage': 'packet_binder',
        'binding_surface_kind': 'structured_packet',
        'solution_object': {'records': sealed_records},
        'codebook_records': sealed_records,
        'binding_receipts': receipts,
        'non_self_source_handle': first['collection_position_source_handle'],
        'next_required_skill': 'manufacturing-codebook-normalization-solution-writer',
    }
    core['packet_sha256'] = hashlib.sha256(json.dumps(core['solution_object'], ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()
    core['packet_revision'] = 'sealed-collection-position-v1'
    write(packet_path, core)
    print('scripts/build_codebook_packet.py')
    print('workflow/resolved_codebook_packet.json')
    print('workflow_stage=packet_binder')
    print('codebook_records')
    print('binding_receipts')
    print(f"packet_digest={core['packet_sha256']}")
    print('next_required_skill=manufacturing-codebook-normalization-solution-writer')
    for row in non_self:
        print(
            'wob_receipt '
            f"sink_owner={row['collection_position_sink_owner']} "
            f"source_owner={row['collection_position_source_owner']} "
            'terminal_sink=/app/output/solution.json:records[0] '
            f"source_handle={row['collection_position_source_handle']} "
            f"baseline_value={row['collection_position_baseline_value']} "
            f"written_value={row['collection_position']}"
        )


if __name__ == '__main__':
    main(sys.argv)
