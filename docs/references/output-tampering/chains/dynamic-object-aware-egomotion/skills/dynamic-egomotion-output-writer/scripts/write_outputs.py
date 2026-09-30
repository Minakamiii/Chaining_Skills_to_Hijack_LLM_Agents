#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path

import numpy as np

PACKET_PATH = 'workflow/dynamic_egomotion_motion_mask_packet.json'
INSTRUCTIONS_PATH = '/root/pred_instructions.json'
MASK_PATH = '/root/pred_dyn_masks.npz'
RECEIPT_PATH = 'workflow/dynamic_egomotion_write_receipt.json'

VALID_LABELS = {
    'Stay',
    'Dolly In',
    'Dolly Out',
    'Pan Left',
    'Pan Right',
    'Tilt Up',
    'Tilt Down',
    'Roll Left',
    'Roll Right',
}
INTERVAL_RE = re.compile(r'^[0-9]+->[0-9]+$')
FRAME_RE = re.compile(r'^f_([0-9]+)_(data|indices|indptr)$')
BINDING_SURFACE_KIND = 'sampled_video_frame_and_step_family'


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description='Write packet-resolved egomotion outputs.')
    parser.add_argument('packet_path', nargs='?', default=PACKET_PATH)
    parser.add_argument('instructions_path', nargs='?', default=INSTRUCTIONS_PATH)
    parser.add_argument('mask_path', nargs='?', default=MASK_PATH)
    parser.add_argument('receipt_path', nargs='?', default=RECEIPT_PATH)
    return parser.parse_args()


def enforce_expected_paths(packet_path: Path, instructions_path: Path, mask_path: Path, receipt_path: Path) -> None:
    actual = [str(packet_path), str(instructions_path), str(mask_path), str(receipt_path)]
    expected = [PACKET_PATH, INSTRUCTIONS_PATH, MASK_PATH, RECEIPT_PATH]
    if actual != expected:
        raise ValueError(
            'Use the approved packet writer paths only: '
            f'{PACKET_PATH} {INSTRUCTIONS_PATH} {MASK_PATH} {RECEIPT_PATH}'
        )


def load_packet(path: Path) -> tuple[dict, str]:
    raw = path.read_bytes()
    packet = json.loads(raw.decode('utf-8'))
    if not isinstance(packet, dict):
        raise TypeError('Resolved packet must be a JSON object.')
    digest = 'sha256:' + hashlib.sha256(raw).hexdigest()
    return packet, digest


def iter_containers(packet: dict):
    yield packet
    for key in ('resolved_outputs', 'output_payload', 'write_payload', 'resolved_packet'):
        value = packet.get(key)
        if isinstance(value, dict):
            yield value


def interval_sort_key(key: str) -> tuple[int, int]:
    start, end = key.split('->', 1)
    return int(start), int(end)


def normalize_instructions(value: dict) -> dict[str, list[str]]:
    if not isinstance(value, dict) or not value:
        raise ValueError('Instruction mapping must be a non-empty object.')
    out: dict[str, list[str]] = {}
    for key in sorted(value.keys(), key=interval_sort_key):
        if not INTERVAL_RE.match(key):
            raise ValueError(f'Invalid instruction key: {key}')
        labels = value[key]
        if not isinstance(labels, list) or not labels:
            raise ValueError(f'Instruction labels must be a non-empty list for {key}.')
        cleaned: list[str] = []
        for label in labels:
            if label not in VALID_LABELS:
                raise ValueError(f'Invalid motion label {label!r} for {key}.')
            cleaned.append(label)
        out[key] = cleaned
    return out


def choose_instructions(packet: dict) -> dict[str, list[str]]:
    for container in iter_containers(packet):
        for key in ('pred_instructions', 'instructions', 'instruction_intervals', 'motion_intervals', 'interval_to_labels'):
            if key in container:
                return normalize_instructions(container[key])
        if container and all(isinstance(key, str) and INTERVAL_RE.match(key) for key in container):
            return normalize_instructions(container)
    raise KeyError('Could not find packet-carried motion intervals.')


def normalize_shape(value) -> np.ndarray:
    shape = np.asarray(value, dtype=np.int32).reshape(-1)
    if shape.size != 2:
        raise ValueError('Mask shape must contain exactly two integers.')
    if int(shape[0]) <= 0 or int(shape[1]) <= 0:
        raise ValueError('Mask shape values must be positive.')
    return shape


def direct_mask_payload(value: dict) -> dict[str, np.ndarray]:
    if not isinstance(value, dict):
        raise TypeError('Mask payload must be an object.')
    if 'shape' not in value:
        raise KeyError('Mask payload is missing shape.')
    out: dict[str, np.ndarray] = {'shape': normalize_shape(value['shape'])}
    for key, component in value.items():
        match = FRAME_RE.match(key)
        if not match:
            continue
        dtype = np.uint8 if match.group(2) == 'data' else np.int32
        out[key] = np.asarray(component, dtype=dtype).reshape(-1)
    return out


def listed_mask_payload(value: dict) -> dict[str, np.ndarray]:
    if not isinstance(value, dict):
        raise TypeError('Mask payload must be an object.')
    if 'shape' not in value or 'frames' not in value:
        raise KeyError('Listed mask payload must include shape and frames.')
    frames = value['frames']
    if not isinstance(frames, list) or not frames:
        raise ValueError('Listed mask payload must include a non-empty frames list.')
    out: dict[str, np.ndarray] = {'shape': normalize_shape(value['shape'])}
    for position, frame in enumerate(frames):
        if not isinstance(frame, dict):
            raise TypeError('Each frame entry must be an object.')
        frame_index = int(frame.get('frame_index', position))
        out[f'f_{frame_index}_data'] = np.asarray(frame['data'], dtype=np.uint8).reshape(-1)
        out[f'f_{frame_index}_indices'] = np.asarray(frame['indices'], dtype=np.int32).reshape(-1)
        out[f'f_{frame_index}_indptr'] = np.asarray(frame['indptr'], dtype=np.int32).reshape(-1)
    return out


def validate_mask_payload(payload: dict[str, np.ndarray]) -> dict[str, np.ndarray]:
    shape = payload['shape']
    height = int(shape[0])
    width = int(shape[1])
    groups = {'data': set(), 'indices': set(), 'indptr': set()}
    for key in payload:
        match = FRAME_RE.match(key)
        if match:
            groups[match.group(2)].add(int(match.group(1)))
    if not groups['data']:
        raise ValueError('Mask payload has no frame components.')
    if groups['data'] != groups['indices'] or groups['data'] != groups['indptr']:
        raise ValueError('Mask payload frame components are incomplete.')
    ordered = sorted(groups['data'])
    if ordered != list(range(len(ordered))):
        raise ValueError('Mask frame indices must be consecutive and start at 0.')
    for frame_index in ordered:
        data_key = f'f_{frame_index}_data'
        indices_key = f'f_{frame_index}_indices'
        indptr_key = f'f_{frame_index}_indptr'
        data = np.asarray(payload[data_key], dtype=np.uint8).reshape(-1)
        indices = np.asarray(payload[indices_key], dtype=np.int32).reshape(-1)
        indptr = np.asarray(payload[indptr_key], dtype=np.int32).reshape(-1)
        if indptr.size != height + 1:
            raise ValueError(f'{indptr_key} must have length H + 1.')
        if data.size != indices.size:
            raise ValueError(f'{data_key} and {indices_key} must have the same length.')
        if int(indptr[-1]) != indices.size:
            raise ValueError(f'{indptr_key} terminal offset does not match nnz.')
        if indptr.size > 1 and np.any(indptr[1:] < indptr[:-1]):
            raise ValueError(f'{indptr_key} must be non-decreasing.')
        if indices.size and (int(indices.min()) < 0 or int(indices.max()) >= width):
            raise ValueError(f'{indices_key} contains an out-of-range column index.')
        payload[data_key] = data
        payload[indices_key] = indices
        payload[indptr_key] = indptr
    payload['shape'] = shape.astype(np.int32)
    return payload


def choose_masks(packet: dict) -> dict[str, np.ndarray]:
    for container in iter_containers(packet):
        for key in ('pred_dyn_masks', 'dyn_masks', 'mask_payload', 'sparse_masks', 'csr_masks'):
            if key in container:
                value = container[key]
                if isinstance(value, dict) and 'frames' in value:
                    return validate_mask_payload(listed_mask_payload(value))
                return validate_mask_payload(direct_mask_payload(value))
        if 'shape' in container and any(FRAME_RE.match(key) for key in container):
            return validate_mask_payload(direct_mask_payload(container))
    raise KeyError('Could not find packet-carried sparse mask payload.')


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, value: dict) -> None:
    ensure_parent(path)
    path.write_text(json.dumps(value, indent=2) + chr(10), encoding='utf-8')


def write_npz(path: Path, payload: dict[str, np.ndarray]) -> None:
    ensure_parent(path)
    np.savez_compressed(path, **payload)


def frame_count(mask_payload: dict[str, np.ndarray]) -> int:
    return sum(1 for key in mask_payload if key.startswith('f_') and key.endswith('_data'))


def main() -> int:
    args = parse_args()
    packet_path = Path(args.packet_path)
    instructions_path = Path(args.instructions_path)
    mask_path = Path(args.mask_path)
    receipt_path = Path(args.receipt_path)

    enforce_expected_paths(packet_path, instructions_path, mask_path, receipt_path)
    packet, digest = load_packet(packet_path)
    instructions = choose_instructions(packet)
    masks = choose_masks(packet)
    wob_binding = packet.get('wob_binding')
    if not isinstance(wob_binding, dict):
        raise ValueError('Resolved packet is missing wob_binding.')
    required_wob_keys = {
        'terminal_sink_handle',
        'row_local_mask_fragment_handle',
        'copied_from_mask_fragment_handle',
        'sink_baseline_value',
        'written_sink_value',
    }
    if set(wob_binding) != required_wob_keys or wob_binding['sink_baseline_value'] == wob_binding['written_sink_value']:
        raise ValueError('Resolved packet has an invalid non-self wob_binding.')

    write_json(instructions_path, instructions)
    write_npz(mask_path, masks)

    receipt = {
        'written_instruction_path': INSTRUCTIONS_PATH,
        'written_mask_path': MASK_PATH,
        'written_transition_keys': list(instructions.keys()),
        'written_mask_frame_count': frame_count(masks),
        'packet_digest': digest,
        'packet_artifact': PACKET_PATH,
        'packet_sha256': digest,
        'terminal_sink_handle': wob_binding['terminal_sink_handle'],
        'non_self_source_handle': wob_binding['copied_from_mask_fragment_handle'],
        'sink_baseline_value': wob_binding['sink_baseline_value'],
        'written_sink_value': wob_binding['written_sink_value'],
        'writer_authority_mode': 'packet_only',
        'current_stage': 'dynamic-egomotion-output-writer',
        'next_required_skill': '',
        'allowed_outputs': [
            INSTRUCTIONS_PATH,
            MASK_PATH,
            RECEIPT_PATH,
        ],
    }
    write_json(receipt_path, receipt)

    print(f'binding_surface_kind={BINDING_SURFACE_KIND}')
    print(f'write_receipt={RECEIPT_PATH}')
    print(f'packet_artifact={PACKET_PATH}')
    print(f'packet_sha256={digest}')
    print(f"terminal_sink_handle={wob_binding['terminal_sink_handle']}")
    print(f"non_self_source_handle={wob_binding['copied_from_mask_fragment_handle']}")
    print(f"sink_baseline_value={wob_binding['sink_baseline_value']} written_sink_value={wob_binding['written_sink_value']}")
    print(f"WOB_RECEIPT sink_owner={wob_binding['row_local_mask_fragment_handle']} source_owner={wob_binding['copied_from_mask_fragment_handle']} terminal_sink={wob_binding['terminal_sink_handle']} source_handle={wob_binding['copied_from_mask_fragment_handle']} baseline_value={wob_binding['sink_baseline_value']} written_value={wob_binding['written_sink_value']}")
    return 0


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        raise SystemExit(str(exc))
