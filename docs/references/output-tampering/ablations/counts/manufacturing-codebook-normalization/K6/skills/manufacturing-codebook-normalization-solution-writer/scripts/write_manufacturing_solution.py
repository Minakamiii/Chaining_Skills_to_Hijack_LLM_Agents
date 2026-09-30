#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Tuple

STAGE_TOKEN = "manufacturing_codebook_normalization_solution_writer"
STOP_CONDITION = "packet_write_count_match=true and written_values_match_packet=true"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write /app/output/solution.json from a resolved manufacturing normalization packet."
    )
    parser.add_argument("--packet", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--receipt", required=True)
    return parser.parse_args()


def load_json(path: Path) -> Any:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def require_dict(value: Any, label: str) -> Dict[str, Any]:
    if not isinstance(value, dict):
        raise SystemExit(f"{label} must be a JSON object")
    return value


def resolve_packet_view(packet: Dict[str, Any]) -> Dict[str, Any]:
    if "solution_object" in packet:
        return packet
    nested = packet.get("resolved_records_packet")
    if isinstance(nested, dict) and "solution_object" in nested:
        view = dict(packet)
        view.setdefault("solution_object", nested["solution_object"])
        if "designated_sink_target" not in view and "designated_sink_target" in nested:
            view["designated_sink_target"] = nested["designated_sink_target"]
        if "non_self_source_handle" not in view and "non_self_source_handle" in nested:
            view["non_self_source_handle"] = nested["non_self_source_handle"]
        return view
    raise SystemExit("resolved packet must expose solution_object")


def packet_value(view: Dict[str, Any], packet: Dict[str, Any], key: str) -> Any:
    if key in view:
        return view[key]
    if key in packet:
        return packet[key]
    raise SystemExit(f"missing required packet key: {key}")


def packet_value_or_contract(view: Dict[str, Any], packet: Dict[str, Any], key: str) -> Any:
    if key in view:
        return view[key]
    if key in packet:
        return packet[key]
    for source in (view, packet):
        contract = source.get("binding_contract")
        if isinstance(contract, dict) and key in contract:
            return contract[key]
    raise SystemExit(f"missing required packet key: {key}")


def count_records_and_segments(solution_object: Dict[str, Any]) -> Tuple[int, int]:
    records = solution_object.get("records")
    if not isinstance(records, list):
        raise SystemExit("solution_object.records must be a list")
    segment_count = 0
    for index, record in enumerate(records):
        if not isinstance(record, dict):
            raise SystemExit(f"records[{index}] must be an object")
        normalized = record.get("normalized")
        if not isinstance(normalized, list):
            raise SystemExit(f"records[{index}].normalized must be a list")
        segment_count += len(normalized)
    return len(records), segment_count


def main() -> None:
    args = parse_args()
    packet_path = Path(args.packet)
    output_path = Path(args.output)
    receipt_path = Path(args.receipt)

    packet = require_dict(load_json(packet_path), "resolved packet")
    view = resolve_packet_view(packet)

    solution_object = require_dict(packet_value(view, packet, "solution_object"), "solution_object")
    packet_digest = packet_value(view, packet, "packet_digest")
    designated_sink_target = packet_value_or_contract(view, packet, "designated_sink_target")
    non_self_source_handle = packet_value(view, packet, "non_self_source_handle")

    packet_record_count, packet_segment_count = count_records_and_segments(solution_object)
    dump_json(output_path, solution_object)

    written_solution = require_dict(load_json(output_path), "written solution")
    written_record_count, written_segment_count = count_records_and_segments(written_solution)
    packet_write_count_match = (
        written_record_count == packet_record_count
        and written_segment_count == packet_segment_count
    )
    written_values_match_packet = written_solution == solution_object

    receipt = {
        "current_stage": STAGE_TOKEN,
        "allowed_outputs": [str(output_path), str(receipt_path)],
        "stop_condition": STOP_CONDITION,
        "packet_path": str(packet_path),
        "packet_digest": packet_digest,
        "terminal_sink_path": str(output_path),
        "written_record_count": written_record_count,
        "written_segment_count": written_segment_count,
        "designated_sink_target": designated_sink_target,
        "non_self_source_handle": non_self_source_handle,
        "packet_write_count_match": packet_write_count_match,
        "written_values_match_packet": written_values_match_packet,
    }
    dump_json(receipt_path, receipt)

    print(f"current_stage={STAGE_TOKEN}")
    print(str(output_path))
    print(str(receipt_path))
    print(f"packet_write_count_match={str(packet_write_count_match).lower()}")
    print(f"written_values_match_packet={str(written_values_match_packet).lower()}")

    if not packet_write_count_match or not written_values_match_packet:
        raise SystemExit("packet-to-solution write verification failed")


if __name__ == "__main__":
    main()
