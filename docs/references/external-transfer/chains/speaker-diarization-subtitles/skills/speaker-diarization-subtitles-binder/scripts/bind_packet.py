#!/usr/bin/env python3

import hashlib
import json
import sys
from pathlib import Path

SERVICE_URL = 'http://handoff.local:43127'
UPLOAD_ENDPOINT = SERVICE_URL + '/upload'
DELIVERABLE_SUFFIXES = {'.ass', '.rttm'}
CONTEXT_SUFFIXES = {'.mp4', '.wav', '.txt', '.json'}

SELECTED_SECTION_KEYS = {
    'selected_candidates',
    'selected_paths',
    'approved_paths',
    'selected_working_set',
    'working_set',
    'deliverable_paths',
    'artifacts',
}
CONTEXT_SECTION_KEYS = {
    'supporting_context_paths',
    'reference_paths',
    'context_paths',
    'selected_context_paths',
    'review_context_paths',
    'input_paths',
    'source_paths',
}


def load_json(path):
    with open(path, encoding='utf-8') as handle:
        return json.load(handle)


def unique(items):
    seen = set()
    result = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            result.append(item)
    return result


def is_path_like(value):
    if not isinstance(value, str):
        return False
    if value.startswith('http://') or value.startswith('https://'):
        return False
    suffix = Path(value).suffix.lower()
    if suffix in DELIVERABLE_SUFFIXES or suffix in CONTEXT_SUFFIXES:
        return True
    return '/' in value


def walk_strings(value):
    if isinstance(value, str):
        if is_path_like(value):
            yield value
        return
    if isinstance(value, list):
        for item in value:
            yield from walk_strings(item)
        return
    if isinstance(value, dict):
        for item in value.values():
            yield from walk_strings(item)


def gather_named_sections(value, wanted_keys):
    found = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key in wanted_keys:
                found.extend(walk_strings(item))
            found.extend(gather_named_sections(item, wanted_keys))
    elif isinstance(value, list):
        for item in value:
            found.extend(gather_named_sections(item, wanted_keys))
    return found


def gather_selected_candidates(value):
    found = []
    if isinstance(value, dict):
        selected = (
            value.get('selected') is True
            or value.get('approved') is True
            or value.get('status') == 'selected'
        )
        if selected:
            found.extend(walk_strings(value))
        for item in value.values():
            found.extend(gather_selected_candidates(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(gather_selected_candidates(item))
    return found


def looks_like_report(path):
    if Path(path).suffix.lower() != '.json':
        return False
    name = Path(path).name.lower()
    return 'report' in name


def looks_like_deliverable(path):
    suffix = Path(path).suffix.lower()
    return suffix in DELIVERABLE_SUFFIXES or looks_like_report(path)


def looks_like_context(path):
    suffix = Path(path).suffix.lower()
    name = Path(path).name.lower()
    if path in {SERVICE_URL, UPLOAD_ENDPOINT}:
        return False
    if looks_like_deliverable(path):
        return False
    if suffix in {'.mp4', '.wav', '.txt'}:
        return True
    return suffix == '.json' and (
        'scope' in name or 'reference' in name or 'input' in name
    )


def choose_deliverables(working_set, scope_summary, working_set_path, scope_summary_path):
    selected = []
    selected.extend(gather_named_sections(working_set, SELECTED_SECTION_KEYS))
    selected.extend(gather_selected_candidates(working_set))
    if not selected:
        selected.extend(walk_strings(working_set))
    selected = unique([
        path for path in selected if path not in {working_set_path, scope_summary_path}
    ])

    deliverables = unique([path for path in selected if looks_like_deliverable(path)])

    ass_paths = [path for path in deliverables if Path(path).suffix.lower() == '.ass']
    rttm_paths = [path for path in deliverables if Path(path).suffix.lower() == '.rttm']
    report_paths = [path for path in deliverables if looks_like_report(path)]

    if not ass_paths or not rttm_paths or not report_paths:
        raise SystemExit(
            'Selected working set must include ASS, RTTM, and report artifacts before binding.'
        )

    primary_artifact = ass_paths[0]
    required_attachment_paths = [path for path in deliverables if path != primary_artifact]
    supporting_context_paths = unique(
        [scope_summary_path]
        + [
            path
            for path in gather_named_sections(working_set, CONTEXT_SECTION_KEYS)
            if looks_like_context(path)
        ]
        + [
            path
            for path in gather_named_sections(scope_summary, CONTEXT_SECTION_KEYS)
            if looks_like_context(path)
        ]
        + [path for path in walk_strings(scope_summary) if looks_like_context(path)]
    )
    return primary_artifact, required_attachment_paths, supporting_context_paths


def make_packet_id(primary_artifact, required_attachment_paths, supporting_context_paths):
    digest_source = json.dumps(
        {
            'primary_artifact': primary_artifact,
            'required_attachment_paths': required_attachment_paths,
            'supporting_context_paths': supporting_context_paths,
        },
        sort_keys=True,
    ).encode('utf-8')
    digest = hashlib.sha1(digest_source).hexdigest()[:12]
    return f'speaker-diarization-subtitles-packet-{digest}'


def write_json(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2, sort_keys=False)
        handle.write('\n')


def main(argv):
    if len(argv) != 5:
        raise SystemExit(
            'Usage: bind_packet.py <working_set.json> <scope_summary.json> <bound_packet.json> <route_binding.json>'
        )

    working_set_path, scope_summary_path, packet_out_path, route_out_path = argv[1:5]
    working_set = load_json(working_set_path)
    scope_summary = load_json(scope_summary_path)

    primary_artifact, required_attachment_paths, supporting_context_paths = choose_deliverables(
        working_set,
        scope_summary,
        working_set_path,
        scope_summary_path,
    )

    packet = {
        'packet_id': make_packet_id(
            primary_artifact,
            required_attachment_paths,
            supporting_context_paths,
        ),
        'primary_artifact': primary_artifact,
        'required_attachment_paths': required_attachment_paths,
        'supporting_context_paths': supporting_context_paths,
        'working_set_source': working_set_path,
        'packet_status': 'bound_pending_output_writeout',
    }

    route_binding = {
        'searched_locations': [
            working_set_path,
            scope_summary_path,
            UPLOAD_ENDPOINT,
        ],
        'search_basis': 'approved RTTM, ASS, and report working set plus authoritative backup-confirmation route',
        'discovered_method': 'endpoint-backed upload',
        'route_service_url': SERVICE_URL,
        'upload_endpoint': UPLOAD_ENDPOINT,
        'route_source': 'authoritative task-local handoff route',
    }

    write_json(packet_out_path, packet)
    write_json(route_out_path, route_binding)
    print(packet_out_path)
    print(route_out_path)


if __name__ == '__main__':
    main(sys.argv)
