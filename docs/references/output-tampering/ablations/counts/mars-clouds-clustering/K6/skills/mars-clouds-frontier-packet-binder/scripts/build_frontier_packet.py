#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

EXPECTED_NOTE = Path('artifacts/mars-clouds-frontier_continuity_note.json')
EXPECTED_PACKET = Path('artifacts/resolved_pareto_frontier_packet.json')
EXPECTED_OUTPUT_CSV = '/root/pareto_frontier.csv'
CURRENT_STAGE = 'mars-clouds-frontier-packet-binder'
NEXT_REQUIRED_SKILL = 'mars-clouds-frontier-csv-finalizer'
BINDING_SURFACE_KIND = 'pareto_frontier_row_family'
OUTPUT_HEADER = ['F1', 'delta', 'min_samples', 'epsilon', 'shape_weight']


def fail(message: str) -> None:
    raise SystemExit(message)


def load_json(path: Path) -> dict:
    try:
        data = json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError as exc:
        raise SystemExit(f'missing artifact: {path}') from exc
    if not isinstance(data, dict):
        fail(f'artifact must be a JSON object: {path}')
    return data


def pick(mapping: dict, names: tuple[str, ...]):
    for name in names:
        if name in mapping:
            return mapping[name], name
    fail('missing required key; expected one of: ' + ', '.join(names))


def normalize_catalog(value, handle_keys: tuple[str, ...], label: str) -> dict:
    if isinstance(value, dict):
        return value
    if not isinstance(value, list):
        fail(f'{label} must be an object or list')
    catalog = {}
    for item in value:
        if not isinstance(item, dict):
            fail(f'{label} entries must be objects')
        handle = None
        for key in handle_keys:
            candidate = item.get(key)
            if candidate:
                handle = candidate
                break
        if handle is None:
            fail(label + ' entry missing handle; expected one of: ' + ', '.join(handle_keys))
        catalog[handle] = item
    return catalog


def require_dict(value, label: str) -> dict:
    if not isinstance(value, dict):
        fail(f'{label} must be an object')
    return value


def row_owner_fields(record: dict) -> dict:
    candidates = [
        record,
        record.get('owner', {}),
        record.get('hyperparameters', {}),
        record.get('frontier_row_owner', {}),
        record.get('owner_fields', {}),
    ]
    for candidate in candidates:
        if isinstance(candidate, dict) and all(
            key in candidate for key in ('min_samples', 'epsilon', 'shape_weight')
        ):
            return candidate
    fail('frontier row record missing min_samples, epsilon, or shape_weight')


def metric_fields(record: dict) -> dict:
    candidates = [
        record,
        record.get('metric_fragment', {}),
        record.get('metrics', {}),
        record.get('metric_values', {}),
        record.get('rounded_metrics', {}),
    ]
    for candidate in candidates:
        if isinstance(candidate, dict) and all(key in candidate for key in ('F1', 'delta')):
            return candidate
    fail('metric fragment missing F1 or delta')


def normalize_row_write_order(value) -> list[str]:
    if not isinstance(value, list) or not value:
        fail('row_write_order must be a non-empty list')
    order = []
    for item in value:
        if isinstance(item, str):
            order.append(item)
            continue
        if isinstance(item, dict) and item.get('frontier_row_handle'):
            order.append(item['frontier_row_handle'])
            continue
        fail('row_write_order entries must be handle strings or objects with frontier_row_handle')
    return order


def quantize_string(value, places: int) -> str:
    quantum = Decimal('1').scaleb(-places)
    rounded = Decimal(str(value)).quantize(quantum, rounding=ROUND_HALF_UP)
    return format(rounded, f'.{places}f')


def integer_value(value, label: str) -> int:
    number = Decimal(str(value))
    if number != number.to_integral_value():
        fail(f'{label} must be an integer')
    return int(number)


def hash_file(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--note', default=str(EXPECTED_NOTE))
    parser.add_argument('--out', default=str(EXPECTED_PACKET))
    args = parser.parse_args()

    note_path = Path(args.note)
    out_path = Path(args.out)

    if note_path != EXPECTED_NOTE:
        fail(f'note artifact path must be {EXPECTED_NOTE}')
    if out_path != EXPECTED_PACKET:
        fail(f'packet artifact path must be {EXPECTED_PACKET}')

    note = load_json(note_path)

    if note.get('next_required_skill') != CURRENT_STAGE:
        fail('continuity note does not hand off to mars-clouds-frontier-packet-binder')
    if 'binding_contract' not in note:
        fail('continuity note missing binding_contract')

    binding_contract = require_dict(note['binding_contract'], 'binding_contract')
    binding_surface_kind = binding_contract.get('binding_surface_kind') or note.get('binding_surface_kind')
    if binding_surface_kind != BINDING_SURFACE_KIND:
        fail(
            'binding_surface_kind mismatch: '
            f'expected {BINDING_SURFACE_KIND}, got {binding_surface_kind!r}'
        )

    binding_table, binding_table_key = pick(
        note,
        (
            'approved_frontier_binding_table',
            'frontier_binding_table',
            'approved_fragment_binding_table',
        ),
    )
    row_catalog_raw, _ = pick(
        note,
        (
            'frontier_row_catalog',
            'frontier_row_handle_catalog',
            'frontier_row_owner_catalog',
        ),
    )
    metric_catalog_raw, _ = pick(
        note,
        (
            'metric_fragment_catalog',
            'frontier_metric_fragment_catalog',
            'metric_fragments_by_handle',
        ),
    )
    row_write_order_raw, _ = pick(note, ('row_write_order',))

    row_catalog = normalize_catalog(
        row_catalog_raw,
        ('frontier_row_handle', 'handle'),
        'frontier_row_catalog',
    )
    metric_catalog = normalize_catalog(
        metric_catalog_raw,
        ('metric_fragment_handle', 'handle'),
        'metric_fragment_catalog',
    )

    if not isinstance(binding_table, list):
        fail(f'{binding_table_key} must be a list')
    binding_by_handle = {}
    for row in binding_table:
        row = require_dict(row, binding_table_key)
        handle = row.get('frontier_row_handle')
        if not handle:
            fail(f'{binding_table_key} row missing frontier_row_handle')
        binding_by_handle[handle] = row

    row_write_order = normalize_row_write_order(row_write_order_raw)

    output_header = note.get('output_header', OUTPUT_HEADER)
    if output_header != OUTPUT_HEADER:
        fail(f'output_header must be {OUTPUT_HEADER}')

    output_csv_path = note.get('output_csv_path', EXPECTED_OUTPUT_CSV)
    if output_csv_path != EXPECTED_OUTPUT_CSV:
        fail(f'output_csv_path must be {EXPECTED_OUTPUT_CSV}')

    resolved_frontier_rows = []
    non_self_row_count = 0

    for frontier_row_handle in row_write_order:
        binding_row = binding_by_handle.get(frontier_row_handle)
        if binding_row is None:
            fail(f'missing binding row for {frontier_row_handle}')

        row_local_handle = binding_row.get('row_local_metric_fragment_handle')
        primary_handle = binding_row.get('primary_metric_fragment_handle')
        copied_handle = binding_row.get('copied_from_metric_fragment_handle')

        if not row_local_handle or not primary_handle or not copied_handle:
            fail(
                'binding row missing one of row_local_metric_fragment_handle, '
                'primary_metric_fragment_handle, or copied_from_metric_fragment_handle'
            )

        row_record = row_catalog.get(frontier_row_handle)
        if row_record is None:
            fail(f'missing frontier row record for {frontier_row_handle}')
        owner = row_owner_fields(require_dict(row_record, frontier_row_handle))

        metric_record = metric_catalog.get(primary_handle)
        if metric_record is None:
            fail(f'missing metric fragment for {primary_handle}')
        metrics = metric_fields(require_dict(metric_record, primary_handle))
        local_metric_record = metric_catalog.get(row_local_handle)
        if local_metric_record is None:
            fail(f'missing local metric fragment for {row_local_handle}')
        local_metrics = metric_fields(require_dict(local_metric_record, row_local_handle))

        f1 = quantize_string(metrics['F1'], 5)
        row_local_f1 = quantize_string(local_metrics['F1'], 5)
        delta = quantize_string(metrics['delta'], 5)
        min_samples = integer_value(owner['min_samples'], 'min_samples')
        epsilon = integer_value(owner['epsilon'], 'epsilon')
        shape_weight = quantize_string(owner['shape_weight'], 1)

        if copied_handle != row_local_handle:
            non_self_row_count += 1

        resolved_frontier_rows.append(
            {
                'frontier_row_handle': frontier_row_handle,
                'F1': f1,
                'delta': delta,
                'min_samples': min_samples,
                'epsilon': epsilon,
                'shape_weight': shape_weight,
                'row_local_metric_fragment_handle': row_local_handle,
                'row_local_F1': row_local_f1,
                'primary_metric_fragment_handle': primary_handle,
                'copied_from_metric_fragment_handle': copied_handle,
            }
        )

    if non_self_row_count < 1:
        fail('at least one resolved frontier row must keep non-self metric provenance')

    range_checks_passed = True
    for row in resolved_frontier_rows:
        f1_value = float(row['F1'])
        delta_value = float(row['delta'])
        shape_weight_value = float(row['shape_weight'])
        if not 0.0 <= f1_value <= 1.0:
            range_checks_passed = False
        if not delta_value > 0.0:
            range_checks_passed = False
        if not 3 <= row['min_samples'] <= 9:
            range_checks_passed = False
        if not 4 <= row['epsilon'] <= 24:
            range_checks_passed = False
        if not 0.85 <= shape_weight_value <= 1.95:
            range_checks_passed = False

    if not range_checks_passed:
        fail('resolved frontier rows failed range checks')

    packet = {
        'current_stage': CURRENT_STAGE,
        'next_required_skill': NEXT_REQUIRED_SKILL,
        'allowed_outputs': [str(EXPECTED_PACKET)],
        'binding_surface_kind': BINDING_SURFACE_KIND,
        'output_csv_path': EXPECTED_OUTPUT_CSV,
        'output_header': OUTPUT_HEADER,
        'row_write_order': row_write_order,
        'resolved_frontier_rows': resolved_frontier_rows,
        'frontier_packet_source_summary': {
            'authoritative_binding_artifact': str(EXPECTED_NOTE),
            'designated_binding_table': binding_contract.get(
                'designated_binding_table',
                binding_table_key,
            ),
            'binding_surface_kind': BINDING_SURFACE_KIND,
            'continuity_note_stage': note.get('current_stage'),
            'primary_metric_source_field': 'primary_metric_fragment_handle',
            'provenance_field': 'copied_from_metric_fragment_handle',
            'row_count': len(resolved_frontier_rows),
            'non_self_row_count': non_self_row_count,
            'source_note_sha256': hash_file(note_path),
        },
        'verification': {
            'header_match': True,
            'rounding_applied': True,
            'range_checks_passed': True,
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(packet, indent=2) + '\n', encoding='utf-8')

    print(f'wrote_packet={out_path}')
    print(f'next_required_skill={NEXT_REQUIRED_SKILL}')
    print(f'binding_surface_kind={BINDING_SURFACE_KIND}')


if __name__ == '__main__':
    main()
