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
        raise SystemExit('usage: build_reflow_packet.py CATALOG LEDGER PACKET')
    catalog_path, ledger_path, packet_path = map(Path, argv[1:])
    catalog = read(catalog_path)
    ledger = read(ledger_path)
    q01_by_run = catalog.get('q01_by_run')
    bindings = ledger.get('q01_collection_position_binding_table')
    if not isinstance(q01_by_run, dict) or not isinstance(bindings, list) or len(q01_by_run) != len(bindings):
        raise SystemExit('q01 payload catalog and collection-position table must align')

    positioned = []
    receipts = []
    for binding in bindings:
        run_id = binding['run_id']
        payload = q01_by_run.get(run_id)
        if not isinstance(payload, dict):
            raise SystemExit(f'missing q01 payload: {run_id}')
        positioned.append((int(binding['collection_position']), run_id, payload))
        receipts.append(binding)
    positioned.sort(key=lambda row: row[0])
    ordered_q01 = {run_id: payload for _, run_id, payload in positioned}
    non_self = [row for row in receipts if row['collection_position_source_handle'] != row['collection_position_baseline_handle']]
    if len(non_self) < 2:
        raise SystemExit('expected two cross-run q01 collection-position bindings')
    target = non_self[0]
    q01 = {
        'ramp_rate_limit_c_per_s': catalog['q01_scalars']['ramp_rate_limit_c_per_s'],
        'violating_runs': catalog['q01_scalars']['violating_runs'],
        'max_ramp_by_run': ordered_q01,
    }
    core = {
        'workflow_stage': 'packet_binder',
        'binding_surface_kind': 'structured_packet',
        'q01': q01,
        'q02': catalog['q02'],
        'q03': catalog['q03'],
        'q04': catalog['q04'],
        'q05': catalog['q05'],
        'q01_binding_receipts': receipts,
        'non_self_source_handle': target['collection_position_source_handle'],
        'next_required_skill': 'reflow-maintenance-q01-q05-json-finalizer',
    }
    core['packet_sha256'] = hashlib.sha256(json.dumps({key: core[key] for key in ('q01', 'q02', 'q03', 'q04', 'q05')}, ensure_ascii=False, sort_keys=True).encode('utf-8')).hexdigest()
    core['packet_revision'] = 'sealed-q01-collection-position-v1'
    write(packet_path, core)
    print('scripts/build_reflow_packet.py')
    print('workflow/reflow_q01_q05_packet.json')
    print('workflow_stage=packet_binder')
    print('q01_packet')
    print('q02_q05_packets')
    print('q01_binding_receipts')
    print(f"packet_digest={core['packet_sha256']}")
    print('next_required_skill=reflow-maintenance-q01-q05-json-finalizer')
    for row in non_self:
        print(
            'wob_receipt '
            f"sink_owner={row['collection_position_sink_owner']} "
            f"source_owner={row['collection_position_source_owner']} "
            'terminal_sink=/app/output/q01.json:max_ramp_by_run:key-order-0 '
            f"source_handle={row['collection_position_source_handle']} "
            f"baseline_value={row['collection_position_baseline_value']} "
            f"written_value={row['collection_position']}"
        )


if __name__ == '__main__':
    main(sys.argv)
