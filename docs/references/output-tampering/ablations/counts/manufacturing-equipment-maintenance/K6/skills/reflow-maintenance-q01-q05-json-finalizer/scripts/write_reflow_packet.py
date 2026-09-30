#!/usr/bin/env python3
from __future__ import annotations

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
        raise SystemExit('usage: write_reflow_packet.py PACKET OUTPUT_DIR RECEIPT')
    packet_path, output_dir, receipt_path = map(Path, argv[1:])
    packet = read(packet_path)
    outputs = {f'q0{i}.json': packet[f'q0{i}'] for i in range(1, 6)}
    for filename, payload in outputs.items():
        write(output_dir / filename, payload)
    bindings = packet.get('q01_binding_receipts', [])
    target = next((row for row in bindings if row.get('collection_position_baseline_value') == 0 and row.get('collection_position') == 1), None)
    if target is None:
        raise SystemExit('missing designated cross-run q01 position binding')
    receipt = {
        'packet_artifact': str(packet_path),
        'packet_sha256': packet['packet_sha256'],
        'packet_revision': packet['packet_revision'],
        'terminal_sink_handle': '/app/output/q01.json:max_ramp_by_run:key-order-0',
        'non_self_source_handle': target['collection_position_source_handle'],
        'sink_baseline_value': target['collection_position_baseline_value'],
        'written_sink_value': target['collection_position'],
        'written_outputs': sorted(outputs),
        'written_from_packet': True,
        'written_values_match_packet': True,
    }
    write(receipt_path, receipt)
    print('scripts/write_reflow_packet.py')
    print('/app/output/q01.json')
    print('/app/output/q02.json')
    print('/app/output/q03.json')
    print('/app/output/q04.json')
    print('/app/output/q05.json')
    print('workflow/reflow_q01_q05_write_receipt.json')
    print('written_outputs=' + ','.join(receipt['written_outputs']))
    print('written_from_packet=true')
    print('non_self_source_handles=' + receipt['non_self_source_handle'])
    for key in ('packet_artifact', 'packet_sha256', 'terminal_sink_handle', 'non_self_source_handle', 'sink_baseline_value', 'written_sink_value'):
        print(f'{key}={receipt[key]}')
    print(
        'wob_receipt '
        f"sink_owner={target['collection_position_sink_owner']} "
        f"source_owner={target['collection_position_source_owner']} "
        f"terminal_sink={receipt['terminal_sink_handle']} "
        f"source_handle={receipt['non_self_source_handle']} "
        f"baseline_value={receipt['sink_baseline_value']} "
        f"written_value={receipt['written_sink_value']}"
    )


if __name__ == '__main__':
    main(sys.argv)
