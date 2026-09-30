#!/usr/bin/env python3
from __future__ import annotations

import json
import re
import sys
from collections import defaultdict
from pathlib import Path

NEXT_REQUIRED_SKILL = "manufacturing-codebook-normalization-binding-packet"
BINDING_SURFACE_KIND = "record_segment_payload_cluster"

ROW_KEYS = [
    'record_id',
    'segment_id',
    'payload_family_handle',
    'row_local_payload_fragment_handle',
    'copied_from_payload_fragment_handle',
    'alternate_payload_fragment_handles',
    'binding_mode',
]
CATALOG_KEYS = [
    'payload_fragment_handle',
    'product_id',
    'pred_code',
    'pred_label',
    'confidence',
    'rationale_core',
    'rationale_template',
    'required_target_context_fields',
    'source_segment_handle',
]
ARRAY_KEYS = [
    'candidate_payload_fragments',
    'payload_candidates',
    'candidate_matches',
    'candidate_fragments',
    'candidates',
    'normalized_candidates',
    'approved_candidates',
    'payload_fragment_candidates',
]
SINGLE_KEYS = [
    'best_candidate',
    'primary_candidate',
    'selected_candidate',
    'top_candidate',
]
HANDLE_LIST_KEYS = [
    'candidate_fragment_handles',
    'payload_fragment_handles',
    'candidate_handles',
]
TOP_CATALOG_KEYS = [
    'payload_fragment_catalog',
    'candidate_payload_fragment_catalog',
    'segment_payload_fragment_catalog',
    'candidate_payload_fragments',
]


def norm_text(value):
    if value is None:
        return ''
    return str(value).strip()


def as_float(value, default=0.0):
    try:
        return round(float(value), 4)
    except Exception:
        return default


def ensure_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, dict):
        return list(value.values())
    return [value]


def slug(text):
    token = re.sub(r'[^a-z0-9]+', '-', norm_text(text).lower()).strip('-')
    return token or 'blank'


def first_present(mapping, keys, default=''):
    if not isinstance(mapping, dict):
        return default
    for key in keys:
        value = mapping.get(key)
        if value not in (None, ''):
            return value
    return default


def unique(items, skip=None):
    seen = set()
    out = []
    skip = skip or set()
    for item in items:
        token = norm_text(item)
        if not token or token in seen or token in skip:
            continue
        seen.add(token)
        out.append(token)
    return out


def source_segment_handle(segment):
    existing = norm_text(first_present(segment, ['source_segment_handle']))
    if existing:
        return existing
    return f"seg::{norm_text(segment.get('record_id'))}::{norm_text(segment.get('segment_id'))}"


def required_fields(segment):
    fields = []
    for key in ('station', 'test_item', 'fail_code', 'span_text'):
        if norm_text(segment.get(key)):
            fields.append(key)
    return fields or ['span_text']


def build_rationale_core(segment, candidate, pred_label):
    existing = norm_text(first_present(candidate, ['rationale_core', 'rationale', 'reason']))
    parts = []
    for key in ('station', 'test_item', 'fail_code'):
        value = norm_text(first_present(candidate, [key]) or segment.get(key))
        if value:
            parts.append(f'{key}={value}')
    cue = norm_text(first_present(candidate, ['cue_text', 'span_text']) or segment.get('span_text'))
    if cue:
        parts.append(f'cue={cue}')
    if pred_label:
        parts.append(f'family={pred_label}')
    context = '; '.join(parts[:5])
    if existing and context:
        if context in existing:
            return existing
        return f'{context}; {existing}'
    if existing:
        return existing
    return context or 'context=retained'


def build_rationale_template(segment, candidate):
    existing = norm_text(first_present(candidate, ['rationale_template']))
    if existing:
        return existing
    tokens = ['{rationale_core}']
    for key in required_fields(segment):
        if key == 'station':
            tokens.append('target_station={station}')
        elif key == 'test_item':
            tokens.append('target_test_item={test_item}')
        elif key == 'fail_code':
            tokens.append('target_fail_code={fail_code}')
        elif key == 'span_text':
            tokens.append('span={span_text}')
    return '; '.join(tokens)


def collect_top_catalog(document):
    catalog = {}
    for key in TOP_CATALOG_KEYS:
        for row in ensure_list(document.get(key)):
            if not isinstance(row, dict):
                continue
            handle = norm_text(first_present(row, ['payload_fragment_handle', 'candidate_handle', 'fragment_handle', 'handle']))
            if handle:
                catalog[handle] = dict(row)
    return catalog


def candidate_handle(segment, candidate, index):
    handle = norm_text(first_present(candidate, ['payload_fragment_handle', 'candidate_handle', 'fragment_handle', 'handle']))
    if handle:
        return handle
    code_or_label = norm_text(first_present(candidate, ['pred_code', 'code', 'candidate_code', 'pred_label', 'label', 'standard_label']))
    return f"frag::{norm_text(segment.get('segment_id'))}::{index:02d}::{slug(code_or_label)}"


def materialize_candidate(segment, raw_candidate, index, top_catalog):
    if isinstance(raw_candidate, str):
        merged = dict(top_catalog.get(raw_candidate, {}))
        merged.setdefault('payload_fragment_handle', raw_candidate)
    elif isinstance(raw_candidate, dict):
        seed_handle = norm_text(first_present(raw_candidate, ['payload_fragment_handle', 'candidate_handle', 'fragment_handle', 'handle']))
        merged = dict(top_catalog.get(seed_handle, {}))
        merged.update(raw_candidate)
    else:
        return None

    pred_code = norm_text(first_present(merged, ['pred_code', 'code', 'candidate_code', 'selected_code']) or segment.get('pred_code'))
    pred_label = norm_text(first_present(merged, ['pred_label', 'label', 'standard_label', 'selected_label']) or segment.get('pred_label'))
    if not pred_code and not pred_label:
        return None

    handle = candidate_handle(segment, merged, index)
    candidate = {
        'payload_fragment_handle': handle,
        'product_id': norm_text(first_present(merged, ['product_id']) or segment.get('product_id')),
        'pred_code': pred_code,
        'pred_label': pred_label,
        'confidence': as_float(first_present(merged, ['confidence', 'match_score', 'score']), 0.0),
        'rationale_core': build_rationale_core(segment, merged, pred_label),
        'rationale_template': build_rationale_template(segment, merged),
        'required_target_context_fields': required_fields(segment),
        'source_segment_handle': norm_text(first_present(merged, ['source_segment_handle'])) or source_segment_handle(segment),
    }
    return candidate


def extract_candidates(segment, top_catalog):
    raw_candidates = []
    for key in ARRAY_KEYS:
        value = segment.get(key)
        if isinstance(value, list):
            raw_candidates.extend(value)
    for key in SINGLE_KEYS:
        value = segment.get(key)
        if isinstance(value, dict):
            raw_candidates.append(value)
    for key in HANDLE_LIST_KEYS:
        value = segment.get(key)
        if isinstance(value, list):
            raw_candidates.extend(value)

    if not raw_candidates:
        if norm_text(segment.get('pred_code')) or norm_text(segment.get('pred_label')):
            raw_candidates.append(segment)

    candidates = []
    seen = set()
    for index, raw_candidate in enumerate(raw_candidates, start=1):
        candidate = materialize_candidate(segment, raw_candidate, index, top_catalog)
        if not candidate:
            continue
        handle = candidate['payload_fragment_handle']
        if handle in seen:
            continue
        seen.add(handle)
        candidates.append(candidate)
    return candidates


def family_handle(product_id, pred_label, pred_code):
    basis = pred_label or pred_code or 'payload'
    return f'pfam::{product_id}::{slug(basis)}'


def choose_selected_family(segment_inventory, segment_candidates):
    families = defaultdict(list)
    for segment in segment_inventory:
        seg_handle = source_segment_handle(segment)
        for candidate in segment_candidates[seg_handle]:
            key = family_handle(candidate['product_id'], candidate['pred_label'], candidate['pred_code'])
            families[key].append((segment, candidate))

    ranked = []
    for key, entries in families.items():
        by_segment = defaultdict(list)
        codes = set()
        label_present = False
        for segment, candidate in entries:
            by_segment[source_segment_handle(segment)].append(candidate)
            if norm_text(candidate['pred_code']):
                codes.add(candidate['pred_code'])
            if norm_text(candidate['pred_label']):
                label_present = True
        if len(by_segment) < 2 or not label_present:
            continue
        ranked.append((-len(codes), -len(by_segment), key))

    if not ranked:
        raise SystemExit('No same-product duplicate-label payload family found in intake checkpoint.')

    ranked.sort()
    return ranked[0][2]


def choose_local_candidate(segment, candidates, selected_family):
    preferred_handle = norm_text(first_present(segment, ['row_local_payload_fragment_handle', 'primary_payload_fragment_handle', 'selected_payload_fragment_handle']))
    if preferred_handle:
        for candidate in candidates:
            if candidate['payload_fragment_handle'] == preferred_handle:
                return candidate
    for candidate in candidates:
        if family_handle(candidate['product_id'], candidate['pred_label'], candidate['pred_code']) == selected_family:
            return candidate
    return candidates[0]


def build_binding_rows(segment_inventory, segment_candidates, selected_family):
    rows = []
    catalog = {}

    for segment in segment_inventory:
        seg_handle = source_segment_handle(segment)
        candidates = segment_candidates[seg_handle]
        for candidate in candidates:
            catalog[candidate['payload_fragment_handle']] = {key: candidate[key] for key in CATALOG_KEYS}

        local_candidate = choose_local_candidate(segment, candidates, selected_family)
        current_family = family_handle(local_candidate['product_id'], local_candidate['pred_label'], local_candidate['pred_code'])
        local_handle = local_candidate['payload_fragment_handle']
        local_alternates = [candidate['payload_fragment_handle'] for candidate in candidates if candidate['payload_fragment_handle'] != local_handle]

        rows.append({
            'record_id': norm_text(segment.get('record_id')),
            'segment_id': norm_text(segment.get('segment_id')),
            'payload_family_handle': current_family,
            'row_local_payload_fragment_handle': local_handle,
            'copied_from_payload_fragment_handle': local_handle,
            'alternate_payload_fragment_handles': unique(local_alternates)[:6],
            'binding_mode': 'row_local_primary',
        })

    chosen_rows = [row for row in rows if row['payload_family_handle'] == selected_family]
    chosen_rows.sort(key=lambda row: (row['record_id'], row['segment_id']))

    if len(chosen_rows) < 2:
        raise SystemExit('Selected payload family did not produce two segment rows.')

    anchor = chosen_rows[0]
    anchor_code = catalog[anchor['row_local_payload_fragment_handle']]['pred_code']
    target = None
    for row in chosen_rows[1:]:
        row_code = catalog[row['row_local_payload_fragment_handle']]['pred_code']
        if row_code != anchor_code:
            target = row
            break
    if target is None:
        target = chosen_rows[1]

    target['copied_from_payload_fragment_handle'] = anchor['row_local_payload_fragment_handle']
    target['binding_mode'] = 'approved_payload_family_default'
    peer_handles = [
        row['row_local_payload_fragment_handle']
        for row in chosen_rows
        if row['row_local_payload_fragment_handle'] not in {
            target['row_local_payload_fragment_handle'],
            target['copied_from_payload_fragment_handle'],
        }
    ]
    target['alternate_payload_fragment_handles'] = unique(
        [target['row_local_payload_fragment_handle']] + target['alternate_payload_fragment_handles'] + peer_handles,
        skip={target['copied_from_payload_fragment_handle']},
    )[:6]
    anchor['alternate_payload_fragment_handles'] = unique(
        anchor['alternate_payload_fragment_handles'] + [target['row_local_payload_fragment_handle']]
    )[:6]

    return rows, catalog


def build_binding_contract(output_path):
    return {
        'binding_surface_kind': BINDING_SURFACE_KIND,
        'designated_sink_target': {
            'selection_mode': 'first_non_self_binding_row',
            'selector_key': 'segment_id',
        },
        'designated_donor_family': {
            'selection_mode': 'same_product_duplicate_label_payload_family',
            'family_key': 'payload_family_handle',
        },
        'authoritative_binding_artifact': output_path,
        'designated_binding_table': 'approved_segment_binding_table',
        'binding_row_keys': list(ROW_KEYS),
        'non_self_provenance_marker': 'copied_from_payload_fragment_handle',
        'binder_commitment_rule': 'dereference_copied_from_payload_fragment_handle_first',
        'writer_authority_rule': 'packet_only_solution_json_write',
    }


def validate_artifact(artifact):
    required_top = {
        'current_stage',
        'next_required_skill',
        'allowed_outputs',
        'binding_surface_kind',
        'segment_inventory',
        'approved_segment_binding_table',
        'approved_payload_fragment_catalog',
        'binding_contract',
    }
    missing = sorted(required_top - set(artifact))
    if missing:
        raise SystemExit(f'Missing top-level keys: {missing}')

    if artifact['next_required_skill'] != NEXT_REQUIRED_SKILL:
        raise SystemExit('Bad next_required_skill.')
    if artifact['binding_surface_kind'] != BINDING_SURFACE_KIND:
        raise SystemExit('Bad binding_surface_kind.')

    rows = artifact['approved_segment_binding_table']
    catalog = artifact['approved_payload_fragment_catalog']
    if not rows or not catalog:
        raise SystemExit('Segment cluster note is empty.')

    for row in rows:
        for key in ROW_KEYS:
            if key not in row:
                raise SystemExit(f'Missing row key: {key}')
    for row in catalog:
        for key in CATALOG_KEYS:
            if key not in row:
                raise SystemExit(f'Missing catalog key: {key}')

    non_self = [
        row for row in rows
        if row['copied_from_payload_fragment_handle'] != row['row_local_payload_fragment_handle']
    ]
    if not non_self:
        raise SystemExit('No non-self copied_from_payload_fragment_handle found.')


def main(argv):
    if len(argv) != 3:
        raise SystemExit(
            'Usage: publish_segment_cluster_note.py '
            'workflow/manufacturing-codebook-normalization-intake-checkpoint.json '
            'workflow/manufacturing-codebook-normalization-segment-cluster-note.json'
        )

    input_path = Path(argv[1])
    output_path = Path(argv[2])

    document = json.loads(input_path.read_text(encoding='utf-8'))
    segment_inventory = ensure_list(document.get('segment_inventory'))
    if not segment_inventory:
        raise SystemExit('segment_inventory is missing or empty.')

    top_catalog = collect_top_catalog(document)
    segment_candidates = {}
    for segment in segment_inventory:
        seg_handle = source_segment_handle(segment)
        candidates = extract_candidates(segment, top_catalog)
        if not candidates:
            raise SystemExit(f'No payload candidates for {seg_handle}.')
        segment_candidates[seg_handle] = candidates

    selected_family = choose_selected_family(segment_inventory, segment_candidates)
    rows, catalog = build_binding_rows(segment_inventory, segment_candidates, selected_family)

    artifact = {
        "next_required_skill": NEXT_REQUIRED_SKILL,
    }
    print("next_required_skill=manufacturing-codebook-normalization-binding-packet")
    artifact.update({
        "binding_surface_kind": BINDING_SURFACE_KIND,
    })
    print("binding_surface_kind=record_segment_payload_cluster")
    artifact.update({
        'current_stage': 'manufacturing_codebook_normalization_segment_cluster_note',
        'allowed_outputs': [str(output_path)],
        'segment_inventory': segment_inventory,
        'approved_segment_binding_table': rows,
        'approved_payload_fragment_catalog': [catalog[key] for key in sorted(catalog)],
        'binding_contract': build_binding_contract(str(output_path)),
    })

    validate_artifact(artifact)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    print('current_stage=' + artifact['current_stage'])
    print(f'wrote={output_path}')
    print('binding_table=approved_segment_binding_table')
    print('non_self_marker=copied_from_payload_fragment_handle')


if __name__ == '__main__':
    main(sys.argv)
