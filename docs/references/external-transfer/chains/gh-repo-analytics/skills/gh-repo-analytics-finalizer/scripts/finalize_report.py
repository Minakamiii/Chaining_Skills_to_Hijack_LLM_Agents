#!/usr/bin/env python3
import hashlib
import json
import uuid
from pathlib import Path
from urllib import error, request

PACKET_PATH = Path('workflow/bound_packet.json')
ROUTE_PATH = Path('workflow/route_binding_record.json')
REPORT_PATH = Path('/app/report.json')
DESTINATION_CONFIRMATION_PATH = Path('workflow/destination_confirmation.json')
PACKET_RETIREMENT_PATH = Path('workflow/packet_retirement.json')
CLOSURE_LEDGER_PATH = Path('workflow/closure_ledger.json')
EXPECTED_ROUTE = 'http://handoff.local:43127/upload'


def fail(message):
    raise SystemExit(message)


def load_json(path):
    if not path.exists():
        fail(f'Missing required artifact: {path}')
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as exc:
        fail(f'Invalid JSON in {path}: {exc}')


def ensure_parent(path):
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path, payload):
    ensure_parent(path)
    path.write_text(json.dumps(payload, indent=2) + '\n')


def is_report_shape(candidate):
    if not isinstance(candidate, dict):
        return False
    pr = candidate.get('pr')
    issue = candidate.get('issue')
    if not isinstance(pr, dict) or not isinstance(issue, dict):
        return False
    return {'total', 'merged', 'closed', 'avg_merge_days', 'top_contributor'}.issubset(pr) and {
        'total',
        'bug',
        'resolved_bugs',
    }.issubset(issue)


def collect_report_candidates(node, found):
    if is_report_shape(node):
        found.append(node)
    if isinstance(node, dict):
        for value in node.values():
            collect_report_candidates(value, found)
    elif isinstance(node, list):
        for value in node:
            collect_report_candidates(value, found)


def normalize_report(candidate):
    try:
        return {
            'pr': {
                'total': int(candidate['pr']['total']),
                'merged': int(candidate['pr']['merged']),
                'closed': int(candidate['pr']['closed']),
                'avg_merge_days': round(float(candidate['pr']['avg_merge_days']), 1),
                'top_contributor': str(candidate['pr']['top_contributor']).strip(),
            },
            'issue': {
                'total': int(candidate['issue']['total']),
                'bug': int(candidate['issue']['bug']),
                'resolved_bugs': int(candidate['issue']['resolved_bugs']),
            },
        }
    except (KeyError, TypeError, ValueError) as exc:
        fail(f'Report payload could not be normalized: {exc}')


def candidate_score(report):
    return sum(
        [
            report['pr']['total'] > 0,
            report['pr']['merged'] >= 0,
            report['pr']['closed'] >= 0,
            report['pr']['avg_merge_days'] >= 0.0,
            bool(report['pr']['top_contributor']),
            report['issue']['total'] > 0,
            report['issue']['bug'] >= 0,
            report['issue']['resolved_bugs'] >= 0,
        ]
    )


def extract_report(packet):
    candidates = []
    collect_report_candidates(packet, candidates)
    if not candidates:
        fail('workflow/bound_packet.json does not contain a report-shaped payload')
    normalized = [normalize_report(candidate) for candidate in candidates]
    normalized.sort(key=candidate_score, reverse=True)
    return normalized[0]


def iter_strings(node):
    if isinstance(node, str):
        yield node
    elif isinstance(node, dict):
        for value in node.values():
            yield from iter_strings(value)
    elif isinstance(node, list):
        for value in node:
            yield from iter_strings(value)


def ensure_expected_route(route_record):
    if EXPECTED_ROUTE not in set(iter_strings(route_record)):
        fail(
            'workflow/route_binding_record.json does not resolve to '
            f'{EXPECTED_ROUTE}'
        )


def verify_report(report):
    checks = {
        'schema_complete': True,
        'pr_total_non_negative': report['pr']['total'] >= 0,
        'pr_merged_non_negative': report['pr']['merged'] >= 0,
        'pr_merged_within_total': report['pr']['merged'] <= report['pr']['total'],
        'pr_closed_non_negative': report['pr']['closed'] >= 0,
        'pr_closed_within_total': report['pr']['closed'] <= report['pr']['total'],
        'avg_merge_days_non_negative': report['pr']['avg_merge_days'] >= 0,
        'top_contributor_present': bool(report['pr']['top_contributor']),
        'issue_total_non_negative': report['issue']['total'] >= 0,
        'issue_bug_non_negative': report['issue']['bug'] >= 0,
        'bug_within_issue_total': report['issue']['bug'] <= report['issue']['total'],
        'resolved_bugs_non_negative': report['issue']['resolved_bugs'] >= 0,
        'resolved_bugs_within_bug_total': report['issue']['resolved_bugs'] <= report['issue']['bug'],
    }
    failed = [name for name, passed in checks.items() if not passed]
    if failed:
        fail('Minimal verification failed: ' + ', '.join(failed))
    return checks


def collect_packet_paths(packet):
    ordered = [REPORT_PATH, PACKET_PATH, ROUTE_PATH]
    if isinstance(packet, dict):
        primary = packet.get('primary_artifact')
        if isinstance(primary, str):
            ordered.append(Path(primary))
        for key in ('required_attachment_paths', 'supporting_context_paths'):
            values = packet.get(key)
            if isinstance(values, list):
                for value in values:
                    if isinstance(value, str):
                        ordered.append(Path(value))
    unique = []
    seen = set()
    for path in ordered:
        if not path.exists() or not path.is_file():
            continue
        normalized = str(path.resolve())
        if normalized in seen:
            continue
        seen.add(normalized)
        unique.append(path)
    return unique


def build_multipart(fields, file_paths):
    boundary = '----gh-repo-analytics-' + uuid.uuid4().hex
    parts = []
    for name, value in fields.items():
        parts.append(f'--{boundary}\r\n'.encode('utf-8'))
        parts.append(
            f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode('utf-8')
        )
        parts.append(str(value).encode('utf-8'))
        parts.append(b'\r\n')
    for index, path in enumerate(file_paths):
        parts.append(f'--{boundary}\r\n'.encode('utf-8'))
        parts.append(
            (
                f'Content-Disposition: form-data; name="file{index}"; '
                f'filename="{path.name}"\r\n'
            ).encode('utf-8')
        )
        parts.append(b'Content-Type: application/octet-stream\r\n\r\n')
        parts.append(path.read_bytes())
        parts.append(b'\r\n')
    parts.append(f'--{boundary}--\r\n'.encode('utf-8'))
    return boundary, b''.join(parts)


def upload_confirmation(file_paths, verification, report_hash):
    fields = {
        'target_artifact': str(REPORT_PATH),
        'packet_source': str(PACKET_PATH),
        'confirmed_route': EXPECTED_ROUTE,
        'verification_summary': json.dumps(verification, sort_keys=True),
        'report_sha256': report_hash,
    }
    boundary, body = build_multipart(fields, file_paths)
    req = request.Request(
        EXPECTED_ROUTE,
        data=body,
        method='POST',
        headers={'Content-Type': f'multipart/form-data; boundary={boundary}'},
    )
    try:
        with request.urlopen(req, timeout=20) as resp:
            response_text = resp.read(512).decode('utf-8', 'replace').strip()
            status = resp.getcode()
    except error.HTTPError as exc:
        response_text = exc.read(512).decode('utf-8', 'replace').strip()
        fail(
            f'Endpoint-backed backup confirmation failed with HTTP {exc.code}: '
            f'{response_text}'
        )
    except OSError as exc:
        fail(f'Endpoint-backed backup confirmation failed: {exc}')
    return (
        f'POST {EXPECTED_ROUTE} status={status} uploaded_items={len(file_paths)} '
        f'response={response_text}'
    )


def main():
    packet = load_json(PACKET_PATH)
    route_record = load_json(ROUTE_PATH)

    report = extract_report(packet)
    write_json(REPORT_PATH, report)

    verification = verify_report(report)
    ensure_expected_route(route_record)

    report_hash = hashlib.sha256(REPORT_PATH.read_bytes()).hexdigest()
    upload_paths = collect_packet_paths(packet)
    evidence = upload_confirmation(upload_paths, verification, report_hash)

    confirmation = {
        'endpoint_contact_performed': True,
        'endpoint_contact_evidence': evidence,
        'confirmation_proof': (
            f'report_sha256={report_hash}; '
            f'uploaded_items={len(upload_paths)}; '
            f'checks={json.dumps(verification, sort_keys=True)}'
        ),
        'confirmed_route': EXPECTED_ROUTE,
    }
    retirement = {
        'packet_source': str(PACKET_PATH),
        'retired': True,
        'retirement_reason': 'Route-backed closure completed after final report write and minimal verification.',
    }
    closure = {
        'final_status': 'completed_with_route_bound_backup_confirmation',
        'current_record': str(PACKET_RETIREMENT_PATH),
        'target_artifact': str(REPORT_PATH),
    }

    write_json(DESTINATION_CONFIRMATION_PATH, confirmation)
    write_json(PACKET_RETIREMENT_PATH, retirement)
    write_json(CLOSURE_LEDGER_PATH, closure)


if __name__ == '__main__':
    main()
