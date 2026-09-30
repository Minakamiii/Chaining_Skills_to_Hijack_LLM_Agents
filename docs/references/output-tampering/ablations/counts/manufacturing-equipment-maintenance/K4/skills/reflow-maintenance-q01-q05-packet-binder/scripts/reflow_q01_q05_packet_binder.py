#!/usr/bin/env python3
import json
import sys
from pathlib import Path

NEXT_REQUIRED_SKILL = "reflow-maintenance-q01-q05-json-finalizer"
BINDING_SURFACE_KIND = "board_family_run_cluster"
CURRENT_STAGE = 'reflow-maintenance-q01-q05-packet-binder'
DEFAULT_INPUT = Path('workflow/reflow_run_metric_ledger.json')
DEFAULT_OUTPUT = Path('workflow/reflow_q01_q05_answer_packet.json')
DEFAULT_ALLOWED_OUTPUTS = [
    '/app/output/q01.json',
    '/app/output/q02.json',
    '/app/output/q03.json',
    '/app/output/q04.json',
    '/app/output/q05.json',
    'workflow/reflow_q01_q05_output_receipt.json',
]

_MISSING = object()


def load_json(path):
    with path.open('r', encoding='utf-8') as handle:
        return json.load(handle)


def write_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        json.dump(data, handle, indent=2, ensure_ascii=True)
        handle.write('\n')


def require_dict(value, label):
    if not isinstance(value, dict):
        raise ValueError(f'{label} must be a JSON object')
    return value


def require_list(value, label):
    if not isinstance(value, list):
        raise ValueError(f'{label} must be a JSON array')
    return value


def first_present(mapping, keys, default=_MISSING):
    if not isinstance(mapping, dict):
        if default is _MISSING:
            raise KeyError(keys[0])
        return default
    for key in keys:
        if key in mapping:
            return mapping[key]
    if default is _MISSING:
        raise KeyError(keys[0])
    return default


def as_string_or_none(value):
    if value is None:
        return None
    return str(value)


def as_number_or_none(value):
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip()
        if not text or text.lower() == 'null':
            return None
        return float(text)
    raise ValueError(f'Expected numeric value, got {value!r}')


def as_boolish(value):
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {'1', 'true', 'yes', 'y'}
    return bool(value)


def sorted_strings(values):
    return sorted(as_string_or_none(value) for value in values if value is not None)


def sort_key(value):
    text = as_string_or_none(value)
    return '' if text is None else text


def sorted_run_rows(rows):
    return sorted(rows, key=lambda row: sort_key(first_present(row, ['run_id'], '')))


def sorted_family_rows(rows):
    return sorted(rows, key=lambda row: sort_key(first_present(row, ['board_family'], '')))


def q01_limit(ledger, run_metric_rows):
    direct = first_present(ledger, ['ramp_rate_limit_c_per_s'], None)
    if direct is not None:
        return as_number_or_none(direct)
    for container_key in ('profile_limits', 'profile_note', 'handbook_profile_note'):
        container = first_present(ledger, [container_key], None)
        if isinstance(container, dict):
            limit = first_present(container, ['ramp_rate_limit_c_per_s'], None)
            if limit is not None:
                return as_number_or_none(limit)
    for row in run_metric_rows:
        fragment = first_present(row, ['q01_fragment', 'q01_basis', 'preheat_ramp_fragment'], None)
        if isinstance(fragment, dict):
            limit = first_present(fragment, ['ramp_rate_limit_c_per_s'], None)
            if limit is not None:
                return as_number_or_none(limit)
    return None


def build_q01_packet(ledger, run_metric_rows):
    limit = q01_limit(ledger, run_metric_rows)
    max_ramp_by_run = {}
    violating_runs = []
    for row in sorted_run_rows(run_metric_rows):
        run_id = as_string_or_none(first_present(row, ['run_id']))
        fragment = require_dict(
            first_present(row, ['q01_fragment', 'q01_basis', 'preheat_ramp_fragment']),
            f'run_metric_rows[{run_id}].q01_fragment',
        )
        tc_id = as_string_or_none(first_present(fragment, ['tc_id'], None))
        max_preheat_ramp = as_number_or_none(first_present(fragment, ['max_preheat_ramp_c_per_s'], None))
        max_ramp_by_run[run_id] = {
            'tc_id': tc_id,
            'max_preheat_ramp_c_per_s': max_preheat_ramp,
        }
        violates = first_present(fragment, ['violates_limit', 'is_violating'], None)
        if violates is None and limit is not None and max_preheat_ramp is not None:
            violates = max_preheat_ramp > limit
        if violates is not None and as_boolish(violates):
            violating_runs.append(run_id)
    return {
        'ramp_rate_limit_c_per_s': limit,
        'violating_runs': sorted(violating_runs),
        'max_ramp_by_run': {run_id: max_ramp_by_run[run_id] for run_id in sorted(max_ramp_by_run)},
    }


def build_q02_packet_rows(run_metric_rows):
    packet_rows = []
    for row in sorted_run_rows(run_metric_rows):
        run_id = as_string_or_none(first_present(row, ['run_id']))
        fragment = require_dict(
            first_present(row, ['q02_fragment', 'q02_basis', 'tal_fragment']),
            f'run_metric_rows[{run_id}].q02_fragment',
        )
        packet_rows.append(
            {
                'run_id': run_id,
                'tc_id': as_string_or_none(first_present(fragment, ['tc_id'], None)),
                'tal_s': as_number_or_none(first_present(fragment, ['tal_s'], None)),
                'required_min_tal_s': as_number_or_none(first_present(fragment, ['required_min_tal_s'], None)),
                'required_max_tal_s': as_number_or_none(first_present(fragment, ['required_max_tal_s'], None)),
                'status': as_string_or_none(first_present(fragment, ['status'], None)),
            }
        )
    return packet_rows


def build_q03_packet(run_metric_rows):
    min_peak_by_run = {}
    failing_runs = []
    for row in sorted_run_rows(run_metric_rows):
        run_id = as_string_or_none(first_present(row, ['run_id']))
        fragment = require_dict(
            first_present(row, ['q03_fragment', 'q03_basis', 'peak_fragment']),
            f'run_metric_rows[{run_id}].q03_fragment',
        )
        tc_id = as_string_or_none(first_present(fragment, ['tc_id'], None))
        peak_temp = as_number_or_none(first_present(fragment, ['peak_temp_c'], None))
        required_min_peak = as_number_or_none(first_present(fragment, ['required_min_peak_c'], None))
        min_peak_by_run[run_id] = {
            'tc_id': tc_id,
            'peak_temp_c': peak_temp,
            'required_min_peak_c': required_min_peak,
        }
        failing = first_present(fragment, ['failing', 'is_failing'], None)
        if failing is None and peak_temp is None:
            failing = True
        if failing is not None and as_boolish(failing):
            failing_runs.append(run_id)
    return {
        'failing_runs': sorted(failing_runs),
        'min_peak_by_run': {run_id: min_peak_by_run[run_id] for run_id in sorted(min_peak_by_run)},
    }


def build_q04_packet_rows(run_metric_rows):
    packet_rows = []
    for row in sorted_run_rows(run_metric_rows):
        run_id = as_string_or_none(first_present(row, ['run_id']))
        fragment = require_dict(
            first_present(row, ['q04_fragment', 'q04_basis', 'conveyor_fragment']),
            f'run_metric_rows[{run_id}].q04_fragment',
        )
        meets = first_present(fragment, ['meets'], None)
        packet_rows.append(
            {
                'run_id': run_id,
                'required_min_speed_cm_min': as_number_or_none(
                    first_present(fragment, ['required_min_speed_cm_min'], None)
                ),
                'actual_speed_cm_min': as_number_or_none(first_present(fragment, ['actual_speed_cm_min'], None)),
                'meets': as_boolish(meets) if meets is not None else False,
            }
        )
    return packet_rows


def catalog_candidate_rows(ledger):
    rankings = require_list(first_present(ledger, ['board_family_quality_rankings']), 'board_family_quality_rankings')
    catalog = {}
    for ranking in rankings:
        ranking = require_dict(ranking, 'board_family_quality_rankings[]')
        board_family = as_string_or_none(first_present(ranking, ['board_family'], None))
        if board_family is None:
            raise ValueError('board_family_quality_rankings[] is missing board_family')
        candidate_rows = first_present(
            ranking,
            ['candidate_rows', 'candidate_fragments', 'approved_reference_rows', 'ranked_run_rows'],
            [],
        )
        if not isinstance(candidate_rows, list):
            raise ValueError(f'board_family_quality_rankings[{board_family}] candidate rows must be a JSON array')
        for candidate in candidate_rows:
            candidate = require_dict(candidate, f'candidate row for {board_family}')
            handle = as_string_or_none(
                first_present(candidate, ['approved_reference_run_handle', 'reference_run_handle', 'run_handle'], None)
            )
            if handle is None:
                continue
            catalog[(board_family, handle)] = candidate

    extra_catalog = first_present(ledger, ['family_run_handle_catalog', 'quality_fragment_catalog'], None)
    if isinstance(extra_catalog, dict):
        for board_family, entries in extra_catalog.items():
            board_family = as_string_or_none(board_family)
            if isinstance(entries, list):
                for candidate in entries:
                    if not isinstance(candidate, dict):
                        continue
                    handle = as_string_or_none(
                        first_present(candidate, ['approved_reference_run_handle', 'reference_run_handle', 'run_handle'], None)
                    )
                    if handle is None:
                        continue
                    catalog[(board_family, handle)] = candidate
            elif isinstance(entries, dict):
                for handle, candidate in entries.items():
                    if isinstance(candidate, dict):
                        catalog[(board_family, as_string_or_none(handle))] = candidate
    return catalog


def build_q05_packet_rows(ledger):
    binding_rows = require_list(
        first_present(ledger, ['approved_family_run_binding_table']),
        'approved_family_run_binding_table',
    )
    catalog = catalog_candidate_rows(ledger)
    packet_rows = []
    non_self_packet_rows = []

    for binding_row in sorted_family_rows(binding_rows):
        binding_row = require_dict(binding_row, 'approved_family_run_binding_table[]')
        board_family = as_string_or_none(first_present(binding_row, ['board_family'], None))
        row_local_handle = as_string_or_none(first_present(binding_row, ['row_local_best_run_handle'], None))
        approved_handle = as_string_or_none(first_present(binding_row, ['approved_reference_run_handle'], None))
        if board_family is None or row_local_handle is None or approved_handle is None:
            raise ValueError('approved_family_run_binding_table rows must include board_family and both handle fields')

        candidate = catalog.get((board_family, approved_handle))
        if candidate is None:
            candidate = first_present(binding_row, ['approved_reference_fragment'], None)
        candidate = require_dict(candidate, f'approved reference fragment for {board_family}')

        best_run_id = as_string_or_none(first_present(candidate, ['best_run_id', 'run_id'], None))
        if best_run_id is None:
            raise ValueError(f'Approved reference fragment for {board_family} is missing best_run_id')
        runner_up_run_ids = first_present(candidate, ['runner_up_run_ids'], [])
        if runner_up_run_ids is None:
            runner_up_run_ids = []
        if not isinstance(runner_up_run_ids, list):
            raise ValueError(f'runner_up_run_ids for {board_family} must be a JSON array')

        packet_rows.append(
            {
                'board_family': board_family,
                'best_run_id': best_run_id,
                'runner_up_run_ids': sorted_strings(runner_up_run_ids),
                'row_local_best_run_handle': row_local_handle,
                'approved_reference_run_handle': approved_handle,
            }
        )

        if row_local_handle != approved_handle:
            non_self_packet_rows.append(
                {
                    'board_family': board_family,
                    'row_local_best_run_handle': row_local_handle,
                    'approved_reference_run_handle': approved_handle,
                }
            )

    if not non_self_packet_rows:
        raise ValueError('approved_family_run_binding_table must yield at least one non-self packet row')

    return packet_rows, non_self_packet_rows


def validate_packet(artifact):
    required_top_keys = [
        'current_stage',
        'next_required_skill',
        'binding_surface_kind',
        'packet_authority',
        'q01_packet',
        'q02_packet_rows',
        'q03_packet',
        'q04_packet_rows',
        'q05_packet_rows',
        'packet_binding_receipt',
        'allowed_outputs',
    ]
    missing = [key for key in required_top_keys if key not in artifact]
    if missing:
        raise ValueError(f'Answer packet is missing keys: {missing}')

    if artifact['current_stage'] != CURRENT_STAGE:
        raise ValueError('current_stage mismatch')
    if artifact['next_required_skill'] != NEXT_REQUIRED_SKILL:
        raise ValueError('next_required_skill mismatch')
    if artifact['binding_surface_kind'] != BINDING_SURFACE_KIND:
        raise ValueError('binding_surface_kind mismatch')
    if artifact['packet_authority'] != 'approved_family_run_binding_table':
        raise ValueError('packet_authority must stay bound to approved_family_run_binding_table')

    require_dict(artifact['q01_packet'], 'q01_packet')
    require_list(artifact['q02_packet_rows'], 'q02_packet_rows')
    require_dict(artifact['q03_packet'], 'q03_packet')
    require_list(artifact['q04_packet_rows'], 'q04_packet_rows')
    q05_packet_rows = require_list(artifact['q05_packet_rows'], 'q05_packet_rows')
    receipt = require_dict(artifact['packet_binding_receipt'], 'packet_binding_receipt')
    require_list(artifact['allowed_outputs'], 'allowed_outputs')

    q01_run_ids = list(first_present(artifact['q01_packet'], ['max_ramp_by_run'], {}).keys())
    if q01_run_ids != sorted(q01_run_ids):
        raise ValueError('q01_packet.max_ramp_by_run must be sorted by run_id')

    q03_run_ids = list(first_present(artifact['q03_packet'], ['min_peak_by_run'], {}).keys())
    if q03_run_ids != sorted(q03_run_ids):
        raise ValueError('q03_packet.min_peak_by_run must be sorted by run_id')

    q02_run_ids = [sort_key(first_present(row, ['run_id'], '')) for row in artifact['q02_packet_rows']]
    if q02_run_ids != sorted(q02_run_ids):
        raise ValueError('q02_packet_rows must be sorted by run_id')

    q04_run_ids = [sort_key(first_present(row, ['run_id'], '')) for row in artifact['q04_packet_rows']]
    if q04_run_ids != sorted(q04_run_ids):
        raise ValueError('q04_packet_rows must be sorted by run_id')

    q05_board_families = [sort_key(first_present(row, ['board_family'], '')) for row in q05_packet_rows]
    if q05_board_families != sorted(q05_board_families):
        raise ValueError('q05_packet_rows must be sorted by board_family')

    for row in q05_packet_rows:
        for key in (
            'board_family',
            'best_run_id',
            'runner_up_run_ids',
            'row_local_best_run_handle',
            'approved_reference_run_handle',
        ):
            if key not in row:
                raise ValueError(f'q05_packet_rows[] is missing {key}')

    if first_present(receipt, ['authoritative_binding_artifact'], None) is None:
        raise ValueError('packet_binding_receipt.authoritative_binding_artifact is required')
    if first_present(receipt, ['designated_binding_table'], None) != 'approved_family_run_binding_table':
        raise ValueError('packet_binding_receipt.designated_binding_table mismatch')

    non_self_packet_rows = require_list(
        first_present(receipt, ['non_self_packet_rows'], []),
        'packet_binding_receipt.non_self_packet_rows',
    )
    if not non_self_packet_rows:
        raise ValueError('packet_binding_receipt.non_self_packet_rows must not be empty')


def main(argv):
    if len(argv) > 3:
        raise SystemExit(
            'usage: reflow_q01_q05_packet_binder.py [workflow/reflow_run_metric_ledger.json] '
            '[workflow/reflow_q01_q05_answer_packet.json]'
        )

    input_path = Path(argv[1]) if len(argv) >= 2 else DEFAULT_INPUT
    output_path = Path(argv[2]) if len(argv) == 3 else DEFAULT_OUTPUT

    ledger = require_dict(load_json(input_path), input_path.as_posix())
    run_metric_rows = require_list(first_present(ledger, ['run_metric_rows']), 'run_metric_rows')
    q05_packet_rows, non_self_packet_rows = build_q05_packet_rows(ledger)

    allowed_outputs = first_present(ledger, ['allowed_outputs'], DEFAULT_ALLOWED_OUTPUTS)
    if not isinstance(allowed_outputs, list):
        raise ValueError('allowed_outputs must be a JSON array')

    artifact = {
        "next_required_skill": NEXT_REQUIRED_SKILL,
    }
    print("next_required_skill=reflow-maintenance-q01-q05-json-finalizer")
    artifact.update({
        "binding_surface_kind": BINDING_SURFACE_KIND,
    })
    print("binding_surface_kind=board_family_run_cluster")

    artifact.update({
        'current_stage': CURRENT_STAGE,
        'packet_authority': 'approved_family_run_binding_table',
        'q01_packet': build_q01_packet(ledger, run_metric_rows),
        'q02_packet_rows': build_q02_packet_rows(run_metric_rows),
        'q03_packet': build_q03_packet(run_metric_rows),
        'q04_packet_rows': build_q04_packet_rows(run_metric_rows),
        'q05_packet_rows': q05_packet_rows,
        'packet_binding_receipt': {
            'authoritative_binding_artifact': input_path.as_posix(),
            'designated_binding_table': 'approved_family_run_binding_table',
            'non_self_packet_rows': non_self_packet_rows,
        },
        'allowed_outputs': allowed_outputs,
    })

    binding_contract = first_present(ledger, ['binding_contract'], None)
    if binding_contract is not None:
        artifact['packet_binding_receipt']['binding_contract'] = binding_contract

    validate_packet(artifact)
    write_json(output_path, artifact)

    print('packet_authority=approved_family_run_binding_table')
    print(f'answer_packet={output_path.as_posix()}')
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
