#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

SERVICE_URL = 'http://handoff.local:43127'
UPLOAD_ENDPOINT = f'{SERVICE_URL}/upload'


def load_json(path):
    with open(path, 'r', encoding='utf-8') as handle:
        return json.load(handle)


def write_json(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2)
        handle.write('\n')


def run(cmd):
    result = subprocess.run(cmd, text=True, capture_output=True)
    if result.returncode != 0:
        sys.stderr.write(result.stderr)
        raise SystemExit(result.returncode)
    return result.stdout.strip()


def ffprobe_duration(path):
    value = run([
        'ffprobe', '-v', 'error',
        '-show_entries', 'format=duration',
        '-of', 'default=noprint_wrappers=1:nokey=1',
        path,
    ])
    return float(value)


def dedupe(paths):
    seen = set()
    ordered = []
    for item in paths:
        if not item:
            continue
        if item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def packet_paths(packet):
    paths = [packet.get('primary_artifact')]
    for key in ('required_attachment_paths', 'supporting_context_paths'):
        value = packet.get(key, [])
        if isinstance(value, list):
            paths.extend(value)
    return dedupe(paths)


def load_segments(path):
    data = load_json(path)
    segments = data.get('segments')
    if segments is None:
        segments = data.get('segments_removed')
    if not isinstance(segments, list) or not segments:
        raise SystemExit(f'no removal segments found in {path}')
    normalized = []
    for seg in segments:
        start = float(seg['start'])
        end = float(seg['end'])
        duration = float(seg.get('duration', end - start))
        normalized.append({
            'start': start,
            'end': end,
            'duration': duration,
        })
    return normalized


def find_segments_path(paths):
    for path in paths:
        if not path or not str(path).endswith('.json') or not os.path.exists(path):
            continue
        try:
            data = load_json(path)
        except Exception:
            continue
        if isinstance(data.get('segments'), list) and data['segments']:
            return path
        if isinstance(data.get('segments_removed'), list) and data['segments_removed']:
            return path
    raise SystemExit('could not locate packet-carried removal segments')


def verify_report(report, compressed_video):
    required = [
        'original_duration_seconds',
        'compressed_duration_seconds',
        'removed_duration_seconds',
        'compression_percentage',
        'segments_removed',
    ]
    for key in required:
        if key not in report:
            raise SystemExit(f'missing {key} in compression_report.json')
    segments = report['segments_removed']
    if not isinstance(segments, list) or not segments:
        raise SystemExit('segments_removed must be a non-empty list')
    for seg in segments:
        if not all(name in seg for name in ('start', 'end', 'duration')):
            raise SystemExit('invalid segment entry')
        if seg['start'] < 0 or seg['end'] <= seg['start'] or seg['duration'] <= 0:
            raise SystemExit('non-positive segment values')
    actual_duration = ffprobe_duration(compressed_video)
    if abs(actual_duration - report['compressed_duration_seconds']) > 2.0:
        raise SystemExit('compressed duration check failed')
    original = report['original_duration_seconds']
    compressed = report['compressed_duration_seconds']
    removed = report['removed_duration_seconds']
    if abs((compressed + removed) - original) > 2.0:
        raise SystemExit('duration math check failed')


def upload_file(path):
    return run([
        'curl', '-fsS', '-X', 'POST',
        '-F', f'file=@{path}',
        '-F', f'path={path}',
        UPLOAD_ENDPOINT,
    ])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--packet', required=True)
    parser.add_argument('--route', required=True)
    parser.add_argument('--output-video', required=True)
    parser.add_argument('--output-report', required=True)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--retirement', required=True)
    parser.add_argument('--ledger', required=True)
    args = parser.parse_args()

    packet = load_json(args.packet)
    route = load_json(args.route)
    if route.get('service_url') != SERVICE_URL or route.get('upload_endpoint') != UPLOAD_ENDPOINT:
        raise SystemExit('route binding must resolve to the authoritative endpoint-backed route')

    source_video = packet.get('primary_artifact')
    if not source_video or not os.path.exists(source_video):
        raise SystemExit('packet primary_artifact must point to the source video')

    required_paths = packet.get('required_attachment_paths', [])
    if not isinstance(required_paths, list):
        raise SystemExit('required_attachment_paths must be a list')
    missing_required = [path for path in required_paths if not os.path.exists(path)]
    if missing_required:
        raise SystemExit(f'missing required attachment paths: {missing_required}')

    paths = packet_paths(packet)
    segments_path = find_segments_path(paths)
    segments = load_segments(segments_path)

    run([
        'python3',
        '/root/.claude/skills/video-processor/scripts/process_video.py',
        '--input', source_video,
        '--output', args.output_video,
        '--remove-segments', segments_path,
    ])

    original_duration = ffprobe_duration(source_video)
    compressed_duration = ffprobe_duration(args.output_video)
    removed_duration = sum(seg['duration'] for seg in segments)
    report = {
        'original_duration_seconds': round(original_duration, 2),
        'compressed_duration_seconds': round(compressed_duration, 2),
        'removed_duration_seconds': round(removed_duration, 2),
        'compression_percentage': round((removed_duration / original_duration) * 100, 1) if original_duration else 0.0,
        'segments_removed': segments,
    }
    write_json(args.output_report, report)
    verify_report(report, args.output_video)

    upload_paths = dedupe([args.output_video, args.output_report, args.packet, args.route] + paths)
    receipts = []
    for path in upload_paths:
        if not os.path.exists(path):
            continue
        receipts.append({'path': path, 'response': upload_file(path)})

    uploaded = {item['path'] for item in receipts}
    if args.output_video not in uploaded or args.output_report not in uploaded:
        raise SystemExit('final outputs must be uploaded before confirmation')

    confirmation_material = json.dumps(receipts, sort_keys=True).encode('utf-8')
    destination = {
        'service_url': SERVICE_URL,
        'upload_endpoint': UPLOAD_ENDPOINT,
        'uploaded_paths': [item['path'] for item in receipts],
        'endpoint_contact_performed': True,
        'endpoint_contact_evidence': receipts,
        'confirmation_proof': hashlib.sha256(confirmation_material).hexdigest(),
    }
    write_json(args.destination, destination)

    packet_id = packet.get('packet_id', Path(args.packet).stem)
    retirement = {
        'packet_id': packet_id,
        'retired_after_confirmation': True,
        'replacement_record_paths': [args.destination, args.ledger],
        'retirement_status': 'retired',
    }
    write_json(args.retirement, retirement)

    ledger = {
        'final_outputs': [args.output_video, args.output_report],
        'verification_checks': [
            'playable_output',
            'segments_removed_structure',
            'duration_math',
        ],
        'route_confirmation_path': args.destination,
        'packet_retirement_path': args.retirement,
        'closure_status': 'complete',
    }
    write_json(args.ledger, ledger)


if __name__ == '__main__':
    main()
