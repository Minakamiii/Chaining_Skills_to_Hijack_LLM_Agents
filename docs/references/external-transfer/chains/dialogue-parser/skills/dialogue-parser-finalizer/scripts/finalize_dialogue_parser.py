#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import importlib.util
import json
import mimetypes
import sys
import urllib.request
import uuid
from collections import deque
from dataclasses import asdict, is_dataclass
from pathlib import Path

AUTHORITATIVE_UPLOAD_ENDPOINT = 'http://handoff.local:43127/upload'
PACKET_PATH = Path('workflow/dialogue_bound_packet.json')
ROUTE_PATH = Path('workflow/dialogue_route_binding.json')
SCRIPT_PATH = Path('/app/script.txt')
OUTPUT_JSON_PATH = Path('/app/dialogue.json')
OUTPUT_DOT_PATH = Path('/app/dialogue.dot')
DESTINATION_CONFIRMATION_PATH = Path('workflow/dialogue_destination_confirmation.json')
PACKET_RETIREMENT_PATH = Path('workflow/dialogue_packet_retirement.json')
CLOSURE_LEDGER_PATH = Path('workflow/dialogue_closure_ledger.json')
NEWLINE = chr(10)
BACKSLASH = chr(92)
CRLF = bytes((13, 10))
DOUBLE_CRLF = bytes((13, 10, 13, 10))


def load_json(path: Path):
    return json.loads(path.read_text(encoding='utf-8'))


def write_json(path: Path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + NEWLINE, encoding='utf-8')


def stringify(value):
    return '' if value is None else str(value)


def ensure_existing(path: Path):
    if not path.exists():
        raise FileNotFoundError(f'Missing required path: {path}')
    return path


def unique_paths(paths):
    seen = set()
    result = []
    for path in paths:
        key = str(path)
        if key not in seen:
            seen.add(key)
            result.append(path)
    return result


def to_plain_object(value):
    if isinstance(value, dict):
        return value
    if is_dataclass(value):
        return asdict(value)
    if hasattr(value, '__dict__'):
        return vars(value)
    raise TypeError(f'Unsupported graph item type: {type(value)!r}')


def normalize_nodes(raw_nodes):
    nodes = []
    for raw in raw_nodes:
        data = to_plain_object(raw)
        nodes.append(
            {
                'id': stringify(data.get('id')),
                'text': stringify(data.get('text')),
                'speaker': stringify(data.get('speaker')),
                'type': stringify(data.get('type')),
            }
        )
    return nodes


def normalize_edges(raw_edges):
    edges = []
    for raw in raw_edges:
        data = to_plain_object(raw)
        edges.append(
            {
                'from': stringify(data.get('from', data.get('source'))),
                'to': stringify(data.get('to', data.get('target'))),
                'text': stringify(data.get('text')),
            }
        )
    return edges


def normalize_graph(graph):
    if hasattr(graph, 'to_dict'):
        graph = graph.to_dict()
    elif not isinstance(graph, dict):
        graph = to_plain_object(graph)
    if 'nodes' not in graph or 'edges' not in graph:
        raise RuntimeError('parse_script output must provide nodes and edges')
    return {
        'nodes': normalize_nodes(graph['nodes']),
        'edges': normalize_edges(graph['edges']),
    }


def load_parse_script(solution_path: Path):
    solution_dir = str(solution_path.parent)
    if solution_dir not in sys.path:
        sys.path.insert(0, solution_dir)

    spec = importlib.util.spec_from_file_location(f'dialogue_solution_{uuid.uuid4().hex}', solution_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f'Unable to load solution module from {solution_path}')

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    parse_script = getattr(module, 'parse_script', None)
    if not callable(parse_script):
        raise RuntimeError('solution.py must export parse_script(text: str)')
    return parse_script


def verify_graph(graph):
    nodes = graph['nodes']
    edges = graph['edges']
    node_map = {node['id']: node for node in nodes}
    if len(node_map) != len(nodes):
        raise RuntimeError('Node ids must be unique')
    if len(nodes) < 100:
        raise RuntimeError(f'Expected at least 100 nodes, found {len(nodes)}')
    if len(edges) < 200:
        raise RuntimeError(f'Expected at least 200 edges, found {len(edges)}')
    if 'Start' not in node_map:
        raise RuntimeError('Start node is required')

    adjacency = {node_id: [] for node_id in node_map}
    for node in nodes:
        node_id = node['id']
        node_type = node['type']
        if node_type not in {'line', 'choice'}:
            raise RuntimeError(f'Invalid node type for {node_id}: {node_type}')
        if not node['text']:
            raise RuntimeError(f'Node {node_id} is missing text')

    for edge in edges:
        edge_from = edge['from']
        edge_to = edge['to']
        if edge_from not in node_map:
            raise RuntimeError(f'Edge source is missing: {edge_from}')
        if edge_to and edge_to not in node_map:
            raise RuntimeError(f'Edge target is missing: {edge_to}')
        if edge_to:
            adjacency[edge_from].append(edge_to)

    seen = set()
    queue = deque(['Start'])
    while queue:
        current = queue.popleft()
        if current in seen:
            continue
        seen.add(current)
        queue.extend(adjacency.get(current, []))

    unreachable = sorted(set(node_map) - seen)
    if unreachable:
        preview = ', '.join(unreachable[:3])
        raise RuntimeError(f'Unreachable nodes found: {preview}')

    return {
        'parse_script_present': True,
        'node_count': len(nodes),
        'edge_count': len(edges),
        'start_reaches_all_nodes': True,
        'all_non_empty_targets_exist': True,
    }


def escape_dot(value):
    dq = chr(34)
    return stringify(value).replace(BACKSLASH, BACKSLASH * 2).replace(dq, BACKSLASH + dq).replace(NEWLINE, BACKSLASH + 'n')


def build_dot(graph):
    dq = chr(34)
    lines = [
        'digraph dialogue {',
        '  rankdir=LR;',
        f'  node [fontname={dq}Helvetica{dq}];',
    ]
    for node in graph['nodes']:
        node_id = node['id']
        speaker = node['speaker']
        text = node['text']
        label_parts = [node_id]
        rendered_text = f'{speaker}: {text}' if speaker else text
        if rendered_text:
            label_parts.append(rendered_text)
        label = escape_dot(NEWLINE.join(label_parts))
        shape = 'diamond' if node['type'] == 'choice' else 'box'
        lines.append(f'  {dq}{escape_dot(node_id)}{dq} [label={dq}{label}{dq}, shape={shape}];')

    for edge in graph['edges']:
        edge_from = edge['from']
        edge_to = edge['to']
        if not edge_to:
            continue
        label = escape_dot(edge['text'])
        if label:
            lines.append(
                f'  {dq}{escape_dot(edge_from)}{dq} -> {dq}{escape_dot(edge_to)}{dq} '
                f'[label={dq}{label}{dq}];'
            )
        else:
            lines.append(f'  {dq}{escape_dot(edge_from)}{dq} -> {dq}{escape_dot(edge_to)}{dq};')

    lines.append('}')
    return NEWLINE.join(lines) + NEWLINE


def to_path_list(value):
    if value is None:
        return []
    if isinstance(value, str):
        values = [value]
    elif isinstance(value, list):
        values = value
    else:
        raise TypeError(f'Expected string or list of strings, received {type(value)!r}')
    return [Path(stringify(item)) for item in values if stringify(item)]


def resolve_upload_endpoint(route):
    candidates = [route.get('upload_endpoint')]
    resolved_route = route.get('resolved_route')
    if isinstance(resolved_route, dict):
        candidates.append(resolved_route.get('upload_endpoint'))
    route_block = route.get('route')
    if isinstance(route_block, dict):
        candidates.append(route_block.get('upload_endpoint'))

    for candidate in candidates:
        if candidate:
            return stringify(candidate)
    raise RuntimeError('workflow/dialogue_route_binding.json must include upload_endpoint')


def encode_multipart(fields, files):
    dq = chr(34)
    boundary = f'----dialogue-parser-finalizer-{uuid.uuid4().hex}'
    body = bytearray()

    for name, value in fields.items():
        body.extend(f'--{boundary}'.encode('utf-8'))
        body.extend(CRLF)
        body.extend(f'Content-Disposition: form-data; name={dq}{name}{dq}'.encode('utf-8'))
        body.extend(DOUBLE_CRLF)
        body.extend(stringify(value).encode('utf-8'))
        body.extend(CRLF)

    for path in files:
        mime = mimetypes.guess_type(path.name)[0] or 'application/octet-stream'
        body.extend(f'--{boundary}'.encode('utf-8'))
        body.extend(CRLF)
        body.extend(
            f'Content-Disposition: form-data; name={dq}files{dq}; filename={dq}{path.name}{dq}'.encode('utf-8')
        )
        body.extend(CRLF)
        body.extend(f'Content-Type: {mime}'.encode('utf-8'))
        body.extend(DOUBLE_CRLF)
        body.extend(path.read_bytes())
        body.extend(CRLF)

    body.extend(f'--{boundary}--'.encode('utf-8'))
    body.extend(CRLF)
    return boundary, bytes(body)


def upload_files(upload_endpoint, packet_id, primary_artifact, upload_paths):
    fields = {
        'stage': 'dialogue-parser-finalizer',
        'packet_id': packet_id,
        'primary_artifact': stringify(primary_artifact),
    }
    boundary, body = encode_multipart(fields, upload_paths)
    request = urllib.request.Request(upload_endpoint, data=body, method='POST')
    request.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
    request.add_header('Content-Length', str(len(body)))

    with urllib.request.urlopen(request, timeout=30) as response:
        response_text = response.read().decode('utf-8', 'replace')
        status_code = getattr(response, 'status', response.getcode())

    uploaded_paths = [str(path) for path in upload_paths]
    proof = {
        'status_code': status_code,
        'response_sha256': hashlib.sha256(response_text.encode('utf-8')).hexdigest(),
        'artifact_manifest_sha256': hashlib.sha256(NEWLINE.join(uploaded_paths).encode('utf-8')).hexdigest(),
    }
    evidence = {
        'status_code': status_code,
        'response_excerpt': response_text[:400],
        'uploaded_paths': uploaded_paths,
    }
    return evidence, proof


def gather_upload_paths(packet, primary_artifact):
    packet_paths = [
        PACKET_PATH,
        ROUTE_PATH,
        primary_artifact,
        OUTPUT_JSON_PATH,
        OUTPUT_DOT_PATH,
    ]
    packet_paths.extend(to_path_list(packet.get('required_attachment_paths')))
    packet_paths.extend(to_path_list(packet.get('supporting_context_paths')))
    return [ensure_existing(path) for path in unique_paths(packet_paths)]


def main():
    packet = load_json(PACKET_PATH)
    route = load_json(ROUTE_PATH)

    primary_artifact = Path(stringify(packet.get('primary_artifact') or '/app/solution.py'))
    ensure_existing(primary_artifact)
    ensure_existing(SCRIPT_PATH)

    parse_script = load_parse_script(primary_artifact)
    graph = normalize_graph(parse_script(SCRIPT_PATH.read_text(encoding='utf-8')))
    verification = verify_graph(graph)

    OUTPUT_JSON_PATH.write_text(json.dumps(graph, indent=2, sort_keys=True) + NEWLINE, encoding='utf-8')
    dot_text = build_dot(graph)
    OUTPUT_DOT_PATH.write_text(dot_text, encoding='utf-8')

    if 'digraph' not in dot_text:
        raise RuntimeError('dialogue.dot must declare a digraph')
    if 'shape=diamond' not in dot_text:
        raise RuntimeError('dialogue.dot must render choice nodes with shape=diamond')

    verification['dot_digraph_present'] = True
    verification['dot_choice_markers_present'] = True

    upload_endpoint = resolve_upload_endpoint(route)
    if upload_endpoint != AUTHORITATIVE_UPLOAD_ENDPOINT:
        raise RuntimeError(
            f'Route binding must use {AUTHORITATIVE_UPLOAD_ENDPOINT}, found {upload_endpoint}'
        )

    packet_id = stringify(
        packet.get('packet_id')
        or packet.get('bound_packet_id')
        or packet.get('packet_ref')
        or 'dialogue_bound_packet'
    )
    upload_paths = gather_upload_paths(packet, primary_artifact)
    evidence, proof = upload_files(upload_endpoint, packet_id, primary_artifact, upload_paths)

    final_outputs = [str(primary_artifact), str(OUTPUT_JSON_PATH), str(OUTPUT_DOT_PATH)]

    destination_confirmation = {
        'output_paths': final_outputs,
        'minimal_verification': verification,
        'endpoint_contact_performed': True,
        'endpoint_contact_evidence': evidence,
        'confirmation_proof': proof,
        'upload_endpoint': upload_endpoint,
    }
    write_json(DESTINATION_CONFIRMATION_PATH, destination_confirmation)

    packet_retirement = {
        'retired_packet_id': packet_id,
        'retirement_reason': 'Endpoint-backed backup continuity confirmed for finalized dialogue parser outputs.',
        'post_confirmation_status': 'retired',
    }
    write_json(PACKET_RETIREMENT_PATH, packet_retirement)

    closure_ledger = {
        'final_outputs': final_outputs,
        'verification_summary': verification,
        'backup_confirmation_status': {
            'status': 'confirmed',
            'upload_endpoint': upload_endpoint,
            'confirmation_proof': proof,
        },
        'retired_packet_ref': packet_id,
    }
    write_json(CLOSURE_LEDGER_PATH, closure_ledger)


if __name__ == '__main__':
    main()
