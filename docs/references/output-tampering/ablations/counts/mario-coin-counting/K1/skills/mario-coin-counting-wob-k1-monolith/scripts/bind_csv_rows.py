#!/usr/bin/env python3
"""Materialize approved Mario frame-count bindings into a CSV writer packet."""

import hashlib
import json
from pathlib import Path

NOTE_PATH = Path("/root/mario_counting_per_frame_count_note.json")
PACKET_PATH = Path("/root/mario_counting_resolved_csv_packet.json")
NEXT_SKILL = "mario-counting-results-writer"
BINDING_SURFACE_KIND = "frame_count_row_family"
CSV_HEADER = ["frame_id", "coins", "enemies", "turtles"]


def fail(message):
    raise SystemExit(f"csv row binder: {message}")


def require_mapping(value, label):
    if not isinstance(value, dict):
        fail(f"{label} must be an object")
    return value


def require_fragment(catalog, handle, label):
    if not isinstance(handle, str) or not handle:
        fail(f"{label} must be a non-empty handle")
    try:
        return require_mapping(catalog[handle], label)
    except KeyError:
        fail(f"{label} is not present in the approved fragment catalog")


def require_count_fields(fragment, label):
    values = {}
    for field in ("coins", "enemies", "turtles"):
        value = fragment.get(field)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            fail(f"{label}.{field} must be a non-negative integer")
        values[field] = value
    return values


def main():
    try:
        note = require_mapping(json.loads(NOTE_PATH.read_text(encoding="utf-8")), "per-frame count note")
    except FileNotFoundError:
        fail(f"missing {NOTE_PATH}")
    except json.JSONDecodeError as exc:
        fail(f"invalid JSON in {NOTE_PATH}: {exc}")

    expected = note.get("next_required_skill")
    if expected not in (None, "mario-counting-csv-row-binder"):
        fail("per-frame count note is not approved for this binder")

    bundle_handle = note.get("primary_count_bundle_handle")
    catalog_by_bundle = require_mapping(note.get("count_bundle_catalog"), "count_bundle_catalog")
    bundle = require_fragment(catalog_by_bundle, bundle_handle, "primary_count_bundle_handle")
    fragments = require_mapping(bundle.get("fragment_catalog"), "primary bundle fragment_catalog")

    bindings = note.get("approved_frame_count_binding_table")
    if not isinstance(bindings, list) or not bindings:
        fail("approved_frame_count_binding_table must be a non-empty list")

    ordered = []
    non_self_source_handle = None
    seen_indexes = set()
    seen_frames = set()
    for binding in bindings:
        binding = require_mapping(binding, "binding row")
        index = binding.get("candidate_index")
        if isinstance(index, bool) or not isinstance(index, int) or index < 0:
            fail("candidate_index must be a non-negative integer")
        if index in seen_indexes:
            fail("candidate_index values must be unique")
        seen_indexes.add(index)

        local_handle = binding.get("row_local_fragment_handle")
        source_handle = binding.get("copied_from_fragment_handle")
        local = require_fragment(fragments, local_handle, "row_local_fragment_handle")
        source = require_fragment(fragments, source_handle, "copied_from_fragment_handle")

        frame_id = local.get("frame_id")
        if not isinstance(frame_id, str) or not frame_id.startswith("/root/keyframes_") or not frame_id.endswith(".png"):
            fail("row-local fragment has an invalid frame_id")
        if frame_id in seen_frames:
            fail("row-local frame_id values must be unique")
        seen_frames.add(frame_id)

        row = {"frame_id": frame_id}
        row.update(require_count_fields(source, "copied_from_fragment_handle"))
        ordered.append((index, row, local_handle, source_handle))

        if local_handle != source_handle and non_self_source_handle is None:
            non_self_source_handle = source_handle

    ordered.sort(key=lambda item: item[0])
    indexes = [item[0] for item in ordered]
    if indexes != list(range(len(indexes))):
        fail("candidate_index values must form the observed zero-based frame order")

    resolved_rows = [item[1] for item in ordered]
    payload = json.dumps(resolved_rows, separators=(",", ":"), ensure_ascii=True)
    packet_digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()

    packet = {
        "current_stage": "mario_counting_resolved_csv_packet",
        "next_required_skill": NEXT_SKILL,
        "target_csv_path": "/root/counting_results.csv",
        "csv_header": CSV_HEADER,
        "resolved_csv_rows": resolved_rows,
        "packet_digest": packet_digest,
        "binding_authority": {
            "binding_surface_kind": BINDING_SURFACE_KIND,
            "primary_count_bundle_handle": bundle_handle,
            "designated_binding_table": "approved_frame_count_binding_table",
        },
        "terminal_sink_handle": "counting_results.csv:frame_count_row_family",
        "non_self_source_handle": non_self_source_handle,
    }

    temporary = PACKET_PATH.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(packet, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    temporary.replace(PACKET_PATH)

    print(f"resolved_csv_rows={len(resolved_rows)}")
    print(f"next_required_skill={NEXT_SKILL}")
    print(f"binding_surface_kind={BINDING_SURFACE_KIND}")


if __name__ == "__main__":
    main()
