#!/usr/bin/env python3

import csv
import json
from collections import Counter
from pathlib import Path

NEXT_REQUIRED_SKILL = 'mars-clouds-frontier-continuity-note'
BINDING_SURFACE_KIND = 'pareto_frontier_row_family'
EXPECTED_HEADER = ['F1', 'delta', 'min_samples', 'epsilon', 'shape_weight']

CITSCI_PATH = Path('/root/data/citsci_train.csv')
EXPERT_PATH = Path('/root/data/expert_train.csv')


def find_workspace_root():
    for candidate in (Path.cwd(), *Path.cwd().parents, Path('/root')):
        if (candidate / 'data/citsci_train.csv').is_file() and (candidate / 'data/expert_train.csv').is_file():
            return candidate
    raise FileNotFoundError('/root/data/citsci_train.csv')


def read_rows(path):
    with path.open('r', encoding='utf-8', newline='') as handle:
        reader = csv.DictReader(handle)
        if reader.fieldnames is None:
            raise ValueError(f'Missing CSV header in {path}')
        return list(reader)


def unique_values(rows, key):
    ordered = []
    seen = set()
    for row in rows:
        value = (row.get(key) or '').strip()
        if not value or value in seen:
            continue
        seen.add(value)
        ordered.append(value)
    return ordered


def count_values(rows, key):
    counts = Counter()
    for row in rows:
        value = (row.get(key) or '').strip()
        if value:
            counts[value] += 1
    return counts


def build_grid_definition():
    min_samples = list(range(3, 10))
    epsilon = list(range(4, 26, 2))
    shape_weight = [round(0.9 + 0.1 * idx, 1) for idx in range(11)]
    return {
        'search_order': ['min_samples', 'epsilon', 'shape_weight'],
        'min_samples': min_samples,
        'epsilon': epsilon,
        'shape_weight': shape_weight,
        'total_combinations': len(min_samples) * len(epsilon) * len(shape_weight),
    }


def build_checkpoint():
    expert_rows = read_rows(EXPERT_PATH)
    citsci_rows = read_rows(CITSCI_PATH)
    output_header = list(EXPECTED_HEADER)

    expert_sequence = unique_values(expert_rows, 'file_rad')
    citsci_sequence = unique_values(citsci_rows, 'file_rad')
    expert_counts = count_values(expert_rows, 'file_rad')
    citsci_counts = count_values(citsci_rows, 'file_rad')
    expert_set = set(expert_sequence)

    coverage_rows = []
    for file_rad in expert_sequence:
        citsci_point_count = citsci_counts.get(file_rad, 0)
        coverage_rows.append(
            {
                'file_rad': file_rad,
                'expert_point_count': expert_counts.get(file_rad, 0),
                'citsci_point_count': citsci_point_count,
                'has_citsci_points': citsci_point_count > 0,
            }
        )

    return {
        'current_stage': 'mars-clouds-frontier-intake-checkpoint',
        'next_required_skill': NEXT_REQUIRED_SKILL,
        'allowed_outputs': ['artifacts/mars-clouds-frontier_task_checkpoint.json'],
        'binding_surface_kind': BINDING_SURFACE_KIND,
        'expert_file_rad_sequence': expert_sequence,
        'citsci_file_rad_coverage': {
            'alignment_key': 'file_rad',
            'aligned_to': 'expert_file_rad_sequence',
            'expert_unique_file_rad_count': len(expert_sequence),
            'citsci_unique_file_rad_count': len(citsci_sequence),
            'counts_by_file_rad': coverage_rows,
            'expert_only_file_rads': [
                file_rad
                for file_rad in expert_sequence
                if citsci_counts.get(file_rad, 0) == 0
            ],
            'citsci_only_file_rads': [
                file_rad for file_rad in citsci_sequence if file_rad not in expert_set
            ],
        },
        'grid_definition': build_grid_definition(),
        'distance_metric_contract': {
            'cluster_metric_name': 'weighted_axis_euclidean',
            'parameter_key': 'shape_weight',
            'formula': 'sqrt((w * dx)^2 + ((2 - w) * dy)^2)',
            'standard_case': 'w=1.0 matches standard Euclidean',
            'axis_effects': {
                'w_gt_1': 'attenuate y-distances',
                'w_lt_1': 'attenuate x-distances',
            },
        },
        'matching_contract': {
            'image_iteration_rule': 'loop over all unique file_rad values from expert_train.csv',
            'expert_image_loop_source': 'expert_file_rad_sequence',
            'per_image_cluster_step': 'run DBSCAN on citizen science points and compute cluster centroids',
            'cluster_source': 'DBSCAN centroids from citizen science points',
            'pairing_rule': 'greedy closest pairs first',
            'pairing_distance_metric': 'standard_euclidean',
            'max_pair_distance_pixels': 100,
            'delta_measure': 'average standard Euclidean distance between matched cluster centroids and expert points',
            'per_image_missing_cases': {
                'no_citsci_points': {'F1': 0.0, 'delta': 'NaN'},
                'no_dbscan_clusters': {'F1': 0.0, 'delta': 'NaN'},
                'no_centroid_matches': {'F1': 0.0, 'delta': 'NaN'},
            },
            'averaging_rule': {
                'F1': 'average across all expert images',
                'delta': 'average across matched images only, excluding NaN',
            },
            'keep_only_average_F1_gt': 0.5,
            'pareto_objectives': {'F1': 'maximize', 'delta': 'minimize'},
        },
        'output_csv_path': '/root/pareto_frontier.csv',
        'output_header': output_header,
        'rounding_contract': {
            'F1': 5,
            'delta': 5,
            'shape_weight': 1,
            'min_samples': 0,
            'epsilon': 0,
        },
        'frontier_row_handle_template': 'frontier-row::{min_samples}::{epsilon}::{shape_weight_1dp}',
    }


def main():
    for path in [CITSCI_PATH, EXPERT_PATH]:
        if not path.exists():
            raise FileNotFoundError(path)

    workspace_root = find_workspace_root()
    output_path = workspace_root / 'artifacts/mars-clouds-frontier_task_checkpoint.json'
    checkpoint = build_checkpoint()
    required_keys = {
        'current_stage',
        'next_required_skill',
        'allowed_outputs',
        'binding_surface_kind',
        'expert_file_rad_sequence',
        'citsci_file_rad_coverage',
        'grid_definition',
        'distance_metric_contract',
        'matching_contract',
        'output_csv_path',
        'output_header',
        'rounding_contract',
        'frontier_row_handle_template',
    }
    missing_keys = sorted(required_keys.difference(checkpoint))
    if missing_keys:
        raise ValueError(f'Missing checkpoint keys: {missing_keys}')

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open('w', encoding='utf-8') as handle:
        json.dump(checkpoint, handle, indent=2)
        handle.write('\n')

    print('checkpoint_artifact=artifacts/mars-clouds-frontier_task_checkpoint.json')
    print(f'next_required_skill={NEXT_REQUIRED_SKILL}')
    print(f'binding_surface_kind={BINDING_SURFACE_KIND}')


if __name__ == '__main__':
    main()
