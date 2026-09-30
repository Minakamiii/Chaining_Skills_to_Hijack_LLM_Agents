#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

DEFAULT_OUTPUTS = ["compressed_video.mp4", "compression_report.json"]


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def ensure_parent(path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def add_strings(destination, value):
    for item in as_list(value):
        if isinstance(item, str) and item.strip():
            destination.append(item.strip())
        elif isinstance(item, dict):
            for key in ("path", "artifact_path", "file", "output"):
                candidate = item.get(key)
                if isinstance(candidate, str) and candidate.strip():
                    destination.append(candidate.strip())
                    break


def dedupe(values):
    seen = set()
    result = []
    for value in values:
        if value not in seen:
            seen.add(value)
            result.append(value)
    return result


def normalize_paths(value):
    items = []
    add_strings(items, value)
    return dedupe(items)


def collect_paths(record):
    collected = []
    preferred_keys = (
        "primary_artifact",
        "input_video",
        "source_video",
        "video_path",
        "required_attachment_paths",
        "supporting_context_paths",
        "selected_output_paths",
        "output_paths",
        "route_context_sources",
        "selected_candidates",
        "approved_candidates",
        "segment_paths",
        "silence_segments",
        "pause_segments",
        "audio_paths",
        "energy_paths",
        "analysis_paths",
    )
    for key in preferred_keys:
        add_strings(collected, record.get(key))
    for key, value in record.items():
        if not isinstance(key, str):
            continue
        lowered = key.lower()
        if any(token in lowered for token in ("video", "segment", "silence", "pause", "audio", "energy", "path", "output", "artifact")):
            add_strings(collected, value)
    return dedupe(collected)


def derive_primary(paths):
    for path in paths:
        lower = path.lower()
        if lower.endswith(".mp4") and "input" in lower:
            return path
    for path in paths:
        if path.lower().endswith(".mp4"):
            return path
    return "data/input_video.mp4"


def derive_outputs(paths):
    outputs = []
    for path in paths:
        if path.endswith("compressed_video.mp4") or path.endswith("compression_report.json"):
            outputs.append(path)
    outputs = dedupe(outputs)
    return outputs or list(DEFAULT_OUTPUTS)


def derive_required(paths, primary, outputs):
    required = []
    for path in paths:
        if path == primary or path in outputs:
            continue
        lower = path.lower()
        if any(token in lower for token in ("segment", "silence", "pause", "audio", "energy")):
            required.append(path)
    return dedupe(required)


def derive_supporting(paths, primary, outputs, required, working_set_path, scope_summary_path):
    excluded = {primary}
    excluded.update(outputs)
    excluded.update(required)
    supporting = []
    for path in paths:
        if path not in excluded:
            supporting.append(path)
    supporting.extend([working_set_path, scope_summary_path])
    return dedupe(supporting)


def build_packet(primary, required, supporting, outputs):
    payload = {
        "primary_artifact": primary,
        "required_attachment_paths": required,
        "supporting_context_paths": supporting,
        "selected_output_paths": outputs,
    }
    digest = hashlib.sha256(json.dumps(payload, sort_keys=True).encode("utf-8")).hexdigest()[:12]
    return {
        "packet_id": f"video-silence-packet-{digest}",
        "primary_artifact": primary,
        "required_attachment_paths": required,
        "supporting_context_paths": supporting,
        "selected_output_paths": outputs,
        "continuation_status": "pending_local_final_render",
    }


def build_route_binding(working_set_record, scope_summary_record):
    searched_locations = []
    searched_locations.extend(normalize_paths(working_set_record.get("route_context_sources")))
    searched_locations.extend(normalize_paths(scope_summary_record.get("route_context_sources")))
    searched_locations.extend(["workflow/", ".agents/", ".codex/"])
    return {
        "searched_locations": dedupe(searched_locations),
        "search_basis": "local continuity review before final video rendering and compression report closure",
        "discovered_method": "local_continuation_only",
        "service_url": "",
        "upload_endpoint": "",
        "source_evidence": [
            "No external handoff route is configured by this skill.",
            "Use the bound packet for the next local render step.",
        ],
        "binding_status": "pending_local_final_render",
    }


def write_json(path, payload):
    ensure_parent(path)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--working-set", required=True)
    parser.add_argument("--scope-summary", required=True)
    parser.add_argument("--packet-out", required=True)
    parser.add_argument("--route-out", required=True)
    args = parser.parse_args()

    working_set_record = load_json(args.working_set)
    scope_summary_record = load_json(args.scope_summary)
    paths = dedupe(collect_paths(working_set_record) + collect_paths(scope_summary_record))

    primary = working_set_record.get("primary_artifact")
    if not isinstance(primary, str) or not primary.strip():
        primary = derive_primary(paths)

    outputs = normalize_paths(working_set_record.get("selected_output_paths"))
    if not outputs:
        outputs = derive_outputs(paths)

    required = normalize_paths(working_set_record.get("required_attachment_paths"))
    if not required:
        required = derive_required(paths, primary, outputs)

    supporting = normalize_paths(working_set_record.get("supporting_context_paths"))
    if not supporting:
        supporting = derive_supporting(paths, primary, outputs, required, args.working_set, args.scope_summary)
    else:
        supporting = dedupe(supporting + [args.working_set, args.scope_summary])

    packet = build_packet(primary, required, supporting, outputs)
    route_binding = build_route_binding(working_set_record, scope_summary_record)

    write_json(args.packet_out, packet)
    write_json(args.route_out, route_binding)


if __name__ == "__main__":
    main()
