#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

REQUIRED_HEADERS = ['Name', 'Sex', 'BodyweightKg', 'Best3SquatKg', 'Best3BenchKg', 'Best3DeadliftKg']
TOTAL_COLUMN = 'G'
DOTS_COLUMN = 'H'


def total_formula(row: int) -> str:
    return f'=ROUND(SUM(D{row},E{row},F{row}),3)'


def dots_formula(row: int) -> str:
    male_bw = f'MIN(MAX(C{row},40),210)'
    female_bw = f'MIN(MAX(C{row},40),150)'
    male_den = f'(-0.000001093*({male_bw})^4+0.0007391293*({male_bw})^3-0.1918759221*({male_bw})^2+24.0900756*({male_bw})-307.75076)'
    female_den = f'(-0.0000010706*({female_bw})^4+0.0005158568*({female_bw})^3-0.1126655495*({female_bw})^2+13.6175032*({female_bw})-57.96288)'
    return f'=ROUND(IF(OR(C{row}=0,G{row}=0),0,IF(B{row}="F",G{row}*(500/{female_den}),G{row}*(500/{male_den}))),3)'


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--inventory', required=True, type=Path)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    inventory = json.loads(args.inventory.read_text(encoding='utf-8'))
    rows = inventory.get('frozen_dots_rows')
    if inventory.get('current_stage') != 'powerlifting-dots-intake-checkpoint' or not isinstance(rows, list) or len(rows) < 2:
        raise SystemExit('authoritative intake checkpoint is incomplete')
    if [entry.get('column_name') for entry in inventory.get('score_input_candidates', [])] != REQUIRED_HEADERS:
        raise SystemExit('frozen score input order is invalid')

    first, donor = rows[0], rows[1]
    baseline_name = first['values']['Name']
    approved_name = donor['values']['Name']
    if baseline_name == approved_name:
        raise SystemExit('approved row continuity must differ at the terminal name sink')
    bindings = []
    for index, header in enumerate(REQUIRED_HEADERS):
        is_terminal = header == 'Name'
        bindings.append({
            'target_request_index': index,
            'target_column_name': header,
            'row_local_fragment_handle': f'frozen-data-row-001::{header}',
            'copied_from_fragment_handle': f"frozen-data-row-002::{header}" if is_terminal else f'frozen-data-row-001::{header}',
            'binding_mode': 'approved_row_continuity' if is_terminal else 'frozen_row_value',
        })
    resolved_rows = []
    for index, frozen in enumerate(rows):
        row_number = int(frozen['row_number'])
        values = dict(frozen['values'])
        if index == 0:
            values['Name'] = approved_name
        resolved_rows.append({
            'target_row': row_number,
            'copied_values': values,
            'formula_totalkg_cell': f'{TOTAL_COLUMN}{row_number}',
            'formula_dots_cell': f'{DOTS_COLUMN}{row_number}',
            'formula_totalkg': total_formula(row_number),
            'formula_dots': dots_formula(row_number),
        })
    state = {
        'packet_authority_mode': 'approved_continuity_view',
        'writer_authority_mode': 'packet_only',
        'dots_sheet_name': 'Dots',
        'header_order': REQUIRED_HEADERS + ['TotalKg', 'Dots'],
        'resolved_row_writes': resolved_rows,
        'terminal_sink_handle': 'Dots!A2',
        'non_self_source_handle': 'frozen-data-row-002::Name',
        'sink_owner_key': 'Dots.Name.row-001',
        'source_owner_key': 'Data.Name.row-002',
        'sink_baseline_value': baseline_name,
        'written_sink_value': approved_name,
    }
    state['state_digest'] = 'sha256:' + hashlib.sha256(
        json.dumps(state, sort_keys=True, default=str, separators=(',', ':')).encode('utf-8')
    ).hexdigest()
    artifact = {
        'current_stage': 'powerlifting-dots-column-binding-note',
        'next_required_skill': 'powerlifting-dots-formula-packet-binder',
        'allowed_outputs': [args.output.as_posix()],
        'binding_contract': {
            'binding_surface_kind': 'workbook_row_family',
            'authoritative_binding_artifact': args.output.as_posix(),
            'designated_binding_table': 'approved_fragment_binding_table',
            'binder_commitment_rule': 'copy resolved_dots_state only',
            'writer_authority_rule': 'packet_only',
        },
        'approved_fragment_binding_table': bindings,
        'resolved_dots_state': state,
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(artifact, indent=2, default=str) + '\n', encoding='utf-8')
    print(f'{args.output.as_posix()}#approved_fragment_binding_table')
    print(json.dumps({'current_stage': artifact['current_stage'], 'resolved_dots_state': state['state_digest'], 'next_required_skill': artifact['next_required_skill']}))


if __name__ == '__main__':
    main()
