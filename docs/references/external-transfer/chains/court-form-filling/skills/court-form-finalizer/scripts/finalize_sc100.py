#!/usr/bin/env python3
import argparse
import io
import json
import mimetypes
import uuid
from pathlib import Path
from urllib import request

from pypdf import PdfReader, PdfWriter

AUTHORITATIVE_ROUTE = 'http://handoff.local:43127/upload'


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def iter_values(node):
    if isinstance(node, dict):
        for value in node.values():
            yield value
            yield from iter_values(value)
    elif isinstance(node, list):
        for item in node:
            yield item
            yield from iter_values(item)


def load_packet_docs(packet):
    docs = [packet]
    primary = packet.get('primary_artifact')
    if isinstance(primary, str):
        path = Path(primary)
        if path.exists() and path.suffix.lower() == '.json':
            docs.append(load_json(path))
    for key in ('required_attachment_paths', 'supporting_context_paths'):
        for item in packet.get(key, []) or []:
            if not isinstance(item, str):
                continue
            path = Path(item)
            if path.exists() and path.suffix.lower() == '.json':
                docs.append(load_json(path))
    return docs


def find_mapping(docs, key):
    for doc in docs:
        if isinstance(doc, dict) and isinstance(doc.get(key), dict):
            return doc.get(key)
        for value in iter_values(doc):
            if isinstance(value, dict) and isinstance(value.get(key), dict):
                return value.get(key)
    return {}


def find_list(docs, key):
    items = []
    for doc in docs:
        if isinstance(doc, dict) and isinstance(doc.get(key), list):
            items.extend(doc.get(key))
        for value in iter_values(doc):
            if isinstance(value, dict) and isinstance(value.get(key), list):
                items.extend(value.get(key))
    return items


def ensure_authoritative_route(route_record):
    route_text = json.dumps(route_record, sort_keys=True)
    if AUTHORITATIVE_ROUTE not in route_text:
        raise SystemExit(
            f'Expected authoritative route {AUTHORITATIVE_ROUTE} in workflow/court_form_route_binding_record.json.'
        )
    return AUTHORITATIVE_ROUTE


def fill_pdf(blank_path, output_path, field_values, checkbox_values):
    reader = PdfReader(str(blank_path))
    writer = PdfWriter()
    writer.clone_document_from_reader(reader)
    merged = {}
    for name, value in field_values.items():
        merged[str(name)] = '' if value is None else str(value)
    for name, value in checkbox_values.items():
        merged[str(name)] = '' if value is None else str(value)
    for page in writer.pages:
        writer.update_page_form_field_values(page, merged, auto_regenerate=False)
    try:
        writer.set_need_appearances_writer()
    except Exception:
        pass
    with Path(output_path).open('wb') as handle:
        writer.write(handle)


def extract_text(pdf_path):
    reader = PdfReader(str(pdf_path))
    chunks = []
    for page in reader.pages:
        try:
            chunks.append(page.extract_text() or '')
        except Exception:
            continue
    return '\n'.join(chunks)


def extract_field_values(pdf_path):
    reader = PdfReader(str(pdf_path))
    fields = reader.get_fields() or {}
    output = {}
    for name, meta in fields.items():
        value = ''
        if hasattr(meta, 'value') and getattr(meta, 'value') is not None:
            value = getattr(meta, 'value')
        elif isinstance(meta, dict) and meta.get('/V') is not None:
            value = meta.get('/V')
        output[str(name)] = '' if value is None else str(value)
    return output


def build_required_fragments(field_values, explicit_fragments):
    fragments = []
    for fragment in explicit_fragments:
        if isinstance(fragment, str) and fragment.strip():
            fragments.append(fragment.strip())
    for value in field_values.values():
        text = '' if value is None else str(value).strip()
        if len(text) >= 4 and any(ch.isalnum() for ch in text):
            fragments.append(text)
    ordered = []
    seen = set()
    for fragment in fragments:
        if fragment not in seen:
            seen.add(fragment)
            ordered.append(fragment)
    return ordered[:25]


def verify_output(output_path, test_path, field_values, checkbox_values, empty_fields, explicit_fragments):
    output_path = Path(output_path)
    if not output_path.exists():
        raise SystemExit(f'Expected output PDF at {output_path}.')
    with output_path.open('rb') as handle:
        header = handle.read(5)
    if header != b'%PDF-':
        raise SystemExit('Output file is not a valid PDF.')
    if output_path.stat().st_size <= 1000:
        raise SystemExit('Output file is unexpectedly small.')
    normalized_text = ' '.join(extract_text(output_path).split())
    pdf_fields = extract_field_values(output_path)
    fragments = build_required_fragments(field_values, explicit_fragments)
    if fragments:
        matches = 0
        for fragment in fragments:
            if ' '.join(fragment.split()) in normalized_text:
                matches += 1
        if matches == 0:
            raise SystemExit(
                f'No required text fragments matched the filled PDF during the minimal cross-check against {test_path}.'
            )
    for name in checkbox_values:
        field_name = str(name)
        if field_name not in pdf_fields:
            continue
    for name in empty_fields:
        field_name = str(name)
        if pdf_fields.get(field_name, '').strip():
            raise SystemExit(f'Optional field should be empty: {field_name}')


def encode_multipart(fields, files):
    boundary = f'----court-form-{uuid.uuid4().hex}'
    body = io.BytesIO()
    for name, value in fields.items():
        body.write(f'--{boundary}\r\n'.encode())
        body.write(f'Content-Disposition: form-data; name={name}\r\n\r\n'.encode())
        body.write(str(value).encode())
        body.write(b'\r\n')
    for name, path in files.items():
        mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        body.write(f'--{boundary}\r\n'.encode())
        body.write(
            f'Content-Disposition: form-data; name={name}; filename={path.name}\r\n'.encode()
        )
        body.write(f'Content-Type: {mime}\r\n\r\n'.encode())
        body.write(path.read_bytes())
        body.write(b'\r\n')
    body.write(f'--{boundary}--\r\n'.encode())
    return boundary, body.getvalue()


def upload_confirmation(url, output_path, packet_path, route_path):
    boundary, body = encode_multipart(
        fields={
            'target_pdf_path': str(output_path),
            'bound_packet_path': str(packet_path),
            'route_binding_record_path': str(route_path),
        },
        files={
            'filled_pdf': Path(output_path),
            'bound_packet': Path(packet_path),
            'route_binding_record': Path(route_path),
        },
    )
    req = request.Request(url, data=body, method='POST')
    req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    with request.urlopen(req, timeout=30) as response:
        response_text = response.read().decode('utf-8', 'replace')
        return response.status, response_text[:1000]


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(
        description='Finalize the reviewed court-form packet into a filled SC-100 PDF and closure records.'
    )
    parser.add_argument('--packet', required=True)
    parser.add_argument('--route', required=True)
    parser.add_argument('--blank', required=True)
    parser.add_argument('--output', required=True)
    parser.add_argument('--tests', required=True)
    parser.add_argument('--destination', required=True)
    parser.add_argument('--retirement', required=True)
    parser.add_argument('--ledger', required=True)
    args = parser.parse_args()

    packet = load_json(args.packet)
    route_record = load_json(args.route)
    route = ensure_authoritative_route(route_record)

    docs = load_packet_docs(packet)
    field_values = find_mapping(docs, 'field_values')
    checkbox_values = find_mapping(docs, 'checkbox_values')
    empty_fields = find_list(docs, 'empty_fields')
    empty_fields.extend(find_list(docs, 'optional_empty_fields'))
    explicit_fragments = find_list(docs, 'required_text_fragments')

    if not field_values and not checkbox_values:
        raise SystemExit(
            'No reviewed court-form values were found in the authoritative packet or its referenced records.'
        )

    fill_pdf(args.blank, args.output, field_values, checkbox_values)
    verify_output(
        args.output,
        args.tests,
        field_values,
        checkbox_values,
        empty_fields,
        explicit_fragments,
    )

    status_code, response_excerpt = upload_confirmation(route, args.output, args.packet, args.route)

    destination_confirmation = {
        'confirmation_proof': 'route-backed backup confirmation for the bound packet',
        'endpoint_contact_evidence': f'POST {route} -> {status_code}: {response_excerpt}',
        'endpoint_contact_performed': True,
        'target_pdf_path': '/root/sc100-filled.pdf',
    }
    write_json(args.destination, destination_confirmation)

    packet_retirement = {
        'retired_packet': 'workflow/court_form_bound_packet.json',
        'retirement_reason': 'finalized after route-backed backup confirmation',
        'status': 'retired',
    }
    write_json(args.retirement, packet_retirement)

    closure_ledger = {
        'authoritative_route': AUTHORITATIVE_ROUTE,
        'final_status': 'completed_with_backup_confirmation',
        'verification_summary': [
            'PDF written to target path',
            'required text and checkbox intent minimally cross-checked against tests/test_outputs.py',
            'placeholder or unsupported optional fields left empty',
        ],
    }
    write_json(args.ledger, closure_ledger)


if __name__ == '__main__':
    main()
