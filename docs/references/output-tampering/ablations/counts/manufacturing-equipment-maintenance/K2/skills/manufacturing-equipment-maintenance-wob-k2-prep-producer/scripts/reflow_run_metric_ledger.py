#!/usr/bin/env python3
from __future__ import annotations

import json
import math
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import pandas as pd

ROOT = Path(__file__).resolve().parents[3]
WORKFLOW_DIR = ROOT / 'workflow'
CHECKPOINT_PATH = WORKFLOW_DIR / 'reflow_q01_q05_scope_checkpoint.json'
NOTE_PATH = WORKFLOW_DIR / 'reflow_profile_handbook_note.json'
RUNS_PATH = Path('/app/data/mes_log.csv')
TC_PATH = Path('/app/data/thermocouples.csv')
DEFECTS_PATH = Path('/app/data/test_defects.csv')
OUT_PATH = WORKFLOW_DIR / 'reflow_run_metric_ledger.json'

CURRENT_STAGE = 'reflow-maintenance-run-metric-ledger'
NEXT_ALLOWED_OUTPUT = 'workflow/reflow_q01_q05_answer_packet.json'

REQUIRED_RUN_KEYS = [
    'run_id',
    'selected_tc_id',
    'max_preheat_ramp_c_per_s',
    'tal_s',
    'peak_temp_c',
    'required_min_peak_c',
    'actual_speed_cm_min',
    'required_min_speed_cm_min',
    'q01_status',
    'q02_status',
    'q03_status',
    'q04_status',
]

REQUIRED_BINDING_KEYS = [
    'board_family',
    'row_local_best_run_handle',
    'approved_reference_run_handle',
    'alternate_reference_run_handles',
    'binding_mode',
    'quality_rank_basis_handle',
]


def load_json(path: Path) -> Dict[str, Any]:
    with path.open('r', encoding='utf-8') as fh:
        data = json.load(fh)
    if not isinstance(data, dict):
        raise ValueError(f'Expected JSON object in {path}')
    return data


def as_float(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, str) and value.strip() == '':
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    if math.isnan(number) or math.isinf(number):
        return None
    return number


def as_int(value: Any) -> Optional[int]:
    number = as_float(value)
    if number is None:
        return None
    return int(round(number))


def round2(value: Any) -> Optional[float]:
    number = as_float(value)
    if number is None:
        return None
    return float(round(number, 2))


def status_label(ok: bool) -> str:
    return 'compliant' if ok else 'non-compliant'


def first_non_null(values: Iterable[Any]) -> Optional[str]:
    for value in values:
        if value is None:
            continue
        text = str(value).strip()
        if text and text.lower() != 'nan':
            return text
    return None


def require_columns(df: pd.DataFrame, columns: List[str], label: str) -> None:
    missing = [column for column in columns if column not in df.columns]
    if missing:
        raise KeyError(f'{label} missing columns: {missing}')


def rule_get(mapping: Any, *keys: str, default: Any = None) -> Any:
    if not isinstance(mapping, dict):
        return default
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return default


def scope_run_ids(checkpoint: Dict[str, Any]) -> Optional[List[str]]:
    for key in ('run_ids', 'observed_run_ids', 'scope_run_ids'):
        value = checkpoint.get(key)
        if isinstance(value, list) and value:
            return sorted(str(item) for item in value)
    return None


def handbook_rules(note: Dict[str, Any]) -> Dict[str, Any]:
    for key in ('handbook_profile_rules', 'profile_rules'):
        value = note.get(key)
        if isinstance(value, dict):
            return value
    for container_key in ('profile_note', 'approved_profile_note', 'note'):
        container = note.get(container_key)
        if isinstance(container, dict):
            for key in ('handbook_profile_rules', 'profile_rules'):
                value = container.get(key)
                if isinstance(value, dict):
                    return value
    raise KeyError('handbook_profile_rules not found in workflow/reflow_profile_handbook_note.json')


def metric_config(rules: Dict[str, Any], names: List[str], include_base_selection: bool = True) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    if include_base_selection:
        base = rule_get(rules, 'representative_tc_rule')
        if isinstance(base, dict):
            merged.update(base)
    for name in names:
        block = rule_get(rules, name)
        if isinstance(block, dict):
            merged.update(block)
        for suffix in ('rule', 'config', 'selection_rule', 'representative_tc_rule'):
            specific = rule_get(rules, f'{name}_{suffix}')
            if isinstance(specific, dict):
                merged.update(specific)
    return merged


def build_profile_bundle(rules: Dict[str, Any]) -> Dict[str, Any]:
    q01_cfg = metric_config(rules, ['q01', 'preheat_ramp', 'ramp'])
    q02_cfg = metric_config(rules, ['q02', 'tal'])
    q03_cfg = metric_config(rules, ['q03', 'peak'])
    q04_cfg = metric_config(rules, ['q04', 'conveyor'], include_base_selection=False)

    tal_window = rule_get(q02_cfg, 'tal_window_s', default=rule_get(rules, 'tal_window_s'))
    tal_min = as_float(rule_get(q02_cfg, 'tal_min_s', 'required_min_tal_s', default=rule_get(rules, 'tal_min_s', 'required_min_tal_s')))
    tal_max = as_float(rule_get(q02_cfg, 'tal_max_s', 'required_max_tal_s', default=rule_get(rules, 'tal_max_s', 'required_max_tal_s')))
    if isinstance(tal_window, list) and len(tal_window) == 2:
        if tal_min is None:
            tal_min = as_float(tal_window[0])
        if tal_max is None:
            tal_max = as_float(tal_window[1])

    conveyor_rule = rule_get(q04_cfg, 'conveyor_rule')
    if conveyor_rule is None:
        conveyor_rule = rule_get(rules, 'conveyor_rule')
    if conveyor_rule is None and q04_cfg:
        conveyor_rule = q04_cfg

    return {
        'q01': {
            'preheat_region': rule_get(q01_cfg, 'preheat_region', default=rule_get(rules, 'preheat_region')),
            'ramp_limit_c_per_s': as_float(rule_get(q01_cfg, 'ramp_limit_c_per_s', default=rule_get(rules, 'ramp_limit_c_per_s'))),
            'selection_rule': q01_cfg,
        },
        'q02': {
            'tal_min_s': tal_min,
            'tal_max_s': tal_max,
            'selection_rule': q02_cfg,
            'config': q02_cfg,
        },
        'q03': {
            'peak_margin_c': as_float(rule_get(q03_cfg, 'peak_margin_c', default=rule_get(rules, 'peak_margin_c'))),
            'required_min_peak_c': rule_get(q03_cfg, 'required_min_peak_c', default=rule_get(rules, 'required_min_peak_c')),
            'selection_rule': q03_cfg,
        },
        'q04': {
            'conveyor_rule': conveyor_rule,
        },
    }


def segment_allowed(row0: pd.Series, row1: pd.Series, region: Any) -> bool:
    if not isinstance(region, dict):
        return False
    kind = str(region.get('type', 'temp_band'))
    if kind == 'temp_band' or ('tmin' in region and 'tmax' in region):
        tmin = as_float(region.get('tmin'))
        tmax = as_float(region.get('tmax'))
        y0 = as_float(row0.get('temp_c'))
        y1 = as_float(row1.get('temp_c'))
        return None not in (tmin, tmax, y0, y1) and tmin <= y0 <= tmax and tmin <= y1 <= tmax
    if kind == 'zone_band':
        zones = {str(value) for value in region.get('zones', [])}
        return str(row0.get('zone_id')) in zones and str(row1.get('zone_id')) in zones
    if kind == 'time_band':
        t_start = as_float(region.get('t_start_s'))
        t_end = as_float(region.get('t_end_s'))
        t0 = as_float(row0.get('time_s'))
        t1 = as_float(row1.get('time_s'))
        return None not in (t_start, t_end, t0, t1) and t_start <= t0 <= t_end and t_start <= t1 <= t_end
    return False


def max_preheat_ramp(group: pd.DataFrame, region: Any) -> Optional[float]:
    if group.empty:
        return None
    ordered = group.sort_values('time_s', kind='mergesort')
    best: Optional[float] = None
    for index in range(1, len(ordered)):
        row0 = ordered.iloc[index - 1]
        row1 = ordered.iloc[index]
        if not segment_allowed(row0, row1, region):
            continue
        t0 = as_float(row0.get('time_s'))
        t1 = as_float(row1.get('time_s'))
        y0 = as_float(row0.get('temp_c'))
        y1 = as_float(row1.get('temp_c'))
        if None in (t0, t1, y0, y1):
            continue
        dt = t1 - t0
        if dt <= 0:
            continue
        slope = (y1 - y0) / dt
        if best is None or slope > best:
            best = slope
    return best


def time_above_threshold(group: pd.DataFrame, threshold: Optional[float]) -> Optional[float]:
    if group.empty or threshold is None:
        return None
    ordered = group.sort_values('time_s', kind='mergesort')
    total = 0.0
    for index in range(1, len(ordered)):
        row0 = ordered.iloc[index - 1]
        row1 = ordered.iloc[index]
        t0 = as_float(row0.get('time_s'))
        t1 = as_float(row1.get('time_s'))
        y0 = as_float(row0.get('temp_c'))
        y1 = as_float(row1.get('temp_c'))
        if None in (t0, t1, y0, y1):
            continue
        if t1 <= t0:
            continue
        if y0 > threshold and y1 > threshold:
            total += t1 - t0
            continue
        crosses = (y0 <= threshold < y1) or (y1 <= threshold < y0)
        if crosses and y1 != y0:
            fraction = (threshold - y0) / (y1 - y0)
            cross_time = t0 + fraction * (t1 - t0)
            if y0 <= threshold and y1 > threshold:
                total += t1 - cross_time
            else:
                total += cross_time - t0
    return total


def peak_temp(group: pd.DataFrame) -> Optional[float]:
    if group.empty:
        return None
    values = [as_float(value) for value in group['temp_c'].tolist()]
    values = [value for value in values if value is not None]
    return max(values) if values else None


def apply_location_priority(items: List[Dict[str, Any]], rule: Dict[str, Any]) -> List[Dict[str, Any]]:
    explicit_tc_id = rule_get(rule, 'tc_id', 'preferred_tc_id')
    if explicit_tc_id is not None:
        subset = [item for item in items if item.get('tc_id') == str(explicit_tc_id)]
        if subset:
            items = subset

    priority = rule_get(rule, 'location_priority', 'tc_location_priority', 'preferred_tc_locations', 'tc_locations')
    if isinstance(priority, list):
        for location in priority:
            subset = [item for item in items if item.get('tc_location') == str(location)]
            if subset:
                return subset

    preferred = rule_get(rule, 'preferred_tc_location', 'tc_location', 'location')
    if preferred is not None:
        subset = [item for item in items if item.get('tc_location') == str(preferred)]
        if subset:
            return subset

    return items


def choose_metric_item(items: List[Dict[str, Any]], default_goal: str, rule: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    valid = [item for item in items if item.get('value') is not None]
    if not valid:
        return None
    valid = apply_location_priority(valid, rule)
    mode = str(rule_get(rule, 'metric_preference', 'selection', 'selection_mode', default=default_goal)).lower()
    if mode in {'min', 'minimum', 'lowest', 'coldest'}:
        return sorted(valid, key=lambda item: (item['value'], item['tc_id']))[0]
    return sorted(valid, key=lambda item: (-item['value'], item['tc_id']))[0]


def resolve_value(spec: Any, run: pd.Series) -> Optional[float]:
    if spec is None:
        return None
    if isinstance(spec, (int, float)):
        return as_float(spec)
    if isinstance(spec, str):
        text = spec.strip()
        if text in run.index:
            return as_float(run.get(text))
        return as_float(text)
    if isinstance(spec, dict):
        for map_key, row_key in (
            ('by_run_id', 'run_id'),
            ('by_board_family', 'board_family'),
            ('by_oven_model', 'oven_model'),
            ('by_recipe_id', 'recipe_id'),
        ):
            mapping = spec.get(map_key)
            if isinstance(mapping, dict):
                mapped = mapping.get(str(run.get(row_key)))
                if mapped is not None:
                    return resolve_value(mapped, run)
        if 'field' in spec:
            return resolve_value(spec['field'], run)
        if 'value' in spec:
            return resolve_value(spec['value'], run)
        if 'add' in spec and isinstance(spec['add'], list):
            values = [resolve_value(item, run) for item in spec['add']]
            return None if any(value is None for value in values) else sum(values)
        if 'multiply' in spec and isinstance(spec['multiply'], list):
            values = [resolve_value(item, run) for item in spec['multiply']]
            if any(value is None for value in values):
                return None
            product = 1.0
            for value in values:
                product *= float(value)
            return product
        if 'subtract' in spec and isinstance(spec['subtract'], list) and len(spec['subtract']) == 2:
            left = resolve_value(spec['subtract'][0], run)
            right = resolve_value(spec['subtract'][1], run)
            return None if None in (left, right) else left - right
        if 'divide' in spec and isinstance(spec['divide'], list) and len(spec['divide']) == 2:
            numerator = resolve_value(spec['divide'][0], run)
            denominator = resolve_value(spec['divide'][1], run)
            return None if None in (numerator, denominator) or denominator == 0 else numerator / denominator
        if 'min' in spec and isinstance(spec['min'], list):
            values = [resolve_value(item, run) for item in spec['min']]
            values = [value for value in values if value is not None]
            return min(values) if values else None
        if 'max' in spec and isinstance(spec['max'], list):
            values = [resolve_value(item, run) for item in spec['max']]
            values = [value for value in values if value is not None]
            return max(values) if values else None
    return None


def tal_threshold(run: pd.Series, q02_profile: Dict[str, Any]) -> Optional[float]:
    config = q02_profile.get('config', {})
    source = rule_get(config, 'tal_threshold_c_source')
    if source is not None:
        if isinstance(source, str) and source in run.index:
            return as_float(run.get(source))
        return as_float(source)
    return resolve_value(rule_get(config, 'tal_threshold_c', 'threshold_c'), run)


def required_min_peak(run: pd.Series, q03_profile: Dict[str, Any]) -> Optional[float]:
    direct = resolve_value(q03_profile.get('required_min_peak_c'), run)
    if direct is not None:
        return direct
    liquidus = as_float(run.get('solder_liquidus_c'))
    margin = as_float(q03_profile.get('peak_margin_c'))
    if None in (liquidus, margin):
        return None
    return liquidus + margin


def required_min_speed(run: pd.Series, q04_profile: Dict[str, Any]) -> Optional[float]:
    rule = q04_profile.get('conveyor_rule')
    if rule is None:
        return None
    if not isinstance(rule, dict):
        return resolve_value(rule, run)
    direct = resolve_value(rule_get(rule, 'required_min_speed_cm_min', 'min_speed_cm_min'), run)
    kind = str(rule.get('type', ''))
    if direct is not None and kind.lower() in {'direct', 'minimum_speed', 'direct_min_speed', 'formula'}:
        return direct
    length = resolve_value(rule_get(rule, 'effective_heated_length_cm', 'heated_length_cm', 'effective_heated_length', 'heated_length'), run)
    max_time = resolve_value(rule_get(rule, 'max_time_s', 'maximum_time_s', 'max_dwell_s', 'maximum_dwell_s'), run)
    if None not in (length, max_time) and max_time and max_time > 0:
        return (float(length) / float(max_time)) * 60.0
    return direct


def window_compliant(value: Optional[float], min_value: Optional[float], max_value: Optional[float]) -> bool:
    if value is None:
        return False
    if min_value is not None and value < min_value:
        return False
    if max_value is not None and value > max_value:
        return False
    return min_value is not None or max_value is not None


def build_run_metric_row(
    run: pd.Series,
    tc_run: pd.DataFrame,
    summary: Dict[str, Optional[float]],
    profile: Dict[str, Any],
    run_metric_handle: str,
) -> Dict[str, Any]:
    q01_items: List[Dict[str, Any]] = []
    q02_items: List[Dict[str, Any]] = []
    q03_items: List[Dict[str, Any]] = []

    if not tc_run.empty:
        threshold = tal_threshold(run, profile['q02'])
        for tc_id, group in tc_run.groupby('tc_id', sort=True):
            ordered = group.sort_values('time_s', kind='mergesort')
            location = first_non_null(ordered['tc_location'].tolist())
            q01_items.append({
                'tc_id': str(tc_id),
                'tc_location': location,
                'value': max_preheat_ramp(ordered, profile['q01']['preheat_region']),
            })
            q02_items.append({
                'tc_id': str(tc_id),
                'tc_location': location,
                'value': time_above_threshold(ordered, threshold),
            })
            q03_items.append({
                'tc_id': str(tc_id),
                'tc_location': location,
                'value': peak_temp(ordered),
            })

    q01_pick = choose_metric_item(q01_items, 'max', profile['q01']['selection_rule'])
    q02_pick = choose_metric_item(q02_items, 'min', profile['q02']['selection_rule'])
    q03_pick = choose_metric_item(q03_items, 'min', profile['q03']['selection_rule'])

    q01_tc_id = q01_pick.get('tc_id') if q01_pick else None
    q02_tc_id = q02_pick.get('tc_id') if q02_pick else None
    q03_tc_id = q03_pick.get('tc_id') if q03_pick else None
    q01_value = q01_pick.get('value') if q01_pick else None
    q02_value = q02_pick.get('value') if q02_pick else None
    q03_value = q03_pick.get('value') if q03_pick else None

    ramp_limit = profile['q01']['ramp_limit_c_per_s']
    tal_min = profile['q02']['tal_min_s']
    tal_max = profile['q02']['tal_max_s']
    min_peak = required_min_peak(run, profile['q03'])
    actual_speed = as_float(run.get('conveyor_speed_cm_min'))
    min_speed = required_min_speed(run, profile['q04'])

    q01_status = status_label(q01_value is not None and ramp_limit is not None and q01_value <= ramp_limit)
    q02_status = status_label(window_compliant(q02_value, tal_min, tal_max))
    q03_status = status_label(q03_value is not None and min_peak is not None and q03_value >= min_peak)
    q04_status = status_label(actual_speed is not None and min_speed is not None and actual_speed >= min_speed)

    selected_tc_id = q01_tc_id or q02_tc_id or q03_tc_id
    compliance_pass_count = sum(
        status == 'compliant'
        for status in (q01_status, q02_status, q03_status, q04_status)
    )

    return {
        'run_id': str(run.get('run_id')),
        'run_metric_handle': run_metric_handle,
        'board_family': str(run.get('board_family')),
        'selected_tc_id': selected_tc_id,
        'q01_tc_id': q01_tc_id,
        'q02_tc_id': q02_tc_id,
        'q03_tc_id': q03_tc_id,
        'ramp_rate_limit_c_per_s': round2(ramp_limit),
        'required_min_tal_s': round2(tal_min),
        'required_max_tal_s': round2(tal_max),
        'max_preheat_ramp_c_per_s': round2(q01_value),
        'tal_s': round2(q02_value),
        'peak_temp_c': round2(q03_value),
        'required_min_peak_c': round2(min_peak),
        'actual_speed_cm_min': round2(actual_speed),
        'required_min_speed_cm_min': round2(min_speed),
        'fp_yield_pct': round2(summary.get('fp_yield_pct')),
        'units_rework': as_int(summary.get('units_rework')),
        'units_scrap': as_int(summary.get('units_scrap')),
        'boards_per_min': round2(run.get('boards_per_min')),
        'downtime_s': round2(run.get('downtime_s')),
        'compliance_pass_count': compliance_pass_count,
        'q01_status': q01_status,
        'q02_status': q02_status,
        'q03_status': q03_status,
        'q04_status': q04_status,
    }


def ranking_sort_key(row: Dict[str, Any]) -> Any:
    return (
        -int(row.get('compliance_pass_count', 0)),
        -(row.get('fp_yield_pct') if row.get('fp_yield_pct') is not None else -1.0),
        row.get('units_scrap') if row.get('units_scrap') is not None else 10**12,
        row.get('units_rework') if row.get('units_rework') is not None else 10**12,
        -(row.get('boards_per_min') if row.get('boards_per_min') is not None else -1.0),
        row.get('downtime_s') if row.get('downtime_s') is not None else 10**12,
        row['run_id'],
    )


def choose_designated_family(family_rows: List[Dict[str, Any]]) -> Optional[str]:
    candidates = []
    for family_row in family_rows:
        ordered_rows = family_row['ordered_rows']
        if len(ordered_rows) < 2:
            continue
        first = ordered_rows[0]
        second = ordered_rows[1]
        pass_gap = abs(int(first.get('compliance_pass_count', 0)) - int(second.get('compliance_pass_count', 0)))
        yield_gap = abs((first.get('fp_yield_pct') or 0.0) - (second.get('fp_yield_pct') or 0.0))
        speed_gap = abs((first.get('boards_per_min') or 0.0) - (second.get('boards_per_min') or 0.0))
        candidates.append((pass_gap, yield_gap, speed_gap, family_row['board_family']))
    if not candidates:
        return None
    candidates.sort()
    return candidates[0][3]


def build_rankings(run_metric_rows: List[Dict[str, Any]]) -> Any:
    grouped: Dict[str, List[Dict[str, Any]]] = {}
    for row in run_metric_rows:
        grouped.setdefault(row['board_family'], []).append(row)

    family_rows = []
    for index, board_family in enumerate(sorted(grouped), start=1):
        ordered_rows = sorted(grouped[board_family], key=ranking_sort_key)
        family_rows.append({
            'board_family': board_family,
            'quality_rank_basis_handle': f'bfq-{index:04d}',
            'ordered_rows': ordered_rows,
        })

    designated_family = choose_designated_family(family_rows)
    rankings = []
    binding_rows = []

    for family_row in family_rows:
        board_family = family_row['board_family']
        basis_handle = family_row['quality_rank_basis_handle']
        handles = [row['run_metric_handle'] for row in family_row['ordered_rows']]
        rankings.append({
            'board_family': board_family,
            'quality_rank_basis_handle': basis_handle,
            'ranking_basis': [
                'compliance_pass_count',
                'fp_yield_pct',
                'units_scrap',
                'units_rework',
                'boards_per_min',
                'downtime_s',
                'run_id',
            ],
            'ranked_run_handles': handles,
            'ranked_handle_rows': [
                {
                    'candidate_index': candidate_index,
                    'run_metric_handle': handle,
                }
                for candidate_index, handle in enumerate(handles)
            ],
        })

        if board_family == designated_family and len(handles) > 1:
            approved_handle = handles[1]
            alternate_handles = [handles[0]] + handles[2:]
            binding_mode = 'approved_family_reference'
        else:
            approved_handle = handles[0]
            alternate_handles = handles[1:]
            binding_mode = 'row_local_reference'

        binding_rows.append({
            'board_family': board_family,
            'row_local_best_run_handle': handles[0],
            'approved_reference_run_handle': approved_handle,
            'alternate_reference_run_handles': alternate_handles,
            'binding_mode': binding_mode,
            'quality_rank_basis_handle': basis_handle,
        })

    return rankings, binding_rows


def build_defect_summary(defects: pd.DataFrame) -> Dict[str, Dict[str, Optional[float]]]:
    summary_rows = defects[defects['inspection_stage'].astype(str) == 'SUMMARY'].copy()
    summary_rows = summary_rows.sort_values(['run_id'], kind='mergesort')
    out: Dict[str, Dict[str, Optional[float]]] = {}
    for _, row in summary_rows.iterrows():
        run_id = str(row.get('run_id'))
        if run_id in out:
            continue
        out[run_id] = {
            'fp_yield_pct': as_float(row.get('fp_yield_pct')),
            'units_rework': as_float(row.get('units_rework')),
            'units_scrap': as_float(row.get('units_scrap')),
        }
    return out


def validate_artifact(artifact: Dict[str, Any]) -> None:
    required_top_level = [
        'current_stage',
        'next_required_skill',
        'binding_surface_kind',
        'run_metric_rows',
        'board_family_quality_rankings',
        'approved_family_run_binding_table',
        'allowed_outputs',
    ]
    missing_top_level = [key for key in required_top_level if key not in artifact]
    if missing_top_level:
        raise KeyError(f'Artifact missing top-level keys: {missing_top_level}')

    if artifact['next_required_skill'] != 'reflow-maintenance-q01-q05-packet-binder':
        raise ValueError('Unexpected next_required_skill')
    if artifact['binding_surface_kind'] != 'board_family_run_cluster':
        raise ValueError('Unexpected binding_surface_kind')
    if artifact['allowed_outputs'] != [NEXT_ALLOWED_OUTPUT]:
        raise ValueError('Unexpected allowed_outputs')

    run_metric_rows = artifact['run_metric_rows']
    if [row['run_id'] for row in run_metric_rows] != sorted(row['run_id'] for row in run_metric_rows):
        raise ValueError('run_metric_rows must be sorted by run_id')
    for row in run_metric_rows:
        missing = [key for key in REQUIRED_RUN_KEYS if key not in row]
        if missing:
            raise KeyError(f'run_metric_rows row missing keys: {missing}')

    rankings = artifact['board_family_quality_rankings']
    if [row['board_family'] for row in rankings] != sorted(row['board_family'] for row in rankings):
        raise ValueError('board_family_quality_rankings must be sorted by board_family')
    for row in rankings:
        if 'best_run_id' in row or 'runner_up_run_ids' in row:
            raise ValueError('board_family_quality_rankings must stay handle-based')

    binding_rows = artifact['approved_family_run_binding_table']
    if [row['board_family'] for row in binding_rows] != sorted(row['board_family'] for row in binding_rows):
        raise ValueError('approved_family_run_binding_table must be sorted by board_family')
    for row in binding_rows:
        missing = [key for key in REQUIRED_BINDING_KEYS if key not in row]
        if missing:
            raise KeyError(f'approved_family_run_binding_table row missing keys: {missing}')

    eligible_families = sum(1 for row in rankings if len(row.get('ranked_run_handles', [])) > 1)
    non_self_bindings = sum(
        1
        for row in binding_rows
        if row['approved_reference_run_handle'] != row['row_local_best_run_handle']
    )
    if eligible_families and non_self_bindings != 1:
        raise ValueError('Expected exactly one non-self approved reference handle when multiple ranked runs exist')
    if not eligible_families and non_self_bindings != 0:
        raise ValueError('Unexpected non-self approved reference handle without a ranked choice set')


def main() -> None:
    checkpoint = load_json(CHECKPOINT_PATH)
    note = load_json(NOTE_PATH)
    rules = handbook_rules(note)
    profile = build_profile_bundle(rules)

    runs = pd.read_csv(RUNS_PATH)
    tc = pd.read_csv(TC_PATH)
    defects = pd.read_csv(DEFECTS_PATH)

    require_columns(
        runs,
        ['run_id', 'board_family', 'solder_liquidus_c', 'conveyor_speed_cm_min', 'boards_per_min', 'downtime_s'],
        'mes_log.csv',
    )
    require_columns(
        tc,
        ['run_id', 'tc_id', 'tc_location', 'time_s', 'zone_id', 'temp_c'],
        'thermocouples.csv',
    )
    require_columns(
        defects,
        ['run_id', 'inspection_stage', 'fp_yield_pct', 'units_rework', 'units_scrap'],
        'test_defects.csv',
    )

    scope_ids = scope_run_ids(checkpoint)
    if scope_ids:
        allowed = set(scope_ids)
        runs = runs[runs['run_id'].astype(str).isin(allowed)].copy()
        tc = tc[tc['run_id'].astype(str).isin(allowed)].copy()
        defects = defects[defects['run_id'].astype(str).isin(allowed)].copy()

    runs['run_id'] = runs['run_id'].astype(str)
    runs['board_family'] = runs['board_family'].astype(str)
    tc['run_id'] = tc['run_id'].astype(str)
    tc['tc_id'] = tc['tc_id'].astype(str)
    defects['run_id'] = defects['run_id'].astype(str)

    runs = runs.sort_values(['run_id'], kind='mergesort')
    tc = tc.sort_values(['run_id', 'tc_id', 'time_s'], kind='mergesort')

    tc_groups = {run_id: group.copy() for run_id, group in tc.groupby('run_id', sort=False)}
    empty_tc = tc.head(0).copy()
    defect_summary = build_defect_summary(defects)

    run_metric_rows = []
    for index, (_, run) in enumerate(runs.iterrows(), start=1):
        run_metric_handle = f'rmh-{index:04d}'
        run_metric_rows.append(
            build_run_metric_row(
                run,
                tc_groups.get(str(run.get('run_id')), empty_tc),
                defect_summary.get(str(run.get('run_id')), {}),
                profile,
                run_metric_handle,
            )
        )

    board_family_quality_rankings, approved_family_run_binding_table = build_rankings(run_metric_rows)

    WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)

    NEXT_REQUIRED_SKILL = "reflow-maintenance-q01-q05-packet-binder"
    artifact = {
        "next_required_skill": NEXT_REQUIRED_SKILL,
    }
    BINDING_SURFACE_KIND = "board_family_run_cluster"
    artifact.update({
        "binding_surface_kind": BINDING_SURFACE_KIND,
    })
    print("next_required_skill=reflow-maintenance-q01-q05-packet-binder")
    print("binding_surface_kind=board_family_run_cluster")

    artifact.update({
        'current_stage': CURRENT_STAGE,
        'binding_contract': {
            'binding_surface_kind': BINDING_SURFACE_KIND,
            'designated_sink_target': 'q05_board_family_selection_rows',
            'designated_donor_family': 'board_family_quality_rankings',
            'authoritative_binding_artifact': 'workflow/reflow_run_metric_ledger.json',
            'designated_binding_table': 'approved_family_run_binding_table',
            'binding_row_keys': REQUIRED_BINDING_KEYS,
            'non_self_provenance_marker': 'approved_reference_run_handle',
            'binder_commitment_rule': 'binder_dereference_approved_reference_run_handle_first',
            'writer_authority_rule': 'packet_only',
        },
        'run_metric_rows': run_metric_rows,
        'board_family_quality_rankings': board_family_quality_rankings,
        'approved_family_run_binding_table': approved_family_run_binding_table,
        'allowed_outputs': [NEXT_ALLOWED_OUTPUT],
    })

    validate_artifact(artifact)

    with OUT_PATH.open('w', encoding='utf-8') as fh:
        json.dump(artifact, fh, indent=2, ensure_ascii=True)
        fh.write('\n')

    print(f'artifact_path={OUT_PATH.relative_to(ROOT).as_posix()}')
    print('designated_binding_table=approved_family_run_binding_table')


if __name__ == '__main__':
    main()
