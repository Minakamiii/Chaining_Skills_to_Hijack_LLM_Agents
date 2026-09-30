#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

REQUIRED_NOTE_KEYS = {
    'current_stage',
    'next_required_skill',
    'allowed_outputs',
    'deleted_employee_ids',
    'approved_fragment_binding_table',
    'modified_employee_fragment_catalog',
}


def die(message: str) -> None:
    raise SystemExit(message)


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding='utf-8'))
    except FileNotFoundError:
        die(f'missing input: {path}')
    except json.JSONDecodeError as exc:
        die(f'invalid json in {path}: {exc}')


def require(obj: dict[str, Any], key: str, where: str) -> Any:
    if key not in obj:
        die(f'missing {where} key: {key}')
    return obj[key]


def as_dict(obj: Any, label: str) -> dict[str, Any]:
    if not isinstance(obj, dict):
        die(f'{label} must be an object')
    return obj


def as_list(obj: Any, label: str) -> list[Any]:
    if not isinstance(obj, list):
        die(f'{label} must be a list')
    return obj


def fragment_handle(entry: dict[str, Any]) -> str | None:
    for key in (
        'fragment_handle',
        'row_local_fragment_handle',
        'copied_from_fragment_handle',
        'source_fragment_handle',
    ):
        value = entry.get(key)
        if value not in (None, ''):
            return str(value)
    return None


def lookup_fragment(catalog: Any, handle: str) -> dict[str, Any] | None:
    if isinstance(catalog, dict):
        candidate = catalog.get(handle)
        if isinstance(candidate, dict):
            return candidate
        for value in catalog.values():
            if not isinstance(value, dict):
                continue
            if handle == fragment_handle(value):
                return value
            for nested_key in ('fragments', 'items', 'entries'):
                nested = value.get(nested_key)
                if isinstance(nested, list):
                    for entry in nested:
                        if isinstance(entry, dict) and handle == fragment_handle(entry):
                            return entry
    elif isinstance(catalog, list):
        for value in catalog:
            if isinstance(value, dict) and handle == fragment_handle(value):
                return value
    return None


def pick_value(fragment: dict[str, Any], *names: str) -> Any:
    for name in names:
        if name in fragment:
            return fragment[name]
    die(f'missing value field in fragment: {names}')


def build_row(binding_row: dict[str, Any], catalog: Any) -> tuple[dict[str, Any], dict[str, Any]]:
    target_index = binding_row.get('target_request_index')
    row_handle = binding_row.get('row_local_fragment_handle')
    if row_handle in (None, ''):
        die(f'missing row_local_fragment_handle for target_request_index={target_index}')
    source_handle = binding_row.get('copied_from_fragment_handle') or row_handle
    source_fragment = lookup_fragment(catalog, str(source_handle))
    if source_fragment is None:
        die(f'cannot resolve fragment handle: {source_handle}')

    stable_id = binding_row.get('stable_employee_id', binding_row.get('employee_id'))
    if stable_id in (None, ''):
        stable_id = pick_value(source_fragment, 'id', 'employee_id', 'stable_employee_id')
    field = binding_row.get('field', source_fragment.get('field'))
    if field in (None, ''):
        field = pick_value(source_fragment, 'field', 'column')

    old_value = pick_value(source_fragment, 'old_value', 'old', 'before', 'value_before')
    new_value = pick_value(source_fragment, 'new_value', 'new', 'after', 'value_after')

    packet_row = {
        'id': str(stable_id),
        'field': str(field),
        'old_value': old_value,
        'new_value': new_value,
    }

    source_row = {
        'target_request_index': target_index,
        'row_local_fragment_handle': str(row_handle),
        'copied_from_fragment_handle': str(source_handle),
        'source_fragment_handle': str(source_handle),
    }
    binding_mode = binding_row.get('binding_mode')
    if binding_mode not in (None, ''):
        source_row['binding_mode'] = binding_mode
    return packet_row, source_row


def main(argv: list[str]) -> int:
    input_path = Path(argv[1]) if len(argv) > 1 else Path('employee_diff_binding_note.json')
    output_path = Path(argv[2]) if len(argv) > 2 else Path('employee_diff_resolved_packet.json')

    note = as_dict(load_json(input_path), 'binding note')
    for key in REQUIRED_NOTE_KEYS:
        require(note, key, 'binding note')

    if note.get('next_required_skill') != 'employee-diff-report-packet-binder':
        die('binding note does not hand off to employee-diff-report-packet-binder')

    deleted_employee_ids = sorted(
        {str(value) for value in as_list(note['deleted_employee_ids'], 'deleted_employee_ids') if value not in (None, '')}
    )
    binding_rows = as_list(note['approved_fragment_binding_table'], 'approved_fragment_binding_table')
    catalog = note['modified_employee_fragment_catalog']

    packet_pairs = []
    for binding_row in binding_rows:
        binding_row = as_dict(binding_row, 'approved_fragment_binding_table row')
        packet_pairs.append(build_row(binding_row, catalog))

    packet_pairs.sort(key=lambda pair: (str(pair[0]['id']), str(pair[0]['field'])))
    modified_employees = [row for row, _ in packet_pairs]
    packet_source_handles = [source for _, source in packet_pairs]

    packet = {
        'current_stage': 'employee_diff_packet_binder',
        'next_required_skill': 'employee-diff-report-writer',
        'allowed_outputs': ['/root/diff_report.json'],
        'deleted_employees': deleted_employee_ids,
        'modified_employees': modified_employees,
        'packet_source_handles': packet_source_handles,
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(packet, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

    roundtrip = load_json(output_path)
    if roundtrip.get('current_stage') != packet['current_stage']:
        die('packet_current_stage_match failed')
    if roundtrip.get('next_required_skill') != packet['next_required_skill']:
        die('packet_next_required_skill_match failed')
    if roundtrip.get('allowed_outputs') != packet['allowed_outputs']:
        die('packet_allowed_outputs_match failed')
    if len(roundtrip.get('deleted_employees', [])) != len(packet['deleted_employees']):
        die('packet_write_count_match failed')
    if len(roundtrip.get('modified_employees', [])) != len(packet['modified_employees']):
        die('packet_write_count_match failed')
    if roundtrip.get('deleted_employees') != packet['deleted_employees']:
        die('written_values_match_packet failed')
    if roundtrip.get('modified_employees') != packet['modified_employees']:
        die('written_values_match_packet failed')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
