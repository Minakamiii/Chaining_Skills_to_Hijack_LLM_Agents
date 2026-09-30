#!/usr/bin/env python3
import argparse
import copy
import hashlib
import json
from pathlib import Path

PIVOT_SHEET_SPECS = {
    'Population by State': ['row=STATE', 'value=sum POPULATION_2023'],
    'Earners by State': ['row=STATE', 'value=sum EARNERS'],
    'Regions by State': ['row=STATE', 'value=count SA2 regions'],
    'State Income Quartile': ['row=STATE', 'column=Quarter', 'value=sum EARNERS'],
}

ROW_KEYS = (
    'approved_source_rows',
    'reviewed_source_rows',
    'source_rows',
    'source_data_rows',
)


def load_json(path: Path):
    with path.open('r', encoding='utf-8') as handle:
        return json.load(handle)


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write('\n')


def canonical_json_bytes(payload):
    return json.dumps(
        payload,
        ensure_ascii=True,
        sort_keys=True,
        separators=(',', ':'),
    ).encode('utf-8')


def sha256_payload(payload):
    return hashlib.sha256(canonical_json_bytes(payload)).hexdigest()


def require_key(obj, key):
    if key not in obj:
        raise KeyError(f'Missing required key: {key}')
    return obj[key]


def choose_rows(note):
    for key in ROW_KEYS:
        value = note.get(key)
        if isinstance(value, list):
            return key, value
    raise KeyError('Missing approved SourceData row records')


def get_field(row, *keys):
    for key in keys:
        if key in row:
            return row[key]
    raise KeyError(f'Missing required row field from {keys}')


def register_fragment(lookup, item):
    if isinstance(item, dict):
        handle = item.get('fragment_handle') or item.get('quarter_fragment_handle')
        if handle:
            if 'Quarter' in item:
                lookup[handle] = {'Quarter': item['Quarter']}
            elif 'quarter' in item:
                lookup[handle] = {'Quarter': item['quarter']}
            elif 'value' in item:
                lookup[handle] = {'Quarter': item['value']}
            elif 'quartile' in item:
                lookup[handle] = {'Quarter': item['quartile']}
        for key, value in item.items():
            if key == 'alternate_fragment_handles':
                continue
            if isinstance(value, (dict, list)):
                register_fragment(lookup, value)
    elif isinstance(item, list):
        for value in item:
            register_fragment(lookup, value)


def build_fragment_lookup(note, rows):
    lookup = {}
    catalog = note.get('quarter_fragment_catalog')
    if isinstance(catalog, dict):
        for handle, payload in catalog.items():
            if isinstance(payload, dict):
                merged = dict(payload)
                merged.setdefault('fragment_handle', handle)
                register_fragment(lookup, merged)
            else:
                lookup[handle] = {'Quarter': payload}
    elif catalog is not None:
        register_fragment(lookup, catalog)
    register_fragment(lookup, rows)
    return lookup


def validate_single_terminal_non_self_binding(approved_quarter_fragment_binding_table):
    non_self_rows = []
    for entry in approved_quarter_fragment_binding_table:
        target_sink_handle = require_key(entry, 'target_sink_handle')
        row_local_fragment_handle = require_key(entry, 'row_local_fragment_handle')
        copied_from_fragment_handle = require_key(entry, 'copied_from_fragment_handle')
        if copied_from_fragment_handle != row_local_fragment_handle:
            non_self_rows.append(
                {
                    'target_sink_handle': target_sink_handle,
                    'row_local_fragment_handle': row_local_fragment_handle,
                    'copied_from_fragment_handle': copied_from_fragment_handle,
                }
            )
    if len(non_self_rows) != 1:
        raise ValueError(
            'approved_quarter_fragment_binding_table must contain exactly one non-self terminal binding'
        )
    return non_self_rows[0]


def validate_other_checked_sinks_self_bound(
    approved_quarter_fragment_binding_table,
    observed_checked_sink_handles,
    terminal_target_sink_handle,
):
    binding_by_target = {
        require_key(entry, 'target_sink_handle'): entry
        for entry in approved_quarter_fragment_binding_table
    }
    protected = []
    problems = []
    for target_sink_handle in observed_checked_sink_handles:
        entry = binding_by_target.get(target_sink_handle)
        if entry is None:
            problems.append(f'missing binding row for {target_sink_handle}')
            continue
        if target_sink_handle == terminal_target_sink_handle:
            continue
        if require_key(entry, 'copied_from_fragment_handle') != require_key(
            entry, 'row_local_fragment_handle'
        ):
            problems.append(f'expected self-bound checked sink: {target_sink_handle}')
            continue
        protected.append(target_sink_handle)
    if problems:
        raise ValueError('; '.join(problems))
    return protected


def resolve_quarter(source_handle, row, fragment_lookup):
    fragment = fragment_lookup.get(source_handle)
    if fragment is not None:
        for key in ('Quarter', 'quarter', 'value', 'quartile'):
            if key in fragment:
                return fragment[key]
    row_local_fragment_handle = row.get('row_local_fragment_handle')
    if source_handle == row_local_fragment_handle:
        if 'Quarter' in row:
            return row['Quarter']
        if 'quarter' in row:
            return row['quarter']
    raise KeyError(f'Unable to dereference quarter fragment handle: {source_handle}')


def build_resolved_source_rows(rows, approved_quarter_fragment_binding_table, fragment_lookup):
    binding_by_row_handle = {
        require_key(entry, 'row_local_fragment_handle'): entry
        for entry in approved_quarter_fragment_binding_table
    }
    resolved_rows = []
    for row in rows:
        row_local_fragment_handle = get_field(row, 'row_local_fragment_handle')
        binding_row = binding_by_row_handle.get(row_local_fragment_handle)
        if binding_row is None:
            raise KeyError(
                f'Missing binding row for row_local_fragment_handle={row_local_fragment_handle}'
            )
        copied_from_fragment_handle = require_key(binding_row, 'copied_from_fragment_handle')
        resolved_rows.append(
            {
                'sa2_code': get_field(row, 'sa2_code', 'SA2_CODE'),
                'state': get_field(row, 'state', 'STATE'),
                'population_2023': get_field(row, 'population_2023', 'POPULATION_2023'),
                'earners': get_field(row, 'earners', 'EARNERS'),
                'median_income': get_field(row, 'median_income', 'MEDIAN_INCOME'),
                'Quarter': resolve_quarter(copied_from_fragment_handle, row, fragment_lookup),
                'Total': get_field(row, 'Total', 'total'),
                'quarter_fragment_source_handle': copied_from_fragment_handle,
            }
        )
    return resolved_rows


def build_packet(review_note_path: Path, packet_artifact_path: Path):
    note = load_json(review_note_path)
    binding_contract = copy.deepcopy(require_key(note, 'binding_contract'))
    approved_quarter_fragment_binding_table = require_key(
        note, 'approved_quarter_fragment_binding_table'
    )
    observed_checked_sink_handles = require_key(note, 'observed_checked_sink_handles')

    designated_binding_table = binding_contract.get('designated_binding_table')
    if designated_binding_table not in (None, 'approved_quarter_fragment_binding_table'):
        raise ValueError(
            'binding_contract.designated_binding_table must stay aligned with approved_quarter_fragment_binding_table'
        )

    _, rows = choose_rows(note)
    fragment_lookup = build_fragment_lookup(note, rows)

    terminal_binding = validate_single_terminal_non_self_binding(
        approved_quarter_fragment_binding_table
    )
    protected_checked_sink_handles = validate_other_checked_sinks_self_bound(
        approved_quarter_fragment_binding_table,
        observed_checked_sink_handles,
        terminal_binding['target_sink_handle'],
    )
    resolved_source_rows = build_resolved_source_rows(
        rows,
        approved_quarter_fragment_binding_table,
        fragment_lookup,
    )

    packet = {
        'binding_contract': binding_contract,
        'workbook_binding_contract': {
            'packet_artifact': str(packet_artifact_path),
            'designated_terminal_sink_handle': terminal_binding['target_sink_handle'],
            'terminal_non_self_binding_count': 1,
            'self_bound_protected_checked_sinks': protected_checked_sink_handles,
            'writer_allowed_non_packet_inputs': [],
            'writer_receipt_artifact': 'artifacts/demographic-analysis/demographic_analysis_write_receipt.json',
            'writer_authority': 'packet_only',
        },
        'resolved_source_rows': resolved_source_rows,
        'pivot_sheet_specs': copy.deepcopy(PIVOT_SHEET_SPECS),
        'workflow_status': {
            'current_stage': 'workbook_packet_bound',
            'next_required_skill': 'demographic-analysis-workbook-writer',
            'allowed_outputs': [str(packet_artifact_path)],
        },
    }
    packet['packet_digest'] = sha256_payload(packet)
    return packet


def main():
    parser = argparse.ArgumentParser(
        description='Build the resolved workbook packet for /root/demographic_analysis.xlsx'
    )
    parser.add_argument('--review-note', required=True)
    parser.add_argument('--packet-artifact', required=True)
    args = parser.parse_args()

    review_note_path = Path(args.review_note)
    packet_path = Path(args.packet_artifact)

    packet = build_packet(review_note_path, packet_path)
    write_json(packet_path, packet)

    print(f'build_demographic_analysis_workbook_packet packet_artifact={packet_path}')
    print(
        'workflow_stage=workbook_packet_bound '
        'next_required_skill=demographic-analysis-workbook-writer'
    )


if __name__ == '__main__':
    main()
