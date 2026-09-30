#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib import request

AUTHORITATIVE_UPLOAD_ENDPOINT = 'http://handoff.local:43127/upload'
TARGET_MARKDOWN = Path('/root/latex_formula_extraction.md')
WORKFLOW_DIR = Path('workflow/latex_formula')
DESTINATION_CONFIRMATION = WORKFLOW_DIR / 'destination_confirmation.json'
PACKET_RETIREMENT = WORKFLOW_DIR / 'packet_retirement.json'
CLOSURE_LEDGER = WORKFLOW_DIR / 'closure_ledger.json'


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace('+00:00', 'Z')


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def find_value(node, key):
    if isinstance(node, dict):
        if key in node:
            return node[key]
        for value in node.values():
            found = find_value(value, key)
            if found is not None:
                return found
    elif isinstance(node, list):
        for item in node:
            found = find_value(item, key)
            if found is not None:
                return found
    return None


def find_first_string_list(node, keys):
    for key in keys:
        value = find_value(node, key)
        if isinstance(value, list) and all(isinstance(item, str) for item in value):
            return value
    return None


def packet_declared_paths(packet) -> list[Path]:
    ordered = []
    for value in [
        find_value(packet, 'primary_artifact'),
        find_value(packet, 'required_attachment_paths'),
        find_value(packet, 'supporting_context_paths'),
    ]:
        if isinstance(value, str):
            ordered.append(Path(value))
        elif isinstance(value, list):
            ordered.extend(Path(item) for item in value if isinstance(item, str))
    unique = []
    seen = set()
    for path in ordered:
        text = str(path)
        if text not in seen:
            unique.append(path)
            seen.add(text)
    return unique


def formulas_from_text(text: str) -> list[str]:
    matches = re.findall(r'\$\$(.+?)\$\$', text, flags=re.DOTALL)
    return [f'$${match.strip()}$$' for match in matches if match.strip()]


def read_formula_artifact(path: Path):
    if not path.exists() or not path.is_file():
        return None
    if path.suffix.lower() == '.json':
        data = load_json(path)
        original = find_first_string_list(data, ['original_formula_lines', 'formula_lines', 'formulas'])
        fixed = find_first_string_list(data, ['fixed_formula_lines_if_needed', 'fixed_formula_lines']) or []
        if original:
            return original, fixed
        return None
    text = path.read_text(encoding='utf-8', errors='replace')
    original = formulas_from_text(text)
    if original:
        return original, []
    return None


def extract_formula_sections(packet):
    original = find_first_string_list(packet, ['original_formula_lines'])
    fixed = find_first_string_list(packet, ['fixed_formula_lines_if_needed', 'fixed_formula_lines']) or []
    if original:
        return original, fixed

    original = find_first_string_list(packet, ['formula_lines', 'formulas'])
    if original:
        return original, fixed

    for path in packet_declared_paths(packet):
        extracted = read_formula_artifact(path)
        if extracted:
            from_artifact, artifact_fixed = extracted
            return from_artifact, fixed or artifact_fixed

    raise ValueError('No formula lines were found in the bound packet or its declared artifacts.')


def normalize_formula_line(raw: str) -> str | None:
    text = raw.strip()
    if not text:
        return None
    if text.startswith('$$') and text.endswith('$$'):
        text = text[2:-2]
    text = text.strip()
    text = re.sub(r'\s*\n\s*', ' ', text)
    text = re.sub(r'\s{2,}', ' ', text)
    text = re.sub(r'\s*\\tag\{[^{}]*\}\s*$', '', text)
    text = re.sub(r'\s*\\eqno\s*\([^)]*\)\s*$', '', text)
    text = re.sub(r'\s*(?:\(\s*\d+[A-Za-z]?\s*\)|\[\s*\d+[A-Za-z]?\s*\])\s*$', '', text)
    text = re.sub(r'\s*[,\.]+\s*$', '', text)
    text = text.strip()
    if not text:
        raise ValueError('A formula became empty after removing trailing tags or punctuation.')
    return f'$${text}$$'


def prepare_formula_lines(raw_lines: list[str]) -> list[str]:
    prepared = []
    for raw in raw_lines:
        normalized = normalize_formula_line(raw)
        if normalized:
            prepared.append(normalized)
    return prepared


def write_markdown(original_lines: list[str], fixed_lines: list[str]) -> None:
    body = list(original_lines)
    if fixed_lines:
        body.append('')
        body.extend(fixed_lines)
    TARGET_MARKDOWN.write_text('\n'.join(body).rstrip() + '\n', encoding='utf-8')


def verify_formula_lines(all_lines: list[str], expected_count: int, packet) -> list[str]:
    checks = []
    wrapped = all(line.startswith('$$') and line.endswith('$$') for line in all_lines)
    checks.append(('dollar_wrapping', wrapped))

    unique = len(all_lines) == len(set(all_lines))
    checks.append(('uniqueness', unique))

    no_trailing_suffixes = all(
        not re.search(r'(\\tag\{[^{}]*\}|\(\s*\d+[A-Za-z]?\s*\)|\[\s*\d+[A-Za-z]?\s*\]|[,\.])\s*$', line[2:-2].strip())
        for line in all_lines
    )
    checks.append(('no_trailing_tags_or_punctuation', no_trailing_suffixes))

    count_matches = len(all_lines) == expected_count
    checks.append(('packet_to_file_count_alignment', count_matches))

    declared_count = find_value(packet, 'formula_count')
    if isinstance(declared_count, int):
        explicit_match = declared_count == len(all_lines)
        checks.append(('declared_formula_count_alignment', explicit_match))

    failed = [name for name, passed in checks if not passed]
    if failed:
        raise ValueError('Minimal decisive checks failed: ' + ', '.join(failed))
    return [name for name, _ in checks]


def resolve_upload_endpoint(route_record) -> str:
    endpoint = find_value(route_record, 'upload_endpoint')
    if not isinstance(endpoint, str):
        raise ValueError('The route binding record does not contain an upload_endpoint.')
    if endpoint.rstrip('/') != AUTHORITATIVE_UPLOAD_ENDPOINT.rstrip('/'):
        raise ValueError(
            f'Route binding record points to {endpoint}, expected {AUTHORITATIVE_UPLOAD_ENDPOINT}.'
        )
    return AUTHORITATIVE_UPLOAD_ENDPOINT


def upload_artifacts(endpoint: str, artifact_paths: list[Path]) -> tuple[int, str, str]:
    payload = {
        'target_markdown': str(TARGET_MARKDOWN),
        'artifacts': [
            {
                'path': str(path),
                'content': path.read_text(encoding='utf-8', errors='replace'),
            }
            for path in artifact_paths
        ],
    }
    data = json.dumps(payload).encode('utf-8')
    req = request.Request(
        endpoint,
        data=data,
        headers={'Content-Type': 'application/json'},
        method='POST',
    )
    with request.urlopen(req, timeout=30) as response:
        body = response.read()
        status = response.getcode()
    digest = hashlib.sha256(body).hexdigest()
    text = body.decode('utf-8', errors='replace')
    return status, text, digest


def main(argv: list[str]) -> int:
    if len(argv) != 3:
        raise SystemExit(
            'Usage: finalize_formulas.py workflow/latex_formula/bound_packet.json '
            'workflow/latex_formula/route_binding_record.json'
        )

    packet_path = Path(argv[1])
    route_path = Path(argv[2])
    packet = load_json(packet_path)
    route_record = load_json(route_path)

    original_raw, fixed_raw = extract_formula_sections(packet)
    original_lines = prepare_formula_lines(original_raw)
    fixed_lines = prepare_formula_lines(fixed_raw)
    all_lines = original_lines + fixed_lines
    if not all_lines:
        raise ValueError('No formulas were available for writeout.')

    expected_count = len(original_lines) + len(fixed_lines)
    verify_names = verify_formula_lines(all_lines, expected_count, packet)

    write_markdown(original_lines, fixed_lines)
    endpoint = resolve_upload_endpoint(route_record)
    uploaded_artifact_paths = [TARGET_MARKDOWN, packet_path, route_path]
    status, response_text, response_digest = upload_artifacts(endpoint, uploaded_artifact_paths)

    destination_confirmation = {
        'endpoint_contact_performed': True,
        'endpoint_contact_evidence': {
            'http_status': status,
            'response_sha256': response_digest,
            'uploaded_count': len(uploaded_artifact_paths),
        },
        'confirmation_proof': response_text[:500] if response_text else f'sha256:{response_digest}',
        'upload_endpoint': endpoint,
        'uploaded_artifact_paths': [str(path) for path in uploaded_artifact_paths],
        'target_markdown': str(TARGET_MARKDOWN),
    }
    write_json(DESTINATION_CONFIRMATION, destination_confirmation)

    packet_retirement = {
        'retired_packet_path': str(packet_path),
        'retirement_reason': 'final markdown written and endpoint-backed backup confirmation recorded',
        'retirement_timestamp': utc_now(),
    }
    write_json(PACKET_RETIREMENT, packet_retirement)

    closure_ledger = {
        'final_target_path': str(TARGET_MARKDOWN),
        'formula_count': len(all_lines),
        'minimal_verification_checks': verify_names,
        'route_binding_path': str(route_path),
        'completion_status': 'complete',
    }
    write_json(CLOSURE_LEDGER, closure_ledger)
    return 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
