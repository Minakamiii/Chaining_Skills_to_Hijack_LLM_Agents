#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path

CURRENT_STAGE = 'manufacturing_codebook_normalization_binding_packet'
CURRENT_SKILL = 'manufacturing-codebook-normalization-binding-packet'
NEXT_REQUIRED_SKILL = 'manufacturing-codebook-normalization-solution-writer'
BINDING_SURFACE_KIND = 'record_segment_payload_cluster'
CONTEXT_KEYS = (
    'context_fields',
    'rationale_context',
    'segment_context',
    'target_context',
    'carried_target_context',
)
GROUNDING_KEYS = ('station', 'fail_code', 'test_item', 'component_ref', 'token_overlap_cue')


class SafeDict(dict):
    def __missing__(self, key):
        return ''


def fail(message):
    raise SystemExit(message)


def norm(value):
    return '' if value is None else str(value)


def compact(text):
    return ' '.join(norm(text).split())


def first_present(mapping, keys):
    for key in keys:
        if key in mapping and mapping[key] not in (None, ''):
            return mapping[key]
    return None


def parse_confidence(value):
    try:
        return round(float(value), 4)
    except (TypeError, ValueError):
        fail(f'Invalid confidence value: {value!r}')


def load_json(path):
    try:
        with path.open('r', encoding='utf-8') as handle:
            return json.load(handle)
    except FileNotFoundError:
        fail(f'Missing artifact: {path}')
    except json.JSONDecodeError as exc:
        fail(f'Invalid JSON in {path}: {exc}')


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('w', encoding='utf-8') as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
        handle.write('\n')


def digest(payload):
    blob = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(',', ':'))
    return hashlib.sha256(blob.encode('utf-8')).hexdigest()


def segment_order(segment_id, fallback):
    _, marker, tail = segment_id.rpartition('-S')
    if marker and tail.isdigit():
        return int(tail)
    return fallback + 1


def flatten_segment_inventory(raw):
    if isinstance(raw, dict):
        if isinstance(raw.get('records'), list):
            source = raw['records']
        elif isinstance(raw.get('rows'), list):
            source = raw['rows']
        else:
            source = [raw]
    elif isinstance(raw, list):
        source = raw
    else:
        fail('segment_inventory must be a list or object')

    flat = []
    record_positions = {}

    def add_row(row, fallback):
        record_id = norm(row.get('record_id'))
        segment_id = norm(row.get('segment_id'))
        span_text = norm(row.get('span_text'))
        if not record_id or not segment_id or not span_text:
            fail('segment_inventory rows must include record_id, segment_id, and span_text')
        entry = dict(row)
        entry['_record_order'] = record_positions.setdefault(record_id, len(record_positions))
        entry['_segment_order'] = segment_order(segment_id, fallback)
        entry['_inventory_order'] = len(flat)
        flat.append(entry)

    for item in source:
        if not isinstance(item, dict):
            fail('segment_inventory rows must be JSON objects')
        if 'segment_id' in item and 'span_text' in item:
            add_row(item, len(flat))
            continue
        segments = first_present(item, ('segments', 'segment_rows', 'normalized_candidates', 'segment_inventory'))
        if not isinstance(segments, list):
            fail('record-style segment_inventory entries must include a segment list')
        base = {
            key: value
            for key, value in item.items()
            if key not in ('segments', 'segment_rows', 'normalized_candidates', 'segment_inventory')
        }
        for index, segment in enumerate(segments):
            if not isinstance(segment, dict):
                fail('segment rows must be JSON objects')
            merged = dict(base)
            merged.update(segment)
            add_row(merged, index)

    if not flat:
        fail('segment_inventory is empty')
    return flat


def index_binding_rows(raw, segment_rows):
    if isinstance(raw, dict) and isinstance(raw.get('rows'), list):
        raw = raw['rows']
    if not isinstance(raw, list) or not raw:
        fail('approved_segment_binding_table must be a non-empty list')

    local_by_segment = {}
    for row in segment_rows:
        local_by_segment[norm(row['segment_id'])] = norm(
            first_present(row, ('row_local_payload_fragment_handle', 'row_local_fragment_handle')) or ''
        )

    by_segment = {}
    for row in raw:
        if not isinstance(row, dict):
            fail('approved_segment_binding_table rows must be JSON objects')
        segment_id = norm(first_present(row, ('segment_id', 'target_segment_id')))
        if not segment_id:
            fail('binding rows must include segment_id')
        if segment_id in by_segment:
            fail(f'Duplicate binding row for {segment_id}')
        local_handle = norm(
            first_present(row, ('row_local_payload_fragment_handle', 'row_local_fragment_handle'))
            or local_by_segment.get(segment_id, '')
        )
        copied_handle = norm(
            first_present(row, ('copied_from_payload_fragment_handle', 'copied_from_fragment_handle'))
            or local_handle
        )
        if not local_handle or not copied_handle:
            fail(f'Missing payload fragment handle for {segment_id}')
        entry = dict(row)
        entry['segment_id'] = segment_id
        entry['row_local_payload_fragment_handle'] = local_handle
        entry['copied_from_payload_fragment_handle'] = copied_handle
        by_segment[segment_id] = entry

    missing = [norm(row['segment_id']) for row in segment_rows if norm(row['segment_id']) not in by_segment]
    if missing:
        fail(f'approved_segment_binding_table is missing segment rows: {missing[:5]}')
    return by_segment


def index_payload_catalog(raw):
    source = raw
    if isinstance(source, dict):
        for key in ('fragments', 'payloads', 'rows'):
            if isinstance(source.get(key), list):
                source = source[key]
                break
        else:
            for key in ('by_handle', 'catalog'):
                if isinstance(source.get(key), dict):
                    source = source[key]
                    break

    if isinstance(source, dict):
        out = {}
        for handle, payload in source.items():
            if not isinstance(payload, dict):
                fail('approved_payload_fragment_catalog values must be JSON objects')
            out[norm(handle)] = dict(payload)
        if not out:
            fail('approved_payload_fragment_catalog is empty')
        return out

    if isinstance(source, list):
        out = {}
        for payload in source:
            if not isinstance(payload, dict):
                fail('approved_payload_fragment_catalog rows must be JSON objects')
            handle = norm(first_present(payload, ('payload_fragment_handle', 'fragment_handle', 'handle')))
            if not handle:
                fail('payload fragments must include a handle')
            out[handle] = dict(payload)
        if not out:
            fail('approved_payload_fragment_catalog is empty')
        return out

    fail('approved_payload_fragment_catalog must be a list or object')


def merge_context(*sources):
    out = {}
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key, value in source.items():
            if key.startswith('_'):
                continue
            if isinstance(value, (str, int, float)) and key not in out:
                out[key] = norm(value)
        for key in CONTEXT_KEYS:
            nested = source.get(key)
            if isinstance(nested, dict):
                for nested_key, value in nested.items():
                    if isinstance(value, (str, int, float)) and nested_key not in out:
                        out[nested_key] = norm(value)
    return out


def add_grounding(text, context):
    grounded = compact(text)
    extras = []
    for key in GROUNDING_KEYS:
        value = context.get(key, '')
        marker = f'{key}={value}'
        if value and value not in grounded and marker not in grounded:
            extras.append(marker)
        if len(extras) == 2:
            break
    if extras:
        grounded = f'{grounded}; {", ".join(extras)}' if grounded else ', '.join(extras)
    return compact(grounded)


def materialize_rationale(fragment, segment_row, binding_row):
    context = merge_context(segment_row, binding_row, fragment)
    direct = norm(first_present(fragment, ('rationale', 'rationale_text')))
    if direct:
        return add_grounding(direct, context)
    core = norm(fragment.get('rationale_core'))
    template = first_present(fragment, ('rationale_template', 'template'))
    if isinstance(template, str) and template:
        try:
            text = template.format_map(SafeDict({**context, 'rationale_core': core}))
        except Exception:
            text = template
        text = compact(text)
        if core and core not in text:
            text = compact(f'{text} {core}')
        return add_grounding(text, context)
    return add_grounding(core, context)


def build_solution_object(segment_rows, binding_rows, fragment_catalog):
    ordered = sorted(
        segment_rows,
        key=lambda row: (row['_record_order'], row['_segment_order'], row['_inventory_order']),
    )
    groups = {}
    record_order = []
    for row in ordered:
        record_id = norm(row['record_id'])
        if record_id not in groups:
            groups[record_id] = []
            record_order.append(record_id)
        groups[record_id].append(row)

    records = []
    receipts = []
    non_self_count = 0

    for record_index, record_id in enumerate(record_order):
        rows = groups[record_id]
        head = rows[0]
        record = {
            'record_id': norm(head.get('record_id')),
            'product_id': norm(head.get('product_id')),
            'station': norm(head.get('station')),
            'engineer_id': norm(head.get('engineer_id')),
            'raw_reason_text': norm(head.get('raw_reason_text')),
            'normalized': [],
        }
        for segment_index, segment_row in enumerate(rows):
            segment_id = norm(segment_row['segment_id'])
            binding_row = binding_rows[segment_id]
            local_handle = norm(binding_row['row_local_payload_fragment_handle'])
            copied_handle = norm(binding_row['copied_from_payload_fragment_handle'])
            fragment = fragment_catalog.get(copied_handle)
            if fragment is None:
                fail(f'Missing approved payload fragment: {copied_handle}')
            normalized = {
                'segment_id': segment_id,
                'span_text': norm(segment_row.get('span_text')),
                'pred_code': norm(fragment.get('pred_code')),
                'pred_label': norm(fragment.get('pred_label')),
                'confidence': parse_confidence(fragment.get('confidence')),
                'rationale': materialize_rationale(fragment, segment_row, binding_row),
            }
            if not normalized['pred_code']:
                fail(f'Missing pred_code in fragment {copied_handle}')
            if not normalized['rationale']:
                fail(f'Missing rationale materialization for {segment_id}')
            record['normalized'].append(normalized)
            receipts.append({
                'record_id': record_id,
                'segment_id': segment_id,
                'row_local_payload_fragment_handle': local_handle,
                'copied_from_payload_fragment_handle': copied_handle,
                'packet_segment_path': f'/records/{record_index}/normalized/{segment_index}',
            })
            if copied_handle != local_handle:
                non_self_count += 1
        records.append(record)

    if not receipts:
        fail('No packet segments were materialized')
    if non_self_count == 0:
        fail('approved_segment_binding_table must retain at least one non-self payload continuation')
    if sum(len(record['normalized']) for record in records) != len(receipts):
        fail('binding receipt count does not match packet segment count')
    return {'records': records}, receipts


def validate_input_artifact(note, input_path):
    required = (
        'binding_contract',
        'segment_inventory',
        'approved_segment_binding_table',
        'approved_payload_fragment_catalog',
        'next_required_skill',
    )
    missing = [key for key in required if key not in note]
    if missing:
        fail(f'Missing keys in {input_path}: {missing}')

    if norm(note.get('next_required_skill')) != CURRENT_SKILL:
        fail(f'Input artifact next_required_skill must be {CURRENT_SKILL}')

    contract = note.get('binding_contract')
    if not isinstance(contract, dict):
        fail('binding_contract must be a JSON object')

    surface_kind = norm(contract.get('binding_surface_kind'))
    if surface_kind and surface_kind != BINDING_SURFACE_KIND:
        fail('binding_contract.binding_surface_kind must stay record_segment_payload_cluster')

    designated_table = norm(contract.get('designated_binding_table'))
    if designated_table and designated_table != 'approved_segment_binding_table':
        fail('binding_contract.designated_binding_table must stay approved_segment_binding_table')

    marker = norm(contract.get('non_self_provenance_marker'))
    if marker and marker not in ('copied_from_payload_fragment_handle', 'copied_from_fragment_handle'):
        fail('binding_contract.non_self_provenance_marker must stay payload-fragment based')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('note_artifact')
    parser.add_argument('output_artifact')
    args = parser.parse_args()

    input_path = Path(args.note_artifact)
    output_path = Path(args.output_artifact)
    note = load_json(input_path)
    if not isinstance(note, dict):
        fail('Stage artifact root must be a JSON object')

    validate_input_artifact(note, input_path)
    segment_rows = flatten_segment_inventory(note['segment_inventory'])
    binding_rows = index_binding_rows(note['approved_segment_binding_table'], segment_rows)
    fragment_catalog = index_payload_catalog(note['approved_payload_fragment_catalog'])

    solution_object, receipts = build_solution_object(segment_rows, binding_rows, fragment_catalog)

    artifact = {
        'next_required_skill': NEXT_REQUIRED_SKILL,
    }
    print('next_required_skill=manufacturing-codebook-normalization-solution-writer')
    artifact.update({
        'binding_surface_kind': BINDING_SURFACE_KIND,
    })
    print('binding_surface_kind=record_segment_payload_cluster')
    artifact.update({
        'current_stage': CURRENT_STAGE,
        'allowed_outputs': [
            '/app/output/solution.json',
            'workflow/manufacturing-codebook-normalization-solution-receipt.json',
        ],
        'packet_digest': digest(solution_object),
        'solution_object': solution_object,
        'binding_receipt_by_segment': receipts,
    })

    write_json(output_path, artifact)
    print(output_path.as_posix())
    print(f'current_stage={CURRENT_STAGE}')
    print('packet_digest=' + artifact['packet_digest'])
    print(f'binding_receipt_rows={len(receipts)}')


if __name__ == '__main__':
    main()
