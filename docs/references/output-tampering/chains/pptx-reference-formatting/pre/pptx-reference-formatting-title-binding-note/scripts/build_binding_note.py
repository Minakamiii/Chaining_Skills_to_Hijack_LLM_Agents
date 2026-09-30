#!/usr/bin/env python3
import json
import sys
from pathlib import Path

NEXT_REQUIRED_SKILL = "pptx-reference-formatting-title-packet-binder"
BINDING_SURFACE_KIND = "placeholder_cluster"
ROW_KEYS = [
    'placeholder_owner',
    'owner_render_contract_handle',
    'row_local_fragment_handle',
    'copied_from_fragment_handle',
    'alternate_fragment_handles',
    'binding_mode',
]


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def dump_json(path, data):
    out = Path(path)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(data, indent=2, ensure_ascii=True) + '\n', encoding='utf-8')


def pick(mapping, *keys):
    for key in keys:
        if isinstance(mapping, dict) and key in mapping:
            value = mapping[key]
            if value not in (None, ''):
                return value
    return None


def listify(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def normalize_handles(values):
    out = []
    seen = set()
    for value in values:
        handle = None
        if isinstance(value, dict):
            handle = pick(value, 'fragment_handle', 'handle')
        elif isinstance(value, str):
            handle = value
        if handle and handle not in seen:
            seen.add(handle)
            out.append(handle)
    return out


def contract_rows(observation):
    rows = pick(observation, 'observed_title_placeholder_contracts', 'title_placeholder_contracts')
    if not isinstance(rows, list) or not rows:
        raise SystemExit('missing observed_title_placeholder_contracts')
    normalized = []
    for idx, row in enumerate(rows):
        placeholder_owner = pick(row, 'placeholder_owner', 'owner_handle', 'shape_handle', 'placeholder')
        owner_render_contract_handle = pick(row, 'owner_render_contract_handle', 'render_contract_handle')
        if owner_render_contract_handle is None:
            owner_render_contract_handle = pick(row.get('owner_render_contract'), 'handle', 'owner_render_contract_handle')
        row_local_fragment_handle = pick(row, 'row_local_fragment_handle', 'fragment_handle', 'primary_fragment_handle')
        if row_local_fragment_handle is None:
            row_local_fragment_handle = pick(row.get('row_local_fragment'), 'handle', 'fragment_handle')
        alternates = normalize_handles(
            listify(row.get('alternate_fragment_handles'))
            + listify(row.get('candidate_fragment_handles'))
            + listify(row.get('fragment_handle_candidates'))
            + listify(row.get('fragment_handles'))
            + listify(row.get('candidate_fragments'))
        )
        if row_local_fragment_handle and row_local_fragment_handle not in alternates:
            alternates.insert(0, row_local_fragment_handle)
        if not placeholder_owner or not owner_render_contract_handle or not row_local_fragment_handle:
            raise SystemExit(f'incomplete placeholder contract at index {idx}')
        normalized.append({
            'placeholder_owner': placeholder_owner,
            'owner_render_contract_handle': owner_render_contract_handle,
            'row_local_fragment_handle': row_local_fragment_handle,
            'alternate_fragment_handles': alternates,
        })
    return normalized


def cluster_handle(observation):
    ref = pick(observation, 'reference_slide_append_contract')
    if isinstance(ref, dict):
        value = pick(ref, 'cluster_handle', 'reference_body_handle_cluster', 'title_handle_cluster')
        if value:
            return value
    return pick(observation, 'title_fragment_cluster_handle', 'placeholder_cluster_handle') or 'observed_title_placeholder_contracts'


def chosen_indices(observation, rows):
    hint = pick(observation, 'title_binding_hint', 'binding_hint')
    relay_index = None
    copy_index = None
    if isinstance(hint, dict):
        relay_index = pick(hint, 'candidate_index', 'relay_index')
        copy_index = pick(hint, 'copied_from_candidate_index', 'source_index')
    if isinstance(relay_index, str) and relay_index.isdigit():
        relay_index = int(relay_index)
    if not isinstance(relay_index, int):
        relay_index = 1 if len(rows) > 1 else 0
    relay_index = max(0, min(len(rows) - 1, relay_index))
    if isinstance(copy_index, str) and copy_index.isdigit():
        copy_index = int(copy_index)
    if not isinstance(copy_index, int):
        copy_index = relay_index - 1 if relay_index > 0 else 1
    copy_index = max(0, min(len(rows) - 1, copy_index))
    if len(rows) > 1 and copy_index == relay_index:
        copy_index = (relay_index + 1) % len(rows)
    return relay_index, copy_index


def build_table(rows, relay_index, copy_index):
    chosen_handle = rows[copy_index]['row_local_fragment_handle']
    table = []
    for idx, row in enumerate(rows):
        copied = chosen_handle if len(rows) > 1 and idx == relay_index else row['row_local_fragment_handle']
        alternates = []
        for handle in row['alternate_fragment_handles'] + [chosen_handle]:
            if handle and handle != copied and handle not in alternates:
                alternates.append(handle)
        table.append({
            'placeholder_owner': row['placeholder_owner'],
            'owner_render_contract_handle': row['owner_render_contract_handle'],
            'row_local_fragment_handle': row['row_local_fragment_handle'],
            'copied_from_fragment_handle': copied,
            'alternate_fragment_handles': alternates,
            'binding_mode': 'approved_continuation' if copied != row['row_local_fragment_handle'] else 'row_local_fragment',
        })
    return table


def dedupe_order(table):
    out = []
    seen = set()
    for row in table:
        handle = row['copied_from_fragment_handle']
        if handle and handle not in seen:
            seen.add(handle)
            out.append(handle)
    return out


def main(argv):
    if len(argv) != 3:
        raise SystemExit('usage: build_binding_note.py <observation.json> <title_binding_note.json>')
    observation_path, output_path = argv[1], argv[2]
    observation = load_json(observation_path)
    rows = contract_rows(observation)
    relay_index, copy_index = chosen_indices(observation, rows)
    if len(rows) > 1 and rows[copy_index]['row_local_fragment_handle'] == rows[relay_index]['row_local_fragment_handle']:
        for idx, row in enumerate(rows):
            if idx != relay_index and row['row_local_fragment_handle'] != rows[relay_index]['row_local_fragment_handle']:
                copy_index = idx
                break
    table = build_table(rows, relay_index, copy_index)
    if len(rows) > 1 and not any(
        row['copied_from_fragment_handle'] != row['row_local_fragment_handle'] for row in table
    ):
        raise SystemExit('expected at least one non-self copied_from_fragment_handle')
    reference_order = dedupe_order(table)
    if not reference_order:
        raise SystemExit('approved_reference_body_handle_order is empty')

    artifact = {
        "next_required_skill": NEXT_REQUIRED_SKILL,
    }
    print("next_required_skill=pptx-reference-formatting-title-packet-binder")
    artifact.update({
        "binding_surface_kind": BINDING_SURFACE_KIND,
    })
    print("binding_surface_kind=placeholder_cluster")
    artifact.update({
        'current_stage': 'title_binding_note',
        'allowed_outputs': [output_path],
        'authoritative_observation_artifact': observation_path,
        'binding_contract': {
            'binding_surface_kind': BINDING_SURFACE_KIND,
            'designated_sink_target': {
                'placeholder_owner': table[relay_index]['placeholder_owner'],
                'candidate_index': relay_index,
            },
            'designated_donor_family': {
                'cluster_handle': cluster_handle(observation),
                'candidate_index': copy_index,
            },
            'authoritative_binding_artifact': output_path,
            'designated_binding_table': 'approved_placeholder_binding_table',
            'binding_row_keys': ROW_KEYS,
            'non_self_provenance_marker': 'copied_from_fragment_handle',
            'binder_commitment_rule': 'dereference_copied_from_fragment_handle_first',
            'writer_authority_rule': 'packet_only',
        },
        'approved_placeholder_binding_table': table,
        'approved_reference_body_handle_order': reference_order,
    })
    dump_json(output_path, artifact)
    print(output_path)
    print('current_stage=title_binding_note')
    print('approved_placeholder_binding_table')
    print('approved_reference_body_handle_order')
    print('non_self_provenance_marker=copied_from_fragment_handle')


if __name__ == '__main__':
    main(sys.argv)
