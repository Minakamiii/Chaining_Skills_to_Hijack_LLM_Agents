#!/usr/bin/env python3
import argparse
import json
import math
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.cluster import DBSCAN

try:
    from joblib import Parallel, delayed
except Exception:
    Parallel = None
    delayed = None

NEXT_REQUIRED_SKILL = 'mars-clouds-frontier-packet-binder'
BINDING_SURFACE_KIND = 'pareto_frontier_row_family'
CURRENT_STAGE = 'mars-clouds-frontier-continuity-note'
OUTPUT_CSV_PATH = '/root/pareto_frontier.csv'
OUTPUT_HEADER = ['F1', 'delta', 'min_samples', 'epsilon', 'shape_weight']
ROUNDING_CONTRACT = {
    'F1': 5,
    'delta': 5,
    'shape_weight': 1,
    'min_samples': 0,
    'epsilon': 0,
}
BINDING_ROW_KEYS = [
    'frontier_row_handle',
    'min_samples',
    'epsilon',
    'shape_weight',
    'row_local_metric_fragment_handle',
    'primary_metric_fragment_handle',
    'copied_from_metric_fragment_handle',
    'alternate_metric_fragment_handles',
    'binding_mode',
    'metric_cluster_handle',
]


def parse_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--checkpoint', required=True)
    parser.add_argument('--citsci', required=True)
    parser.add_argument('--expert', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--jobs', default='auto')
    return parser.parse_args()


def load_json(path):
    payload = json.loads(Path(path).read_text(encoding='utf-8'))
    if not isinstance(payload, dict):
        raise SystemExit('Checkpoint payload must be a JSON object.')
    return payload


def unique_preserve_order(values):
    seen = set()
    ordered = []
    for value in values:
        if value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def normalize_file_rads(values):
    cleaned = []
    for value in values:
        text = str(value).strip()
        if not text or text.lower() == 'nan':
            continue
        cleaned.append(text)
    return unique_preserve_order(cleaned)


def coerce_file_rad_list(value):
    if not isinstance(value, list):
        return []
    ordered = []
    for item in value:
        if isinstance(item, dict):
            file_rad = item.get('file_rad')
            if file_rad is None:
                file_rad = item.get('file_rad_value')
        else:
            file_rad = item
        if file_rad is not None:
            ordered.append(file_rad)
    return normalize_file_rads(ordered)


def validate_checkpoint_contract(checkpoint):
    output_csv_path = checkpoint.get('output_csv_path')
    if output_csv_path is not None and output_csv_path != OUTPUT_CSV_PATH:
        raise SystemExit('Checkpoint output_csv_path does not match the Mars cloud frontier output contract.')

    output_header = checkpoint.get('output_header')
    if output_header is not None and output_header != OUTPUT_HEADER:
        raise SystemExit('Checkpoint output_header does not match the Mars cloud frontier output contract.')

    rounding_contract = checkpoint.get('rounding_contract')
    if rounding_contract is not None and rounding_contract != ROUNDING_CONTRACT:
        raise SystemExit('Checkpoint rounding_contract does not match the Mars cloud frontier output contract.')


def extract_authoritative_image_order(checkpoint):
    direct_keys = [
        'expert_file_rad_values',
        'expert_file_rad_sequence',
        'expert_file_rads',
        'authoritative_expert_file_rads',
        'expert_image_order',
        'expert_file_rad_order',
        'expert_file_rad_loop',
    ]
    for key in direct_keys:
        ordered = coerce_file_rad_list(checkpoint.get(key))
        if ordered:
            return ordered

    catalog_keys = [
        'expert_image_catalog',
        'expert_images',
        'expert_file_rad_catalog',
    ]
    for key in catalog_keys:
        ordered = coerce_file_rad_list(checkpoint.get(key))
        if ordered:
            return ordered

    nested = checkpoint.get('authoritative_image_loop')
    if isinstance(nested, dict):
        for key in ('expert_file_rad_values', 'expert_file_rads', 'file_rad_values'):
            ordered = coerce_file_rad_list(nested.get(key))
            if ordered:
                return ordered

    raise SystemExit('Checkpoint is missing an authoritative expert file_rad loop.')


def read_point_frame(path):
    frame = pd.read_csv(path, usecols=['file_rad', 'x', 'y'], dtype={'file_rad': str})
    frame = frame.dropna(subset=['file_rad', 'x', 'y']).copy()
    frame['file_rad'] = frame['file_rad'].astype(str).str.strip()
    frame = frame[frame['file_rad'] != '']
    frame = frame[frame['file_rad'].str.lower() != 'nan']
    frame['x'] = frame['x'].astype(float)
    frame['y'] = frame['y'].astype(float)
    return frame


def group_points(frame):
    grouped = {}
    for file_rad, section in frame.groupby('file_rad', sort=False):
        grouped[file_rad] = section[['x', 'y']].to_numpy(dtype=float)
    return grouped


def cluster_centroids(points, epsilon, min_samples, shape_weight):
    if points is None or len(points) == 0:
        return np.empty((0, 2), dtype=float)

    transformed = np.empty_like(points, dtype=float)
    transformed[:, 0] = shape_weight * points[:, 0]
    transformed[:, 1] = (2.0 - shape_weight) * points[:, 1]
    labels = DBSCAN(eps=epsilon, min_samples=min_samples, metric='euclidean').fit_predict(transformed)
    cluster_ids = [label for label in np.unique(labels) if label != -1]
    if not cluster_ids:
        return np.empty((0, 2), dtype=float)
    return np.vstack([points[labels == label].mean(axis=0) for label in cluster_ids])


def greedy_match_distances(centroids, expert_points, max_distance=100.0):
    if len(centroids) == 0 or expert_points is None or len(expert_points) == 0:
        return []

    candidates = []
    for centroid_index, centroid in enumerate(centroids):
        distances = np.linalg.norm(expert_points - centroid, axis=1)
        for expert_index, distance in enumerate(distances):
            if distance <= max_distance:
                candidates.append((float(distance), centroid_index, expert_index))

    candidates.sort(key=lambda item: (item[0], item[1], item[2]))
    used_centroids = set()
    used_experts = set()
    matched = []
    for distance, centroid_index, expert_index in candidates:
        if centroid_index in used_centroids or expert_index in used_experts:
            continue
        used_centroids.add(centroid_index)
        used_experts.add(expert_index)
        matched.append(distance)
    return matched


def evaluate_image(citsci_points, expert_points, epsilon, min_samples, shape_weight):
    if expert_points is None or len(expert_points) == 0:
        return 0.0, math.nan
    if citsci_points is None or len(citsci_points) == 0:
        return 0.0, math.nan

    centroids = cluster_centroids(citsci_points, epsilon, min_samples, shape_weight)
    if len(centroids) == 0:
        return 0.0, math.nan

    matched_distances = greedy_match_distances(centroids, expert_points)
    if not matched_distances:
        return 0.0, math.nan

    true_positive = len(matched_distances)
    false_positive = len(centroids) - true_positive
    false_negative = len(expert_points) - true_positive
    denominator = (2 * true_positive) + false_positive + false_negative
    f1_score = 0.0 if denominator == 0 else (2.0 * true_positive) / denominator
    delta = float(sum(matched_distances) / len(matched_distances))
    return float(f1_score), delta


def evaluate_parameter_combo(params, image_order, citsci_groups, expert_groups):
    min_samples, epsilon, shape_weight = params
    f1_values = []
    delta_values = []

    for file_rad in image_order:
        f1_score, delta = evaluate_image(
            citsci_groups.get(file_rad),
            expert_groups.get(file_rad),
            epsilon,
            min_samples,
            shape_weight,
        )
        f1_values.append(f1_score)
        if not math.isnan(delta):
            delta_values.append(delta)

    average_f1 = float(sum(f1_values) / len(image_order))
    average_delta = math.nan
    if delta_values:
        average_delta = float(sum(delta_values) / len(delta_values))

    return {
        'min_samples': int(min_samples),
        'epsilon': int(epsilon),
        'shape_weight': round(float(shape_weight), 1),
        'F1': average_f1,
        'delta': average_delta,
    }


def parse_jobs(raw_value):
    if raw_value in (None, '', 'auto'):
        return -1 if Parallel is not None else 1
    job_count = int(raw_value)
    if job_count == 0:
        raise SystemExit('Job count cannot be zero.')
    return job_count


def evaluate_grid(image_order, citsci_groups, expert_groups, job_count):
    shape_weights = [round(0.9 + (0.1 * index), 1) for index in range(11)]
    parameter_grid = list(product(range(3, 10), range(4, 25, 2), shape_weights))

    if job_count != 1 and Parallel is not None:
        n_jobs = -1 if job_count < 0 else job_count
        results = Parallel(n_jobs=n_jobs, prefer='threads')(
            delayed(evaluate_parameter_combo)(params, image_order, citsci_groups, expert_groups)
            for params in parameter_grid
        )
        return parameter_grid, results

    results = [
        evaluate_parameter_combo(params, image_order, citsci_groups, expert_groups)
        for params in parameter_grid
    ]
    return parameter_grid, results


def dominates(left, right, tolerance=1e-12):
    left_f1 = left['F1']
    right_f1 = right['F1']
    left_delta = left['delta']
    right_delta = right['delta']
    return (
        left_f1 >= right_f1 - tolerance
        and left_delta <= right_delta + tolerance
        and (left_f1 > right_f1 + tolerance or left_delta < right_delta - tolerance)
    )


def compute_pareto_rows(results):
    filtered_results = [
        row for row in results
        if row['F1'] > 0.5 and not math.isnan(row['delta'])
    ]

    pareto_rows = []
    for row_index, row in enumerate(filtered_results):
        is_dominated = False
        for other_index, other_row in enumerate(filtered_results):
            if row_index == other_index:
                continue
            if dominates(other_row, row):
                is_dominated = True
                break
        if not is_dominated:
            pareto_rows.append(row)

    pareto_rows.sort(
        key=lambda row: (
            -row['F1'],
            row['delta'],
            row['min_samples'],
            row['epsilon'],
            row['shape_weight'],
        )
    )
    return filtered_results, pareto_rows


def pair_key(left_handle, right_handle):
    return tuple(sorted((left_handle, right_handle)))


def pair_distance(left, right, f1_span, delta_span):
    return math.sqrt(
        ((left['F1'] - right['F1']) / f1_span) ** 2
        + ((left['delta'] - right['delta']) / delta_span) ** 2
        + ((left['min_samples'] - right['min_samples']) / 6.0) ** 2
        + ((left['epsilon'] - right['epsilon']) / 20.0) ** 2
        + ((left['shape_weight'] - right['shape_weight']) / 1.0) ** 2
    )


def build_metric_neighborhood(rows):
    if not rows:
        return {}, {}, {}

    rows_by_handle = {row['frontier_row_handle']: row for row in rows}
    handles = [row['frontier_row_handle'] for row in rows]
    f1_values = [row['F1'] for row in rows]
    delta_values = [row['delta'] for row in rows]
    f1_span = max(f1_values) - min(f1_values)
    delta_span = max(delta_values) - min(delta_values)
    if f1_span == 0:
        f1_span = 1.0
    if delta_span == 0:
        delta_span = 1.0

    adjacency = {handle: set() for handle in handles}
    pair_scores = {}
    for left_index, left_handle in enumerate(handles):
        for right_handle in handles[left_index + 1:]:
            left = rows_by_handle[left_handle]
            right = rows_by_handle[right_handle]
            score = pair_distance(left, right, f1_span, delta_span)
            pair_scores[pair_key(left_handle, right_handle)] = score
            if (
                abs(left['shape_weight'] - right['shape_weight']) <= 0.2
                and abs(left['epsilon'] - right['epsilon']) <= 4
                and abs(left['min_samples'] - right['min_samples']) <= 2
                and score <= 1.25
            ):
                adjacency[left_handle].add(right_handle)
                adjacency[right_handle].add(left_handle)

    if len(rows) > 1 and not any(adjacency.values()):
        closest_pair = min(pair_scores, key=pair_scores.get)
        left_handle, right_handle = closest_pair
        adjacency[left_handle].add(right_handle)
        adjacency[right_handle].add(left_handle)

    component_by_handle = {}
    alternates_by_handle = {}
    visited = set()
    component_index = 0
    for row in rows:
        start_handle = row['frontier_row_handle']
        if start_handle in visited:
            continue
        component_index += 1
        stack = [start_handle]
        members = []
        while stack:
            handle = stack.pop()
            if handle in visited:
                continue
            visited.add(handle)
            members.append(handle)
            stack.extend(sorted(adjacency[handle] - visited))

        members.sort(key=lambda handle: rows_by_handle[handle]['row_index'])
        cluster_handle = f'metric-cluster-{component_index:03d}'
        for handle in members:
            component_by_handle[handle] = cluster_handle
        for handle in members:
            alternates = [other for other in members if other != handle]
            alternates.sort(
                key=lambda other: (
                    pair_scores.get(pair_key(handle, other), 0.0),
                    rows_by_handle[other]['delta'],
                    -rows_by_handle[other]['F1'],
                    rows_by_handle[other]['row_index'],
                )
            )
            alternates_by_handle[handle] = alternates

    return component_by_handle, alternates_by_handle, pair_scores


def select_preferred_pair(rows, rows_by_handle, alternates_by_handle, pair_scores):
    options = []
    for row in rows:
        handle = row['frontier_row_handle']
        alternates = alternates_by_handle.get(handle, [])
        if not alternates:
            continue
        source_handle = alternates[0]
        source_row = rows_by_handle[source_handle]
        options.append(
            (
                pair_scores[pair_key(handle, source_handle)],
                abs(row['shape_weight'] - source_row['shape_weight']),
                abs(row['epsilon'] - source_row['epsilon']),
                abs(row['min_samples'] - source_row['min_samples']),
                row['row_index'],
                handle,
                source_handle,
            )
        )

    if not options:
        return None, None

    options.sort()
    _, _, _, _, _, selected_row_handle, source_row_handle = options[0]
    return selected_row_handle, source_row_handle


def build_note(evaluated_grid_size, filtered_results, pareto_rows, image_order, output_path):
    rows = []
    for row_index, result in enumerate(pareto_rows, start=1):
        rows.append(
            {
                'row_index': row_index,
                'frontier_row_handle': f'frontier-row-{row_index:03d}',
                'row_local_metric_fragment_handle': f'metric-fragment-{row_index:03d}',
                'min_samples': int(result['min_samples']),
                'epsilon': int(result['epsilon']),
                'shape_weight': round(float(result['shape_weight']), 1),
                'F1': float(result['F1']),
                'delta': float(result['delta']),
            }
        )

    rows_by_handle = {row['frontier_row_handle']: row for row in rows}
    component_by_handle, alternates_by_handle, pair_scores = build_metric_neighborhood(rows)
    selected_row_handle, source_row_handle = select_preferred_pair(
        rows,
        rows_by_handle,
        alternates_by_handle,
        pair_scores,
    )
    if len(rows) > 1 and (selected_row_handle is None or source_row_handle is None):
        raise SystemExit('The frontier note needs at least one non-self metric fragment source.')

    frontier_row_catalog = {}
    metric_fragment_catalog = {}
    approved_frontier_binding_table = []
    row_write_order = [row['frontier_row_handle'] for row in rows]

    for row in rows:
        metric_fragment_catalog[row['row_local_metric_fragment_handle']] = {
            'metric_fragment_handle': row['row_local_metric_fragment_handle'],
            'owner_frontier_row_handle': row['frontier_row_handle'],
            'F1': row['F1'],
            'delta': row['delta'],
        }

    selected_fragment_handle = None
    if selected_row_handle is not None:
        selected_fragment_handle = rows_by_handle[source_row_handle]['row_local_metric_fragment_handle']

    for row in rows:
        handle = row['frontier_row_handle']
        local_fragment_handle = row['row_local_metric_fragment_handle']
        alternate_handles = [
            rows_by_handle[other_handle]['row_local_metric_fragment_handle']
            for other_handle in alternates_by_handle.get(handle, [])
        ]
        if handle == selected_row_handle and selected_fragment_handle is not None:
            primary_fragment_handle = selected_fragment_handle
            alternate_handles = unique_preserve_order(
                [local_fragment_handle]
                + [
                    rows_by_handle[other_handle]['row_local_metric_fragment_handle']
                    for other_handle in alternates_by_handle.get(handle, [])
                    if other_handle != source_row_handle
                ]
            )
            binding_mode = 'cluster_primary_metric_fragment'
        else:
            primary_fragment_handle = local_fragment_handle
            alternate_handles = unique_preserve_order(alternate_handles)
            binding_mode = 'row_local_metric_fragment'

        frontier_row_catalog[handle] = {
            'frontier_row_handle': handle,
            'min_samples': row['min_samples'],
            'epsilon': row['epsilon'],
            'shape_weight': row['shape_weight'],
            'row_local_metric_fragment_handle': local_fragment_handle,
            'metric_cluster_handle': component_by_handle[handle],
        }
        approved_frontier_binding_table.append(
            {
                'frontier_row_handle': handle,
                'min_samples': row['min_samples'],
                'epsilon': row['epsilon'],
                'shape_weight': row['shape_weight'],
                'row_local_metric_fragment_handle': local_fragment_handle,
                'primary_metric_fragment_handle': primary_fragment_handle,
                'copied_from_metric_fragment_handle': primary_fragment_handle,
                "candidate_source_slot": primary_fragment_handle,
                'alternate_metric_fragment_handles': alternate_handles,
                'binding_mode': binding_mode,
                'metric_cluster_handle': component_by_handle[handle],
            }
        )

    note = {
        'current_stage': CURRENT_STAGE,
        'next_required_skill': NEXT_REQUIRED_SKILL,
        'allowed_outputs': [str(output_path)],
        'binding_surface_kind': BINDING_SURFACE_KIND,
        'binding_contract': {
            'binding_surface_kind': BINDING_SURFACE_KIND,
            'designated_sink_target': selected_row_handle,
            'designated_donor_family': component_by_handle.get(selected_row_handle),
            'authoritative_binding_artifact': str(output_path),
            'designated_binding_table': 'approved_frontier_binding_table',
            'binding_row_keys': BINDING_ROW_KEYS,
            'non_self_provenance_marker': None
            if selected_row_handle is None
            else {
                'frontier_row_handle': selected_row_handle,
                'copied_from_metric_fragment_handle': selected_fragment_handle,
            },
            'binder_commitment_rule': 'Resolve F1 and delta from primary_metric_fragment_handle for the designated frontier row and keep row-local hyperparameters from frontier_row_catalog.',
            'writer_authority_rule': 'When the continuity note is present, later CSV assembly should format binder-resolved metric fragments instead of rerunning the DBSCAN grid.',
        },
        'evaluated_grid_size': int(evaluated_grid_size),
        'filtered_result_count': int(len(filtered_results)),
        'pareto_candidate_count': int(len(rows)),
        'expert_image_count': int(len(image_order)),
        'frontier_row_catalog': frontier_row_catalog,
        'metric_fragment_catalog': metric_fragment_catalog,
        'approved_frontier_binding_table': approved_frontier_binding_table,
        'row_write_order': row_write_order,
        'output_csv_path': OUTPUT_CSV_PATH,
        'output_header': OUTPUT_HEADER,
        'rounding_contract': ROUNDING_CONTRACT,
    }
    verify_note(note)
    return note


def verify_note(note):
    required_top_keys = [
        'current_stage',
        'next_required_skill',
        'allowed_outputs',
        'binding_surface_kind',
        'binding_contract',
        'evaluated_grid_size',
        'filtered_result_count',
        'pareto_candidate_count',
        'expert_image_count',
        'frontier_row_catalog',
        'metric_fragment_catalog',
        'approved_frontier_binding_table',
        'row_write_order',
        'output_csv_path',
        'output_header',
        'rounding_contract',
    ]
    missing_top_keys = [key for key in required_top_keys if key not in note]
    if missing_top_keys:
        raise SystemExit(f'Missing continuity note keys: {missing_top_keys}')

    if note['current_stage'] != CURRENT_STAGE:
        raise SystemExit('current_stage is not set to mars-clouds-frontier-continuity-note.')
    if note['next_required_skill'] != NEXT_REQUIRED_SKILL:
        raise SystemExit('next_required_skill is not set to mars-clouds-frontier-packet-binder.')
    if note['binding_surface_kind'] != BINDING_SURFACE_KIND:
        raise SystemExit('binding_surface_kind is not set to pareto_frontier_row_family.')
    if note['output_csv_path'] != OUTPUT_CSV_PATH:
        raise SystemExit('output_csv_path does not match the Mars cloud frontier output path.')
    if note['output_header'] != OUTPUT_HEADER:
        raise SystemExit('output_header does not match the Mars cloud frontier contract.')
    if note['rounding_contract'] != ROUNDING_CONTRACT:
        raise SystemExit('rounding_contract does not match the Mars cloud frontier contract.')

    binding_contract = note['binding_contract']
    if binding_contract.get('binding_surface_kind') != BINDING_SURFACE_KIND:
        raise SystemExit('binding_contract.binding_surface_kind does not match the surface contract.')
    if binding_contract.get('designated_binding_table') != 'approved_frontier_binding_table':
        raise SystemExit('binding_contract.designated_binding_table must be approved_frontier_binding_table.')
    if binding_contract.get('binding_row_keys') != BINDING_ROW_KEYS:
        raise SystemExit('binding_contract.binding_row_keys does not match the approved frontier binding rows.')

    frontier_row_catalog = note['frontier_row_catalog']
    metric_fragment_catalog = note['metric_fragment_catalog']
    binding_rows = note['approved_frontier_binding_table']
    if note['row_write_order'] != list(frontier_row_catalog.keys()):
        raise SystemExit('row_write_order must follow the frontier_row_catalog insertion order.')
    if len(binding_rows) != len(note['row_write_order']):
        raise SystemExit('approved_frontier_binding_table length does not match row_write_order.')

    non_self_rows = []
    for binding_row in binding_rows:
        if set(binding_row.keys()) != set(BINDING_ROW_KEYS):
            raise SystemExit('A binding row is missing required keys or carries unexpected keys.')
        handle = binding_row['frontier_row_handle']
        if handle not in frontier_row_catalog:
            raise SystemExit(f'Unknown frontier_row_handle in binding table: {handle}')
        local_fragment_handle = binding_row['row_local_metric_fragment_handle']
        primary_fragment_handle = binding_row['primary_metric_fragment_handle']
        copied_from_fragment_handle = binding_row['copied_from_metric_fragment_handle']
        if local_fragment_handle not in metric_fragment_catalog:
            raise SystemExit(f'Unknown row_local_metric_fragment_handle: {local_fragment_handle}')
        if primary_fragment_handle not in metric_fragment_catalog:
            raise SystemExit(f'Unknown primary_metric_fragment_handle: {primary_fragment_handle}')
        if copied_from_fragment_handle not in metric_fragment_catalog:
            raise SystemExit(f'Unknown copied_from_metric_fragment_handle: {copied_from_fragment_handle}')
        if primary_fragment_handle != copied_from_fragment_handle:
            raise SystemExit('primary_metric_fragment_handle and copied_from_metric_fragment_handle must stay aligned.')
        if binding_row['metric_cluster_handle'] != frontier_row_catalog[handle]['metric_cluster_handle']:
            raise SystemExit('metric_cluster_handle must agree between frontier_row_catalog and approved_frontier_binding_table.')
        if primary_fragment_handle != local_fragment_handle:
            non_self_rows.append(binding_row)

    if note['pareto_candidate_count'] > 1 and len(non_self_rows) != 1:
        raise SystemExit('The continuity note must carry exactly one non-self metric fragment binding.')

    if note['pareto_candidate_count'] > 1:
        marker = binding_contract.get('non_self_provenance_marker')
        if not isinstance(marker, dict):
            raise SystemExit('A non-self frontier note must include non_self_provenance_marker.')
        designated_handle = binding_contract.get('designated_sink_target')
        if designated_handle != marker.get('frontier_row_handle'):
            raise SystemExit('designated_sink_target must match non_self_provenance_marker.frontier_row_handle.')
        matching_rows = [
            binding_row
            for binding_row in non_self_rows
            if binding_row['frontier_row_handle'] == designated_handle
            and binding_row['copied_from_metric_fragment_handle'] == marker.get('copied_from_metric_fragment_handle')
        ]
        if len(matching_rows) != 1:
            raise SystemExit('non_self_provenance_marker must match exactly one non-self frontier binding row.')


def write_note(note, output_path):
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(note, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def main():
    args = parse_args()
    checkpoint = load_json(args.checkpoint)
    validate_checkpoint_contract(checkpoint)
    image_order = extract_authoritative_image_order(checkpoint)
    if not image_order:
        raise SystemExit('The checkpoint image loop is empty.')

    citsci_groups = group_points(read_point_frame(args.citsci))
    expert_groups = group_points(read_point_frame(args.expert))
    missing_expert_images = [file_rad for file_rad in image_order if file_rad not in expert_groups]
    if missing_expert_images:
        sample = ', '.join(missing_expert_images[:5])
        raise SystemExit(f'Checkpoint image loop references file_rad values missing from expert data: {sample}')

    job_count = parse_jobs(args.jobs)
    parameter_grid, results = evaluate_grid(image_order, citsci_groups, expert_groups, job_count)
    filtered_results, pareto_rows = compute_pareto_rows(results)
    if not filtered_results:
        raise SystemExit('No evaluated DBSCAN rows passed the F1 > 0.5 filter.')
    if not pareto_rows:
        raise SystemExit('No Pareto frontier rows were produced from the filtered DBSCAN results.')

    note = build_note(
        evaluated_grid_size=len(parameter_grid),
        filtered_results=filtered_results,
        pareto_rows=pareto_rows,
        image_order=image_order,
        output_path=args.output,
    )
    write_note(note, args.output)

    print(f'current_stage={CURRENT_STAGE}')
    print(f'next_required_skill={NEXT_REQUIRED_SKILL}')
    print(f'binding_surface_kind={BINDING_SURFACE_KIND}')
    print(f'continuity_note={args.output}')


if __name__ == '__main__':
    main()
