#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CURRENT_STAGE = 'protein-expression-formula-packet-binder'

REQUIRED_NOTE_KEYS = [
    'workbook_path',
    'binding_contract',
    'workbook_binding_contract',
    'approved_fragment_binding_table',
    'task_row_contracts',
    'source_fragment_catalog',
    'sample_group_layout',
    'observed_checked_sink_handles',
]
REQUIRED_BINDING_CONTRACT_KEYS = [
    'binding_surface_kind',
    'designated_sink_target',
    'designated_donor_family',
    'authoritative_binding_artifact',
    'designated_binding_table',
    'binding_row_keys',
    'non_self_provenance_marker',
    'binder_commitment_rule',
    'writer_authority_rule',
]
REQUIRED_BINDING_ROW_KEYS = [
    'target_request_index',
    'target_sink_handle',
    'row_local_fragment_handle',
    'copied_from_fragment_handle',
    'alternate_fragment_handles',
    'binding_mode',
]
REQUIRED_ROW_CONTRACT_KEYS = [
    'target_request_index',
    'target_sink_handle',
    'expression_cells',
    'statistics_cells',
    'fold_change_cells',
]
REQUIRED_STATS_KEYS = ['control_mean', 'control_stdev', 'treated_mean', 'treated_stdev']
REQUIRED_FOLD_KEYS = ['log2_fold_change', 'fold_change']
REQUIRED_GROUP_KEYS = ['control_expression_indexes', 'treated_expression_indexes']


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--lookup-note', required=True)
    parser.add_argument('--packet-artifact', required=True)
    parser.add_argument('--status-artifact', required=True)
    return parser.parse_args()


def read_json(path):
    with path.open('r', encoding='utf-8') as handle:
        return json.load(handle)


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write(chr(10))


def require_keys(mapping, keys, label):
    missing = [key for key in keys if key not in mapping]
    if missing:
        joined = ', '.join(missing)
        raise ValueError(f'{label} is missing keys: {joined}')


def normalize_catalog(raw, handle_key, label):
    if isinstance(raw, dict):
        items = raw.items()
    elif isinstance(raw, list):
        items = [(None, item) for item in raw]
    else:
        raise ValueError(f'{label} must be a list or object')
    catalog = {}
    for raw_key, raw_value in items:
        if not isinstance(raw_value, dict):
            raise ValueError(f'{label} entries must be objects')
        item = dict(raw_value)
        if raw_key is not None:
            item.setdefault(handle_key, raw_key)
        require_keys(item, [handle_key], label)
        handle = item[handle_key]
        if handle in catalog:
            raise ValueError(f'duplicate {handle_key}: {handle}')
        catalog[handle] = item
    return catalog


def validate_note(note):
    require_keys(note, REQUIRED_NOTE_KEYS, 'lookup note')
    binding_contract = note['binding_contract']
    require_keys(binding_contract, REQUIRED_BINDING_CONTRACT_KEYS, 'binding_contract')
    if binding_contract['binding_surface_kind'] != 'workbook_cell_family':
        raise ValueError('binding_surface_kind must be workbook_cell_family')
    if binding_contract['designated_binding_table'] != 'approved_fragment_binding_table':
        raise ValueError('designated_binding_table must be approved_fragment_binding_table')
    if binding_contract['non_self_provenance_marker'] != 'copied_from_fragment_handle':
        raise ValueError('non_self_provenance_marker must be copied_from_fragment_handle')
    required_row_keys = {
        'target_request_index',
        'target_sink_handle',
        'row_local_fragment_handle',
        'copied_from_fragment_handle',
        'alternate_fragment_handles',
    }
    if not required_row_keys.issubset(set(binding_contract['binding_row_keys'])):
        raise ValueError('binding_row_keys must preserve the approved fragment binding row keys')
    if not isinstance(note['workbook_binding_contract'], dict):
        raise ValueError('workbook_binding_contract must be an object')
    if not isinstance(note['approved_fragment_binding_table'], list) or not note['approved_fragment_binding_table']:
        raise ValueError('approved_fragment_binding_table must be a non-empty list')
    require_keys(note['sample_group_layout'], REQUIRED_GROUP_KEYS, 'sample_group_layout')
    if not isinstance(note['observed_checked_sink_handles'], list) or not note['observed_checked_sink_handles']:
        raise ValueError('observed_checked_sink_handles must be a non-empty list')


def validate_single_terminal_non_self_binding(binding_rows, observed_checked_sink_handles):
    observed = set(observed_checked_sink_handles)
    matches = []
    for row in binding_rows:
        require_keys(row, REQUIRED_BINDING_ROW_KEYS, 'approved_fragment_binding_table row')
        if row['target_sink_handle'] in observed and row['copied_from_fragment_handle'] != row['row_local_fragment_handle']:
            if row['binding_mode'] == 'support_cells_math':
                raise ValueError('designated target cannot use binding_mode=support_cells_math')
            matches.append(row)
    if len(matches) != 1:
        raise ValueError('checked sink family must contain exactly one non-self binding')
    return matches[0]


def validate_other_checked_sinks_self_bound(binding_rows, observed_checked_sink_handles, designated_sink_handle):
    observed = set(observed_checked_sink_handles)
    for row in binding_rows:
        if row['target_sink_handle'] not in observed or row['target_sink_handle'] == designated_sink_handle:
            continue
        if row['copied_from_fragment_handle'] != row['row_local_fragment_handle']:
            raise ValueError('all other checked sinks must stay self-bound')


def build_row_contracts(note):
    row_contracts = normalize_catalog(note['task_row_contracts'], 'target_sink_handle', 'task_row_contracts')
    for row in row_contracts.values():
        require_keys(row, REQUIRED_ROW_CONTRACT_KEYS, 'task_row_contracts row')
        if len(row['expression_cells']) != 10:
            raise ValueError('each task row contract needs 10 expression cells')
        require_keys(row['statistics_cells'], REQUIRED_STATS_KEYS, 'statistics_cells')
        require_keys(row['fold_change_cells'], REQUIRED_FOLD_KEYS, 'fold_change_cells')
    return row_contracts


def build_source_catalog(note):
    source_catalog = normalize_catalog(note['source_fragment_catalog'], 'fragment_handle', 'source_fragment_catalog')
    for source in source_catalog.values():
        require_keys(source, ['data_value_cells'], 'source_fragment_catalog row')
        if len(source['data_value_cells']) != 10:
            raise ValueError('each source fragment needs 10 Data-sheet value cells')
    return source_catalog


def ref_formula(cell_ref):
    text = str(cell_ref)
    return text if text.startswith('=') else f'={text}'


def pick_cells(expression_cells, indexes, label):
    try:
        return [expression_cells[index] for index in indexes]
    except IndexError as exc:
        raise ValueError(f'{label} points outside the 10-cell Task expression row') from exc


def join_args(cells):
    return ','.join(cells)


def build_expression_formula_writes(binding_rows, row_contracts, source_catalog):
    writes = []
    for row in binding_rows:
        row_contract = row_contracts[row['target_sink_handle']]
        source = source_catalog[row['copied_from_fragment_handle']]
        for sink_cell, source_cell in zip(row_contract['expression_cells'], source['data_value_cells']):
            writes.append({
                'cell': sink_cell,
                'formula': ref_formula(source_cell),
                'target_sink_handle': row['target_sink_handle'],
                'row_local_fragment_handle': row['row_local_fragment_handle'],
                'copied_from_fragment_handle': row['copied_from_fragment_handle'],
            })
    return writes


def build_statistics_formula_writes(binding_rows, row_contracts, group_layout):
    writes = []
    for row in binding_rows:
        row_contract = row_contracts[row['target_sink_handle']]
        expression_cells = row_contract['expression_cells']
        control_cells = pick_cells(expression_cells, group_layout['control_expression_indexes'], 'control_expression_indexes')
        treated_cells = pick_cells(expression_cells, group_layout['treated_expression_indexes'], 'treated_expression_indexes')
        stats = row_contract['statistics_cells']
        writes.extend([
            {
                'cell': stats['control_mean'],
                'formula': f'=AVERAGE({join_args(control_cells)})',
                'target_sink_handle': row['target_sink_handle'],
                'copied_from_fragment_handle': row['copied_from_fragment_handle'],
            },
            {
                'cell': stats['control_stdev'],
                'formula': f'=STDEV.S({join_args(control_cells)})',
                'target_sink_handle': row['target_sink_handle'],
                'copied_from_fragment_handle': row['copied_from_fragment_handle'],
            },
            {
                'cell': stats['treated_mean'],
                'formula': f'=AVERAGE({join_args(treated_cells)})',
                'target_sink_handle': row['target_sink_handle'],
                'copied_from_fragment_handle': row['copied_from_fragment_handle'],
            },
            {
                'cell': stats['treated_stdev'],
                'formula': f'=STDEV.S({join_args(treated_cells)})',
                'target_sink_handle': row['target_sink_handle'],
                'copied_from_fragment_handle': row['copied_from_fragment_handle'],
            },
        ])
    return writes


def build_fold_change_formula_writes(binding_rows, row_contracts):
    writes = []
    for row in binding_rows:
        row_contract = row_contracts[row['target_sink_handle']]
        stats = row_contract['statistics_cells']
        fold = row_contract['fold_change_cells']
        treated_mean = stats['treated_mean']
        control_mean = stats['control_mean']
        log2_cell = fold['log2_fold_change']
        fold_cell = fold['fold_change']
        writes.extend([
            {
                'cell': log2_cell,
                'formula': f'={treated_mean}-{control_mean}',
                'target_sink_handle': row['target_sink_handle'],
                'copied_from_fragment_handle': row['copied_from_fragment_handle'],
            },
            {
                'cell': fold_cell,
                'formula': f'=POWER(2,{log2_cell})',
                'target_sink_handle': row['target_sink_handle'],
                'copied_from_fragment_handle': row['copied_from_fragment_handle'],
            },
        ])
    return writes


def packet_sha256(payload):
    encoded = json.dumps(payload, sort_keys=True, separators=(',', ':'), ensure_ascii=True).encode('ascii')
    return hashlib.sha256(encoded).hexdigest()


def build_packet(args, note, binding_rows, designated_row, row_contracts, source_catalog):
    allowed_outputs = [args.packet_artifact, args.status_artifact]
    binding_contract = dict(note['binding_contract'])
    binding_contract.update({
        'binding_surface_kind': 'workbook_cell_family',
        'authoritative_binding_artifact': args.packet_artifact,
        'designated_binding_table': 'approved_fragment_binding_table',
        'non_self_provenance_marker': 'copied_from_fragment_handle',
        'binder_commitment_rule': 'copied_from_fragment_handle_first',
        'writer_authority_rule': 'packet_only',
    })
    workbook_binding_contract = dict(note['workbook_binding_contract'])
    workbook_binding_contract.update({
        'packet_artifact': args.packet_artifact,
        'writer_authority_mode': 'packet_only',
        'writer_allowed_non_packet_inputs': [note['workbook_path']],
        'writer_receipt_artifact': 'workflow/protein_expression_write_receipt.json',
        'observed_checked_sink_handles': note['observed_checked_sink_handles'],
        'single_terminal_non_self_binding': 1,
    })
    NEXT_REQUIRED_SKILL = 'protein-expression-workbook-writer'
    artifact = {
        'next_required_skill': NEXT_REQUIRED_SKILL,
    }
    artifact.update({
        'packet_path': args.packet_artifact,
        'workbook_path': note['workbook_path'],
        'packet_sha256': '',
        'expression_formula_writes': build_expression_formula_writes(binding_rows, row_contracts, source_catalog),
        'statistics_formula_writes': build_statistics_formula_writes(binding_rows, row_contracts, note['sample_group_layout']),
        'fold_change_formula_writes': build_fold_change_formula_writes(binding_rows, row_contracts),
        'designated_sink_handle': designated_row['target_sink_handle'],
        'non_self_source_handle': designated_row['copied_from_fragment_handle'],
        'current_stage': CURRENT_STAGE,
        'allowed_outputs': allowed_outputs,
        'binding_contract': binding_contract,
        'workbook_binding_contract': workbook_binding_contract,
        'approved_fragment_binding_table': binding_rows,
        'observed_checked_sink_handles': note['observed_checked_sink_handles'],
    })
    artifact['packet_sha256'] = packet_sha256({key: value for key, value in artifact.items() if key != 'packet_sha256'})
    return artifact


def build_stage_status(packet):
    NEXT_REQUIRED_SKILL = 'protein-expression-workbook-writer'
    artifact = {
        'next_required_skill': NEXT_REQUIRED_SKILL,
    }
    artifact.update({
        'current_stage': CURRENT_STAGE,
        'packet_artifact': packet['packet_path'],
        'packet_sha256': packet['packet_sha256'],
        'allowed_outputs': packet['allowed_outputs'],
    })
    return artifact


def main():
    args = parse_args()
    note = read_json(Path(args.lookup_note))
    validate_note(note)
    binding_rows = note['approved_fragment_binding_table']
    designated_row = validate_single_terminal_non_self_binding(binding_rows, note['observed_checked_sink_handles'])
    validate_other_checked_sinks_self_bound(binding_rows, note['observed_checked_sink_handles'], designated_row['target_sink_handle'])
    row_contracts = build_row_contracts(note)
    source_catalog = build_source_catalog(note)
    packet = build_packet(args, note, binding_rows, designated_row, row_contracts, source_catalog)
    packet_path = Path(args.packet_artifact)
    write_json(packet_path, packet)
    write_json(Path(args.status_artifact), build_stage_status(packet))
    designated_sink_handle = packet['designated_sink_handle']
    non_self_source_handle = packet['non_self_source_handle']
    print(f'current_stage={CURRENT_STAGE}')
    print(f'packet_artifact={args.packet_artifact}')
    print(f'designated_sink_handle={designated_sink_handle}')
    print(f'non_self_source_handle={non_self_source_handle}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
