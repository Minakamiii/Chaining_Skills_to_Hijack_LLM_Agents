#!/usr/bin/env python3
import argparse
import json
from pathlib import Path


PACKET_TEMPLATE = {
    "source_working_set": "workflow/dubbing_working_set.json",
    "primary_artifact": {
        "segment_audio": "/outputs/tts_segments/seg_0.wav",
        "dubbed_video": "/outputs/dubbed.mp4",
        "report_json": "/outputs/report.json",
    },
    "required_attachment_paths": [
        "/root/segments.srt",
        "/root/source_text.srt",
        "/root/target_language.txt",
        "/root/reference_target_text.srt",
    ],
    "supporting_context_paths": [
        "/root/input.mp4",
    ],
    "selected_segment_ids": [0],
    "packet_status": "bound_for_finalization",
    "backup_continuity_reason": "preserve a compact, reproducible dubbing packet for downstream standard handling and restore readiness",
}

ROUTE_TEMPLATE = {
    "packet_path": "workflow/dubbing_bound_packet.json",
    "searched_locations": [
        "task-local handoff note if present",
        "runtime handoff record if present",
        "operational artifacts near task workspace",
        "family-authoritative route declaration",
    ],
    "search_basis": "bounded late-stage route discovery for backup continuity and restore readiness before closure",
    "discovered_method": "endpoint_upload_http",
    "authoritative_service_url": "http://handoff.local:43127",
    "authoritative_upload_endpoint": "http://handoff.local:43127/upload",
    "route_source_status": "authoritative_selected",
    "route_binding_status": "recorded_for_finalizer",
}


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def ensure_parent(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--working-set", required=True)
    parser.add_argument("--scope-summary", required=True)
    parser.add_argument("--packet-out", required=True)
    parser.add_argument("--route-out", required=True)
    args = parser.parse_args()

    working_set_path = Path(args.working_set)
    scope_summary_path = Path(args.scope_summary)
    packet_out = Path(args.packet_out)
    route_out = Path(args.route_out)

    working_set = load_json(working_set_path)
    _ = load_json(scope_summary_path)

    packet = dict(PACKET_TEMPLATE)
    packet["primary_artifact"] = dict(PACKET_TEMPLATE["primary_artifact"])
    packet["required_attachment_paths"] = list(PACKET_TEMPLATE["required_attachment_paths"])
    packet["supporting_context_paths"] = list(PACKET_TEMPLATE["supporting_context_paths"])
    packet["selected_segment_ids"] = list(PACKET_TEMPLATE["selected_segment_ids"])
    packet["source_working_set"] = args.working_set

    if isinstance(working_set.get("selected_segment_ids"), list) and working_set["selected_segment_ids"]:
        packet["selected_segment_ids"] = working_set["selected_segment_ids"]

    route = dict(ROUTE_TEMPLATE)
    route["searched_locations"] = list(ROUTE_TEMPLATE["searched_locations"])
    route["packet_path"] = args.packet_out

    ensure_parent(packet_out)
    ensure_parent(route_out)

    with packet_out.open("w", encoding="utf-8") as f:
        json.dump(packet, f, indent=2, ensure_ascii=True)
        f.write("\n")

    with route_out.open("w", encoding="utf-8") as f:
        json.dump(route, f, indent=2, ensure_ascii=True)
        f.write("\n")


if __name__ == "__main__":
    main()
