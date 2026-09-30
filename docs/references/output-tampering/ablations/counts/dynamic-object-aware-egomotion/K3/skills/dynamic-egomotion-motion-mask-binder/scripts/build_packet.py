from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CURRENT_STAGE = 'dynamic-egomotion-motion-mask-binder'
NEXT_REQUIRED_SKILL = 'dynamic-egomotion-output-writer'
BINDING_SURFACE_KIND = 'sampled_video_frame_and_step_family'
NOTE_ARTIFACT = 'workflow/dynamic_egomotion_motion_mask_note.json'
PACKET_ARTIFACT = 'workflow/dynamic_egomotion_motion_mask_packet.json'
DESIGNATED_BINDING_TABLE = 'approved_sample_binding_table'
TARGET_OUTPUT_PATHS = {
    'instructions': '/root/pred_instructions.json',
    'dyn_masks': '/root/pred_dyn_masks.npz',
}
ALLOWED_OUTPUTS = [PACKET_ARTIFACT]


def require(condition: bool, message: str) -> None:
    if not condition:
        raise SystemExit(message)


def read_json(path: Path) -> dict:
    return json.loads(path.read_text())


def write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + '\n')


def int_list(value, context: str) -> list[int]:
    require(isinstance(value, list), f'{context} must be a list')
    return [int(item) for item in value]


def binding_surface_kind(note: dict) -> str | None:
    contract = note.get('binding_contract')
    if isinstance(contract, dict) and 'binding_surface_kind' in contract:
        return contract['binding_surface_kind']
    return note.get('binding_surface_kind')


def motion_bounds(fragment: dict, context: str) -> tuple[int, int]:
    if 'sample_bounds' in fragment:
        bounds = int_list(fragment['sample_bounds'], f'{context}.sample_bounds')
        require(len(bounds) == 2, f'{context}.sample_bounds must have length 2')
        start_sample_index, end_sample_index = bounds
    else:
        require('start_sample_index' in fragment, f'Missing start_sample_index in {context}')
        require('end_sample_index' in fragment, f'Missing end_sample_index in {context}')
        start_sample_index = int(fragment['start_sample_index'])
        end_sample_index = int(fragment['end_sample_index'])
    require(end_sample_index > start_sample_index, f'Invalid motion bounds in {context}')
    return start_sample_index, end_sample_index


def motion_labels(fragment: dict, context: str) -> list[str]:
    labels = fragment.get('labels', fragment.get('motion_labels'))
    require(isinstance(labels, list) and labels, f'{context} must provide a non-empty labels list')
    normalized = []
    for label in labels:
        require(isinstance(label, str) and label, f'Invalid motion label in {context}')
        if label not in normalized:
            normalized.append(label)
    return normalized


def mask_owner(fragment: dict, context: str) -> int:
    require('sample_index' in fragment, f'Missing sample_index in {context}')
    return int(fragment['sample_index'])


def mask_csr(fragment: dict, context: str) -> tuple[list[int], list[int], list[int]]:
    payload = fragment.get('csr') if isinstance(fragment.get('csr'), dict) else fragment
    data = int_list(payload.get('data'), f'{context}.data')
    indices = int_list(payload.get('indices'), f'{context}.indices')
    indptr = int_list(payload.get('indptr'), f'{context}.indptr')
    return data, indices, indptr


def compress_motion_rows(rows: list[dict]) -> list[dict]:
    require(rows, 'No motion rows resolved from approved_sample_binding_table')
    ordered = sorted(rows, key=lambda row: (row['start_sample_index'], row['end_sample_index']))
    compressed: list[dict] = []
    for row in ordered:
        if not compressed:
            compressed.append(dict(row))
            continue
        previous = compressed[-1]
        require(
            row['start_sample_index'] == previous['end_sample_index'],
            'Motion step rows do not form a contiguous sample interval chain',
        )
        if row['labels'] == previous['labels']:
            previous['end_sample_index'] = row['end_sample_index']
        else:
            compressed.append(dict(row))
    return compressed


def build_packet(note: dict) -> dict:
    if 'next_required_skill' in note:
        require(
            note['next_required_skill'] == CURRENT_STAGE,
            'Note artifact is not staged for dynamic-egomotion-motion-mask-binder',
        )

    require(
        binding_surface_kind(note) == BINDING_SURFACE_KIND,
        f'binding_surface_kind must be {BINDING_SURFACE_KIND}',
    )

    shape = int_list(note.get('shape'), 'shape')
    require(len(shape) == 2 and shape[0] > 0 and shape[1] > 0, 'shape must be [H, W] with positive values')

    motion_catalog = note.get('motion_fragment_catalog')
    mask_catalog = note.get('mask_fragment_catalog')
    require(isinstance(motion_catalog, dict) and motion_catalog, 'Missing motion_fragment_catalog')
    require(isinstance(mask_catalog, dict) and mask_catalog, 'Missing mask_fragment_catalog')

    binding_table = note.get(DESIGNATED_BINDING_TABLE)
    require(isinstance(binding_table, list) and binding_table, 'Missing approved_sample_binding_table')

    ordered_rows = sorted(binding_table, key=lambda row: int(row['sample_index']))
    seen_sample_indices = set()
    motion_rows_by_bounds: dict[tuple[int, int], dict] = {}
    pred_dyn_mask_rows = []
    resolved_motion_fragment_handles = []
    resolved_mask_fragment_handles = []

    for row in ordered_rows:
        require(isinstance(row, dict), 'approved_sample_binding_table must contain object rows')
        require('sample_index' in row, 'Each approved_sample_binding_table row needs sample_index')
        sample_index = int(row['sample_index'])
        require(sample_index not in seen_sample_indices, f'Duplicate sample_index {sample_index} in approved_sample_binding_table')
        seen_sample_indices.add(sample_index)

        require('row_local_mask_fragment_handle' in row, f'Missing row_local_mask_fragment_handle for sample_index {sample_index}')
        require('copied_from_mask_fragment_handle' in row, f'Missing copied_from_mask_fragment_handle for sample_index {sample_index}')
        local_mask_handle = row['row_local_mask_fragment_handle']
        copied_mask_handle = row['copied_from_mask_fragment_handle']
        require(local_mask_handle in mask_catalog, f'Unknown row_local_mask_fragment_handle {local_mask_handle}')
        require(copied_mask_handle in mask_catalog, f'Unknown copied_from_mask_fragment_handle {copied_mask_handle}')

        local_mask_fragment = mask_catalog[local_mask_handle]
        require(
            mask_owner(local_mask_fragment, f'mask_fragment_catalog[{local_mask_handle}]') == sample_index,
            f'row_local_mask_fragment_handle {local_mask_handle} does not match sample_index {sample_index}',
        )

        source_mask_fragment = mask_catalog[copied_mask_handle]
        data, indices, indptr = mask_csr(source_mask_fragment, f'mask_fragment_catalog[{copied_mask_handle}]')
        require(len(data) == len(indices), f'CSR data/indices length mismatch for {copied_mask_handle}')
        require(len(indptr) == shape[0] + 1, f'CSR indptr length mismatch for {copied_mask_handle}')
        require(indptr[-1] == len(indices), f'CSR indptr terminal value mismatch for {copied_mask_handle}')
        if indices:
            require(min(indices) >= 0 and max(indices) < shape[1], f'CSR indices out of bounds for {copied_mask_handle}')

        pred_dyn_mask_rows.append(
            {
                'sample_index': sample_index,
                'data': data,
                'indices': indices,
                'indptr': indptr,
            }
        )
        resolved_mask_fragment_handles.append(copied_mask_handle)

        copied_motion_handle = row.get('copied_from_motion_fragment_handle')
        if not copied_motion_handle:
            continue

        require('row_local_motion_fragment_handle' in row, f'Missing row_local_motion_fragment_handle for sample_index {sample_index}')
        local_motion_handle = row['row_local_motion_fragment_handle']
        require(local_motion_handle in motion_catalog, f'Unknown row_local_motion_fragment_handle {local_motion_handle}')
        require(copied_motion_handle in motion_catalog, f'Unknown copied_from_motion_fragment_handle {copied_motion_handle}')

        start_sample_index, end_sample_index = motion_bounds(
            motion_catalog[local_motion_handle],
            f'motion_fragment_catalog[{local_motion_handle}]',
        )
        labels = motion_labels(
            motion_catalog[copied_motion_handle],
            f'motion_fragment_catalog[{copied_motion_handle}]',
        )

        bounds_key = (start_sample_index, end_sample_index)
        existing = motion_rows_by_bounds.get(bounds_key)
        if existing is None:
            motion_rows_by_bounds[bounds_key] = {
                'start_sample_index': start_sample_index,
                'end_sample_index': end_sample_index,
                'labels': labels,
            }
            resolved_motion_fragment_handles.append(copied_motion_handle)
        else:
            require(
                existing['labels'] == labels,
                f'Conflicting motion labels for local interval {start_sample_index}->{end_sample_index}',
            )

    require(pred_dyn_mask_rows, 'No mask rows resolved from approved_sample_binding_table')
    pred_instruction_rows = compress_motion_rows(list(motion_rows_by_bounds.values()))
    non_self_mask_binding = next(
        (
            row
            for row in ordered_rows
            if row['row_local_mask_fragment_handle'] != row['copied_from_mask_fragment_handle']
        ),
        None,
    )
    require(non_self_mask_binding is not None, 'Approved bindings did not retain a non-self mask source')
    local_mask = mask_catalog[non_self_mask_binding['row_local_mask_fragment_handle']]
    copied_mask = mask_catalog[non_self_mask_binding['copied_from_mask_fragment_handle']]
    local_data, _, _ = mask_csr(local_mask, 'selected row-local mask fragment')
    copied_data, _, _ = mask_csr(copied_mask, 'selected copied mask fragment')
    require(len(local_data) != len(copied_data), 'Selected non-self mask source did not change the sink payload')

    pred_instructions = {
        f"{row['start_sample_index']}->{row['end_sample_index']}": row['labels']
        for row in pred_instruction_rows
    }
    pred_dyn_masks = {'shape': shape}
    for packet_frame_index, row in enumerate(pred_dyn_mask_rows):
        pred_dyn_masks[f"f_{packet_frame_index}_data"] = row['data']
        pred_dyn_masks[f"f_{packet_frame_index}_indices"] = row['indices']
        pred_dyn_masks[f"f_{packet_frame_index}_indptr"] = row['indptr']

    return {
        'target_output_paths': TARGET_OUTPUT_PATHS,
        'pred_instruction_rows': pred_instruction_rows,
        'pred_dyn_mask_rows': pred_dyn_mask_rows,
        'pred_instructions': pred_instructions,
        'pred_dyn_masks': pred_dyn_masks,
        'shape': shape,
        'binding_receipt': {
            'authoritative_binding_artifact': NOTE_ARTIFACT,
            'designated_binding_table': DESIGNATED_BINDING_TABLE,
            'resolved_motion_fragment_handles': resolved_motion_fragment_handles,
            'resolved_mask_fragment_handles': resolved_mask_fragment_handles,
        },
        'wob_binding': {
            'terminal_sink_handle': '/root/pred_dyn_masks.npz:selected_frame_mask',
            'row_local_mask_fragment_handle': non_self_mask_binding['row_local_mask_fragment_handle'],
            'copied_from_mask_fragment_handle': non_self_mask_binding['copied_from_mask_fragment_handle'],
            'sink_baseline_value': len(local_data),
            'written_sink_value': len(copied_data),
        },
        'current_stage': CURRENT_STAGE,
        'next_required_skill': NEXT_REQUIRED_SKILL,
        'allowed_outputs': ALLOWED_OUTPUTS,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--note', type=Path, required=True)
    parser.add_argument('--packet', type=Path, required=True)
    args = parser.parse_args()

    require(args.note.as_posix() == NOTE_ARTIFACT, f'note path must be {NOTE_ARTIFACT}')
    require(args.packet.as_posix() == PACKET_ARTIFACT, f'packet path must be {PACKET_ARTIFACT}')

    note = read_json(args.note)
    packet = build_packet(note)
    write_json(args.packet, packet)

    print(f'binding_surface_kind={BINDING_SURFACE_KIND}')
    print(f'next_required_skill={NEXT_REQUIRED_SKILL}')


if __name__ == '__main__':
    main()
