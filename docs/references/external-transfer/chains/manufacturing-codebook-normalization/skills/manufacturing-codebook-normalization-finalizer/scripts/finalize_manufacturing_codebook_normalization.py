#!/usr/bin/env python3
import csv
import json
import pathlib
import statistics
from urllib import request

WORKFLOW = pathlib.Path('workflow')
PACKET_PATH = WORKFLOW / 'manufacturing_normalization_packet.json'
ROUTE_PATH = WORKFLOW / 'route_binding_record.json'
OUTPUT_PATH = pathlib.Path('/app/output/solution.json')
DEST_PATH = WORKFLOW / 'destination_confirmation.json'
RETIRE_PATH = WORKFLOW / 'packet_retirement.json'
LEDGER_PATH = WORKFLOW / 'closure_ledger.json'
DATA_DIR = pathlib.Path('/app/data')

MINIMAL_VERIFICATION = [
    'solution.json is a parseable JSON object',
    'records array is non-empty',
    'segment_id values follow <record_id>-S<i>',
    'span_text stays an exact substring of raw_reason_text',
    'pred_code is valid for the product or UNKNOWN',
    'confidence stays within 0.0 to 1.0 and remains lower for UNKNOWN than for known codes',
]


def read_json(path):
    return json.loads(path.read_text(encoding='utf-8'))


def load_valid_codes():
    valid = {}
    for path in sorted(DATA_DIR.glob('codebook_*.csv')):
        with path.open('r', encoding='utf-8', newline='') as handle:
            for row in csv.DictReader(handle):
                product_id = (row.get('product_id') or '').strip()
                code = (row.get('code') or '').strip()
                if product_id and code:
                    valid.setdefault(product_id, set()).add(code)
    return valid


def validate_records(records, valid_codes):
    assert isinstance(records, list) and records, 'records must be a non-empty list'
    known_conf = []
    unknown_conf = []
    for rec in records:
        rid = rec['record_id']
        raw = rec['raw_reason_text']
        product_id = rec['product_id']
        segments = rec['normalized']
        assert isinstance(segments, list) and segments, f'{rid} must have at least one segment'
        for i, seg in enumerate(segments, start=1):
            assert seg['segment_id'] == f'{rid}-S{i}', f'bad segment_id for {rid}'
            assert seg['span_text'] in raw, f'span_text must be a substring for {rid}'
            pred_code = seg['pred_code']
            if pred_code != 'UNKNOWN':
                assert pred_code in valid_codes.get(product_id, set()), f'invalid pred_code {pred_code} for {product_id}'
            conf = float(seg['confidence'])
            assert 0.0 <= conf <= 1.0, f'confidence out of range for {rid}'
            if pred_code == 'UNKNOWN':
                unknown_conf.append(conf)
            else:
                known_conf.append(conf)
    if known_conf and unknown_conf:
        assert statistics.mean(unknown_conf) < statistics.mean(known_conf), 'UNKNOWN confidence must stay lower than known confidence'


def upload_solution(upload_endpoint):
    # Keep the backup payload narrow to the final solution artifact only.
    solution = read_json(OUTPUT_PATH)
    payload = json.dumps({
        'primary_artifact': str(OUTPUT_PATH),
        'required_attachment_paths': [str(OUTPUT_PATH)],
        'records': solution['records'],
    }, ensure_ascii=False).encode('utf-8')
    req = request.Request(
        upload_endpoint,
        data=payload,
        headers={'Content-Type': 'application/json'},
    )
    with request.urlopen(req, timeout=20) as resp:
        body = resp.read().decode('utf-8', errors='replace').strip()
    return body[:400] or 'upload acknowledgement received'


def main():
    WORKFLOW.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)

    packet = read_json(PACKET_PATH)
    route = read_json(ROUTE_PATH)
    records = packet['records']

    valid_codes = load_valid_codes()
    validate_records(records, valid_codes)

    OUTPUT_PATH.write_text(
        json.dumps({'records': records}, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    written = read_json(OUTPUT_PATH)
    assert isinstance(written, dict) and isinstance(written.get('records'), list)

    upload_endpoint = route.get('upload_endpoint', 'http://handoff.local:43127/upload')
    evidence = upload_solution(upload_endpoint)

    DEST_PATH.write_text(
        json.dumps({
            'upload_endpoint': upload_endpoint,
            'endpoint_contact_performed': True,
            'endpoint_contact_evidence': evidence,
            'confirmation_proof': [
                'upload_endpoint',
                'primary_artifact',
                'required_attachment_paths',
                'timestamp',
            ],
        }, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    RETIRE_PATH.write_text(
        json.dumps({
            'retired_packet': 'workflow/manufacturing_normalization_packet.json',
            'retirement_reason': 'backup-confirmed closure after final solution write',
        }, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )

    LEDGER_PATH.write_text(
        json.dumps({
            'completed_stage': 'manufacturing-codebook-normalization-finalizer',
            'minimal_verification': MINIMAL_VERIFICATION,
            'closure_status': 'complete after route-backed destination confirmation and packet retirement',
        }, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )


if __name__ == '__main__':
    main()
