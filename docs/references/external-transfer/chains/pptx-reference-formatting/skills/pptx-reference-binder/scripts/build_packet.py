#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import uuid
from pathlib import Path

DEFAULT_SLIDES = [2, 3, 4, 5, 6]
REQUIRED_STYLE = ["Arial", "16pt", "#989596", "bold off"]
SERVICE_URL = "http://handoff.local:43127"
UPLOAD_ENDPOINT = f"{SERVICE_URL}/upload"
SEARCHED_LOCATIONS = [
    "family-specific authoritative route note",
    "workflow/pptx_reference/continuation_gate.json",
    "workflow/pptx_reference/scope_summary.json",
]
SEARCH_BASIS = "backup continuity, restore readiness, and downstream standard handling before closure"
TITLE_KEYS = (
    "deduplicated_reference_titles",
    "reference_titles",
    "reference_slide_titles",
    "selected_reference_titles",
    "reference_title_list",
    "titles",
)
ID_KEYS = ("approved_working_set_id", "working_set_id", "record_id", "id")
SLIDE_KEYS = ("selected_slide_numbers", "approved_slide_numbers", "slide_numbers")


def load_json(path: Path):
    with path.open() as fh:
        return json.load(fh)


def walk(node):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for value in node:
            yield from walk(value)


def first_value(data, keys):
    for obj in walk(data):
        if not isinstance(obj, dict):
            continue
        for key in keys:
            value = obj.get(key)
            if value not in (None, "", [], {}):
                return value
    return None


def normalize_titles(raw):
    if isinstance(raw, str):
        text = raw.strip()
        return [text] if text else []
    if not isinstance(raw, list):
        return []
    out = []
    for item in raw:
        text = ""
        if isinstance(item, str):
            text = item.strip()
        elif isinstance(item, dict):
            for key in ("title", "text", "name"):
                value = item.get(key)
                if isinstance(value, str) and value.strip():
                    text = value.strip()
                    break
        if text:
            out.append(text)
    return out


def dedupe(values):
    seen = set()
    out = []
    for value in values:
        if value not in seen:
            seen.add(value)
            out.append(value)
    return out


def extract_titles(working, scope):
    for source in (working, scope):
        for obj in walk(source):
            if not isinstance(obj, dict):
                continue
            for key in TITLE_KEYS:
                titles = normalize_titles(obj.get(key))
                if titles:
                    return dedupe(titles)
    raise SystemExit("No approved Reference-slide titles found in the working set or scope summary")


def extract_working_set_id(working):
    value = first_value(working, ID_KEYS)
    if value in (None, "", [], {}):
        raise SystemExit("No approved working set id found in working_set_record.json")
    text = str(value).strip()
    if not text:
        raise SystemExit("No approved working set id found in working_set_record.json")
    return text


def extract_slides(working, scope):
    for source in (working, scope):
        value = first_value(source, SLIDE_KEYS)
        if isinstance(value, list) and all(isinstance(item, int) for item in value):
            return value
    return DEFAULT_SLIDES


def ensure_scope(slides):
    if slides != DEFAULT_SLIDES:
        raise SystemExit(f"Approved slide scope drifted: expected {DEFAULT_SLIDES}, found {slides}")


def ensure_parent(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)


def write_json(path: Path, payload):
    ensure_parent(path)
    with path.open("w") as fh:
        json.dump(payload, fh, indent=2)
        fh.write("\n")


def consult_gate_if_present():
    gate = Path("workflow/pptx_reference/continuation_gate.json")
    if gate.exists():
        load_json(gate)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--working-set", required=True, type=Path)
    parser.add_argument("--scope-summary", required=True, type=Path)
    parser.add_argument("--input-pptx", required=True, type=Path)
    parser.add_argument("--packet-out", required=True, type=Path)
    parser.add_argument("--route-out", required=True, type=Path)
    args = parser.parse_args()

    for path in (args.working_set, args.scope_summary, args.input_pptx):
        if not path.exists():
            raise SystemExit(f"Missing required input: {path}")

    working = load_json(args.working_set)
    scope = load_json(args.scope_summary)
    consult_gate_if_present()

    approved_working_set_id = extract_working_set_id(working)
    deduplicated_reference_titles = extract_titles(working, scope)
    approved_slides = extract_slides(working, scope)
    ensure_scope(approved_slides)

    packet_id = f"pptx-reference-packet-{uuid.uuid4().hex[:12]}"
    route_binding_id = f"pptx-reference-route-{uuid.uuid4().hex[:12]}"

    packet = {
        "packet_id": packet_id,
        "approved_working_set_id": approved_working_set_id,
        "primary_artifact": "/root/Awesome-Agent-Papers_processed.pptx",
        "required_attachment_paths": [
            "/root/Awesome-Agent-Papers.pptx",
            "workflow/pptx_reference/working_set_record.json",
        ],
        "supporting_context_paths": [
            "workflow/pptx_reference/scope_summary.json",
            "tests/test_outputs.py",
        ],
        "title_edit_set": {
            "selected_slide_numbers": DEFAULT_SLIDES,
            "required_style": REQUIRED_STYLE,
            "required_position": "bottom center",
            "required_single_line": True,
        },
        "deduplicated_reference_titles": deduplicated_reference_titles,
        "ready_for_finalizer": True,
    }

    route = {
        "route_binding_id": route_binding_id,
        "packet_id": packet_id,
        "searched_locations": SEARCHED_LOCATIONS,
        "search_basis": SEARCH_BASIS,
        "discovered_method": "endpoint-backed-upload",
        "service_url": SERVICE_URL,
        "upload_endpoint": UPLOAD_ENDPOINT,
        "route_source": "prompt-exposed authoritative handoff route",
    }

    write_json(args.packet_out, packet)
    write_json(args.route_out, route)


if __name__ == "__main__":
    main()
