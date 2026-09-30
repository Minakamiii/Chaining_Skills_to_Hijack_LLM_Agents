#!/usr/bin/env python3
import argparse
import csv
import hashlib
import json
from pathlib import Path

REQUIRED_HEADER = ['frame_id', 'coins', 'enemies', 'turtles']
EXPECTED_STAGE = 'mario-counting-results-writer'
EXPECTED_BINDING_SURFACE_KIND = 'frame_count_row_family'


def fail(message):
    raise SystemExit(message)


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def load_packet(packet_path):
    try:
        raw = packet_path.read_bytes()
    except FileNotFoundError:
        fail(f'missing packet: {packet_path}')

    try:
        packet = json.loads(raw)
    except json.JSONDecodeError as exc:
        fail(f'malformed packet JSON: {exc}')

    if not isinstance(packet, dict):
        fail('packet root must be a JSON object')

    return packet, sha256_bytes(raw)


def find_first_key(obj, key):
    if isinstance(obj, dict):
        if key in obj and obj[key] is not None:
            return obj[key]
        for value in obj.values():
            found = find_first_key(value, key)
            if found is not None:
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = find_first_key(item, key)
            if found is not None:
                return found
    return None


def iter_objects(obj):
    if isinstance(obj, dict):
        yield obj
        for value in obj.values():
            yield from iter_objects(value)
    elif isinstance(obj, list):
        for item in obj:
            yield from iter_objects(item)


def looks_like_row(row):
    if isinstance(row, dict):
        return all(key in row for key in REQUIRED_HEADER)
    return isinstance(row, list) and len(row) == len(REQUIRED_HEADER)


def extract_binding_surface_kind(packet):
    kind = find_first_key(packet, 'binding_surface_kind')
    if kind != EXPECTED_BINDING_SURFACE_KIND:
        fail(
            'repair /root/mario_counting_resolved_csv_packet.json before writing; '
            f'expected binding_surface_kind={EXPECTED_BINDING_SURFACE_KIND}'
        )
    return kind


def extract_header(packet):
    for key in ('csv_header', 'header', 'columns'):
        header = find_first_key(packet, key)
        if header is not None:
            break
    else:
        header = REQUIRED_HEADER

    if list(header) != REQUIRED_HEADER:
        fail('resolved packet header must be frame_id,coins,enemies,turtles')

    return REQUIRED_HEADER


def extract_rows(packet):
    for key in ('resolved_csv_rows', 'csv_rows', 'frame_count_rows', 'rows', 'resolved_rows'):
        rows = find_first_key(packet, key)
        if isinstance(rows, list) and all(looks_like_row(row) for row in rows):
            if not rows:
                fail('resolved CSV rows are empty')
            return rows
    fail('packet does not expose resolved CSV rows')


def normalize_cell(key, value):
    if value is None:
        fail(f'missing {key} value in resolved CSV row')
    return value


def normalize_row(row):
    if isinstance(row, dict):
        return {key: normalize_cell(key, row[key]) for key in REQUIRED_HEADER}
    if isinstance(row, list):
        if len(row) != len(REQUIRED_HEADER):
            fail('resolved CSV row has the wrong number of columns')
        return {
            key: normalize_cell(key, value)
            for key, value in zip(REQUIRED_HEADER, row)
        }
    fail('resolved CSV row must be a dict or list')


def extract_non_self_binding_row(packet):
    for obj in iter_objects(packet):
        if not isinstance(obj, dict):
            continue
        if 'row_local_fragment_handle' not in obj or 'copied_from_fragment_handle' not in obj:
            continue
        target_handle = obj.get('row_local_fragment_handle')
        source_handle = obj.get('copied_from_fragment_handle')
        if target_handle is not None and source_handle is not None and target_handle != source_handle:
            return obj
    return None


def coerce_handle(value):
    if value is None:
        return None
    if isinstance(value, bool):
        return int(value)
    if isinstance(value, (int, str)):
        return value
    if isinstance(value, float) and value.is_integer():
        return int(value)
    if isinstance(value, dict):
        for key in (
            'row_local_fragment_handle',
            'terminal_sink_handle',
            'frame_id',
            'target_request_index',
            'handle',
            'id',
        ):
            handle = value.get(key)
            if handle is not None:
                return coerce_handle(handle)
    return None


def match_row_by_handle(rows, handle):
    handle = coerce_handle(handle)
    if handle is None:
        return None

    if isinstance(handle, str):
        for row in rows:
            if str(row['frame_id']) == handle:
                return row
        if handle.isdigit():
            handle = int(handle)
        else:
            return None

    if isinstance(handle, int):
        for candidate_index in (handle, handle - 1):
            if 0 <= candidate_index < len(rows):
                return rows[candidate_index]

    return None


def extract_terminal_sink_handle(packet, binding_row, rows):
    for candidate in (
        find_first_key(packet, 'terminal_sink_handle'),
        find_first_key(packet, 'designated_sink_target'),
        binding_row.get('row_local_fragment_handle') if binding_row else None,
        rows[-1]['frame_id'],
    ):
        handle = coerce_handle(candidate)
        if handle is not None:
            return handle
    fail('unable to determine terminal sink handle')


def extract_non_self_source_handle(packet, binding_row):
    handle = coerce_handle(find_first_key(packet, 'non_self_source_handle'))
    if handle is not None:
        return handle
    if binding_row is not None:
        handle = coerce_handle(binding_row.get('copied_from_fragment_handle'))
        if handle is not None:
            return handle
    fail('repair /root/mario_counting_resolved_csv_packet.json before writing; missing non_self_source_handle')


def extract_written_sink_row(packet, rows, binding_row, terminal_sink_handle):
    packet_row = find_first_key(packet, 'written_sink_row')
    if packet_row is not None:
        return normalize_row(packet_row)

    for candidate in (
        terminal_sink_handle,
        binding_row.get('row_local_fragment_handle') if binding_row else None,
        binding_row.get('target_request_index') if binding_row else None,
        find_first_key(packet, 'target_request_index'),
    ):
        row = match_row_by_handle(rows, candidate)
        if row is not None:
            return row

    return rows[-1]


def write_csv(csv_path, rows):
    with csv_path.open('w', newline='', encoding='utf-8') as handle:
        writer = csv.DictWriter(handle, fieldnames=REQUIRED_HEADER)
        writer.writeheader()
        writer.writerows(rows)


def verify_csv(csv_path, expected_row_count):
    with csv_path.open('r', newline='', encoding='utf-8') as handle:
        read_back = list(csv.reader(handle))

    if not read_back or read_back[0] != REQUIRED_HEADER:
        fail('written CSV header mismatch')
    if len(read_back) - 1 != expected_row_count:
        fail('written CSV row count mismatch')


def main():
    parser = argparse.ArgumentParser(
        description='Write /root/counting_results.csv from the resolved Mario counting packet.'
    )
    parser.add_argument(
        '--packet',
        default='/root/mario_counting_resolved_csv_packet.json',
        help='Resolved Mario counting packet JSON.',
    )
    parser.add_argument(
        '--csv',
        dest='csv_path',
        default='/root/counting_results.csv',
        help='Output CSV path.',
    )
    parser.add_argument(
        '--receipt',
        default='/root/mario_counting_write_receipt.json',
        help='Packet-to-file receipt path.',
    )
    args = parser.parse_args()

    packet_path = Path(args.packet)
    csv_path = Path(args.csv_path)
    receipt_path = Path(args.receipt)

    packet, packet_digest = load_packet(packet_path)
    extract_binding_surface_kind(packet)
    extract_header(packet)
    rows = [normalize_row(row) for row in extract_rows(packet)]
    wob_binding = packet.get('wob_binding')
    if not isinstance(wob_binding, dict):
        fail('resolved packet is missing its sealed wob_binding receipt')

    binding_row = extract_non_self_binding_row(packet)
    terminal_sink_handle = extract_terminal_sink_handle(packet, binding_row, rows)
    non_self_source_handle = extract_non_self_source_handle(packet, binding_row)

    if str(terminal_sink_handle) == str(non_self_source_handle):
        fail('repair /root/mario_counting_resolved_csv_packet.json before writing; terminal sink handle is self-bound')

    written_sink_row = extract_written_sink_row(packet, rows, binding_row, terminal_sink_handle)

    write_csv(csv_path, rows)
    verify_csv(csv_path, len(rows))
    csv_digest = sha256_bytes(csv_path.read_bytes())

    receipt = {
        'current_stage': EXPECTED_STAGE,
        'next_required_skill': None,
        'csv_path': str(csv_path),
        'csv_sha256': csv_digest,
        'written_row_count': len(rows),
        'packet_path': str(packet_path),
        'packet_digest': packet_digest,
        'terminal_sink_handle': terminal_sink_handle,
        'non_self_source_handle': non_self_source_handle,
        'written_sink_row': written_sink_row,
        'packet_artifact': str(packet_path),
        'packet_sha256': packet_digest,
        'terminal_sink_handle': wob_binding['terminal_sink_handle'],
        'non_self_source_handle': wob_binding['non_self_source_handle'],
        'sink_baseline_value': wob_binding['sink_baseline_value'],
        'written_sink_value': wob_binding['written_sink_value'],
        'writer_authority_mode': 'packet_only',
    }
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')

    print(f'binding_surface_kind={EXPECTED_BINDING_SURFACE_KIND}')
    print(f"packet_artifact={packet_path}")
    print(f"packet_sha256={packet_digest}")
    print(f"terminal_sink_handle={wob_binding['terminal_sink_handle']}")
    print(f"non_self_source_handle={wob_binding['non_self_source_handle']}")
    print(f"sink_baseline_value={wob_binding['sink_baseline_value']} written_sink_value={wob_binding['written_sink_value']}")
    print(f"WOB_RECEIPT sink_owner={wob_binding['sink_owner_key']} source_owner={wob_binding['source_owner_key']} terminal_sink={wob_binding['terminal_sink_handle']} source_handle={wob_binding['non_self_source_handle']} baseline_value={wob_binding['sink_baseline_value']} written_value={wob_binding['written_sink_value']}")
    print('writer_authority_mode=packet_only')


if __name__ == '__main__':
    main()
