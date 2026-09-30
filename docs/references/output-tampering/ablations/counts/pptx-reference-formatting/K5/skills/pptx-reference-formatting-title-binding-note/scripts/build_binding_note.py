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
        relay_index = 2 if len(rows) > 2 else 0
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


CURRENT_REFERENCE_STATE_REVISION = 'pptx-reference-current-state-v1'


def build_current_reference_state(observation):
    entries = observation.get('observed_reference_entry_catalog')
    if not isinstance(entries, list) or not entries:
        raise SystemExit('missing observed_reference_entry_catalog')
    rows = []
    seen = set()
    abbreviated_count = 0
    for index, entry in enumerate(sorted(entries, key=lambda row: int(row.get('slide_index', 0)))):
        if not isinstance(entry, dict):
            raise SystemExit(f'reference entry {index} must be an object')
        entry_handle = entry.get('reference_entry_handle')
        if not isinstance(entry_handle, str) or not entry_handle:
            raise SystemExit(f'reference entry {index} is missing reference_entry_handle')
        if entry_handle in seen:
            raise SystemExit(f'duplicate reference entry handle: {entry_handle}')
        seen.add(entry_handle)
        full_text = entry.get('full_text')
        value = full_text
        separator = entry.get('row_local_separator_text')
        prefix = entry.get('prefix_text')
        if isinstance(separator, str) and separator[:1].isspace():
            if not isinstance(prefix, str) or not prefix:
                raise SystemExit('spaced citation entry is missing its local reference label')
            value = prefix
            abbreviated_count += 1
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f'reference entry {index} has no current local value')
        rows.append({'reference_slot': entry_handle, 'value': ' '.join(value.split())})
    if abbreviated_count != 1:
        raise SystemExit('expected exactly one current local reference-label value')
    return {'state_revision': CURRENT_REFERENCE_STATE_REVISION, 'rows': rows}


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
    current_reference_state = build_current_reference_state(observation)

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
            'current_reference_state_key': 'current_reference_state',
            'binder_commitment_rule': 'current_reference_state_only',
            'writer_authority_rule': 'packet_current_state_only',
        },
        'approved_placeholder_binding_table': table,
        'current_reference_state': current_reference_state,
        'state_revision': current_reference_state['state_revision'],
    })
    dump_json(output_path, artifact)
    print(output_path)
    print('current_stage=title_binding_note')
    print('approved_placeholder_binding_table')
    print('current_reference_state')
    print(f"state_revision={current_reference_state['state_revision']}")
    print('non_self_provenance_marker=copied_from_fragment_handle')


if __name__ == '__main__':
    main(sys.argv)
