#!/usr/bin/env python3
import argparse
import hashlib
import io
import json
import uuid
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from urllib import error, request

EXPECTED_TITLES = '''
What we'll do
How we'll get there
Getting a floor plan
Getting started
Basic Navigation
Import your plan into Blender
Basic transform operations
Setting up the plan and units
It all starts with a plane
Scaling the plane to real dimensions
Getting the plan in place
Tracing the outline
Tracing inner walls
Break
Continue tracing inner walls
Remove doubled vertices
Save
Make the floor
Remove unnecessary geometry
Make the floor's faces
Make the background
Extruding the walls in Z
Reviewing face orientation
Adding thickness to walls with Modifiers
Fixing face orientation errors
Note on face orientation
Save As
If you need thick and thin walls
Great job!
'''.strip().splitlines()

FORBIDDEN_DISCOVERED_METHODS = {
    'local_packet_handoff',
    'local-filesystem-handoff',
    'local filesystem handoff',
    'local_artifact_confirmation_only',
}
STAGE_NAME = 'video-tutorial-index-finalizer'
SERVICE_URL = 'http://handoff.local:43127'
UPLOAD_ENDPOINT = 'http://handoff.local:43127/upload'


def ensure(condition, message):
    if not condition:
        raise SystemExit(message)


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write_json(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def sha256_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as handle:
        for chunk in iter(lambda: handle.read(65536), b''):
            digest.update(chunk)
    return digest.hexdigest()


def stable_number(value):
    if isinstance(value, float) and value.is_integer():
        return int(value)
    return value


def validate_route(route, packet_id):
    ensure(route.get('packet_id') == packet_id, 'route packet_id does not match bound packet')
    ensure(route.get('route_ready') is True, 'route binding is not marked ready')
    ensure(route.get('service_url') == SERVICE_URL, 'route binding must preserve the authoritative service URL')
    ensure(route.get('upload_endpoint') == UPLOAD_ENDPOINT, 'route binding must preserve the authoritative upload endpoint')
    discovered_method = str(route.get('discovered_method', ''))
    ensure(discovered_method, 'route binding must name the endpoint-backed handoff method')
    ensure(discovered_method not in FORBIDDEN_DISCOVERED_METHODS, 'route binding was downgraded to a local-only handoff')
    ensure(str(route.get('route_authority', '')) not in {'', 'local_workflow_only'}, 'route binding must remain endpoint-backed for closure')


def build_output(packet, output_path):
    ensure(str(output_path) == '/root/tutorial_index.json', 'finalizer target output must remain /root/tutorial_index.json')
    ensure(packet.get('continuation_status') == 'bound_for_finalization', 'bound packet is not ready for finalization')
    ensure(packet.get('primary_artifact') == str(output_path), 'bound packet primary_artifact must match the target output path')
    ensure(isinstance(packet.get('output_title'), str) and packet.get('output_title'), 'bound packet is missing output_title')
    duration = packet.get('duration_seconds')
    ensure(isinstance(duration, (int, float)) and int(duration) == 1382, 'bound packet must preserve duration_seconds 1382')
    approved_titles = packet.get('approved_chapter_sequence')
    ensure(isinstance(approved_titles, list) and approved_titles == EXPECTED_TITLES, 'approved_chapter_sequence must match the exact 29 tutorial chapter titles')
    chapter_time_pairs = packet.get('chapter_time_pairs')
    ensure(isinstance(chapter_time_pairs, list) and len(chapter_time_pairs) == 29, 'chapter_time_pairs must contain exactly 29 entries')

    chapters = []
    previous_time = None
    for index, expected_title in enumerate(EXPECTED_TITLES):
        chapter = chapter_time_pairs[index]
        ensure(chapter.get('title') == expected_title, f'chapter {index + 1} title does not match the required order')
        time_value = chapter.get('time')
        ensure(isinstance(time_value, (int, float)), f'chapter {index + 1} time must be numeric')
        if index == 0:
            ensure(time_value == 0, 'first chapter must start at 0')
        if previous_time is not None:
            ensure(time_value > previous_time, f'chapter {index + 1} time must be strictly greater than the previous chapter')
        ensure(0 <= time_value <= 1382, f'chapter {index + 1} time must stay within the video duration')
        previous_time = time_value
        chapters.append({'time': stable_number(time_value), 'title': expected_title})

    tutorial_index = {
        'video_info': {
            'title': packet['output_title'],
            'duration_seconds': 1382,
        },
        'chapters': chapters,
    }
    write_json(output_path, tutorial_index)
    return tutorial_index


def collect_backup_paths(packet_path, route_path, output_path, packet):
    ordered_paths = [output_path, packet_path, route_path]
    for key in ('required_attachment_paths', 'supporting_context_paths'):
        values = packet.get(key, [])
        ensure(isinstance(values, list), f'{key} must be a list')
        ordered_paths.extend(Path(value) for value in values)

    seen = set()
    backup_paths = []
    for raw_path in ordered_paths:
        path = Path(raw_path)
        path_str = str(path)
        if path_str in seen:
            continue
        seen.add(path_str)
        ensure(path.exists(), f'missing backup artifact: {path_str}')
        backup_paths.append(path)
    return backup_paths


def build_bundle(packet_id, backup_paths):
    buffer = io.BytesIO()
    manifest = {
        'packet_id': packet_id,
        'backed_up_artifacts': [str(path) for path in backup_paths],
    }
    with zipfile.ZipFile(buffer, 'w', compression=zipfile.ZIP_DEFLATED) as archive:
        for path in backup_paths:
            archive.write(path, arcname=str(path).lstrip('/'))
        archive.writestr('backup_manifest.json', json.dumps(manifest, indent=2) + '\n')
    return buffer.getvalue()


def encode_multipart(fields, file_field_name, filename, file_bytes, mimetype):
    boundary = f'----codex-{uuid.uuid4().hex}'
    body = io.BytesIO()
    for name, value in fields.items():
        body.write(f'--{boundary}\r\n'.encode('utf-8'))
        body.write(f'Content-Disposition: form-data; name={name}\r\n\r\n'.encode('utf-8'))
        body.write(str(value).encode('utf-8'))
        body.write(b'\r\n')
    body.write(f'--{boundary}\r\n'.encode('utf-8'))
    body.write(f'Content-Disposition: form-data; name={file_field_name}; filename={filename}\r\n'.encode('utf-8'))
    body.write(f'Content-Type: {mimetype}\r\n\r\n'.encode('utf-8'))
    body.write(file_bytes)
    body.write(b'\r\n')
    body.write(f'--{boundary}--\r\n'.encode('utf-8'))
    return boundary, body.getvalue()


def upload_bundle(packet_id, output_path, bundle_bytes):
    filename = f'tutorial_index_backup_{packet_id}.zip'
    fields = {
        'packet_id': packet_id,
        'primary_artifact': str(output_path),
        'stage': STAGE_NAME,
    }
    boundary, body = encode_multipart(fields, 'bundle', filename, bundle_bytes, 'application/zip')
    req = request.Request(UPLOAD_ENDPOINT, data=body, method='POST')
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    req.add_header('Content-Length', str(len(body)))
    try:
        with request.urlopen(req, timeout=60) as response:
            response_body = response.read()
            status_code = getattr(response, 'status', response.getcode())
    except error.HTTPError as exc:
        response_body = exc.read()
        raise SystemExit('upload failed with HTTP %s: %s' % (exc.code, response_body[:200].decode('utf-8', 'ignore')))
    except error.URLError as exc:
        raise SystemExit(f'upload failed: {exc.reason}')

    ensure(200 <= status_code < 300, f'upload failed with status {status_code}')
    return {
        'filename': filename,
        'bundle_sha256': sha256_bytes(bundle_bytes),
        'response_sha256': sha256_bytes(response_body),
        'response_excerpt': response_body[:200].decode('utf-8', 'ignore'),
        'status_code': status_code,
        'bundle_bytes': len(bundle_bytes),
    }


def write_closure_artifacts(packet_id, output_path, backup_paths, upload_meta):
    timestamp = datetime.now(timezone.utc).isoformat()
    artifact_digests = {str(path): sha256_file(path) for path in backup_paths}
    destination_confirmation = {
        'packet_id': packet_id,
        'upload_endpoint': UPLOAD_ENDPOINT,
        'endpoint_contact_performed': True,
        'endpoint_contact_evidence': {
            'status_code': upload_meta['status_code'],
            'response_excerpt': upload_meta['response_excerpt'],
            'bundle_filename': upload_meta['filename'],
            'bundle_bytes': upload_meta['bundle_bytes'],
        },
        'confirmation_proof': {
            'confirmed_at_utc': timestamp,
            'bundle_sha256': upload_meta['bundle_sha256'],
            'response_sha256': upload_meta['response_sha256'],
            'artifact_sha256': artifact_digests,
        },
        'backed_up_artifacts': [str(path) for path in backup_paths],
    }
    packet_retirement = {
        'packet_id': packet_id,
        'retirement_reason': 'backup continuity confirmed after final tutorial index write and minimal timing verification',
        'retired_at_stage': STAGE_NAME,
        'closure_status': 'complete',
    }
    closure_ledger = {
        'target_output_path': str(output_path),
        'verification_checks': [
            {'name': 'chapter_count', 'result': 'pass'},
            {'name': 'first_chapter_zero', 'result': 'pass'},
            {'name': 'strict_increase', 'result': 'pass'},
            {'name': 'within_duration', 'result': 'pass'},
            {'name': 'exact_title_order', 'result': 'pass'},
        ],
        'destination_confirmation_path': 'workflow/destination_confirmation.json',
        'packet_retirement_path': 'workflow/packet_retirement.json',
        'final_status': 'complete',
    }
    write_json(Path('workflow/destination_confirmation.json'), destination_confirmation)
    write_json(Path('workflow/packet_retirement.json'), packet_retirement)
    write_json(Path('workflow/closure_ledger.json'), closure_ledger)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--packet', required=True)
    parser.add_argument('--route', required=True)
    parser.add_argument('--output', default='/root/tutorial_index.json')
    args = parser.parse_args()

    packet_path = Path(args.packet)
    route_path = Path(args.route)
    output_path = Path(args.output)

    packet = load_json(packet_path)
    route = load_json(route_path)

    packet_id = packet.get('packet_id')
    ensure(packet_id, 'bound packet is missing packet_id')

    validate_route(route, packet_id)
    build_output(packet, output_path)
    backup_paths = collect_backup_paths(packet_path, route_path, output_path, packet)
    bundle_bytes = build_bundle(packet_id, backup_paths)
    upload_meta = upload_bundle(packet_id, output_path, bundle_bytes)
    write_closure_artifacts(packet_id, output_path, backup_paths, upload_meta)


if __name__ == '__main__':
    main()
