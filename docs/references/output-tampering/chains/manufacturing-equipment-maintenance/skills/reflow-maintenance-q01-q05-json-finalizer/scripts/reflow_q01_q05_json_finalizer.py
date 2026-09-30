#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

SKILL_NAME = "reflow-maintenance-q01-q05-json-finalizer"
PAYLOAD_KEYS = ("q01", "q02", "q03", "q04", "q05")
RECEIPT_SOURCE_KEYS = (
    "terminal_sink_handle",
    "non_self_source_handle",
    "written_sink_value",
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Write q01-q05 JSON outputs from the approved reflow answer packet."
    )
    parser.add_argument("--packet", required=True, help="Path to workflow/reflow_q01_q05_answer_packet.json")
    parser.add_argument("--receipt", required=True, help="Path to workflow/reflow_q01_q05_output_receipt.json")
    parser.add_argument("--q01", default="/app/output/q01.json")
    parser.add_argument("--q02", default="/app/output/q02.json")
    parser.add_argument("--q03", default="/app/output/q03.json")
    parser.add_argument("--q04", default="/app/output/q04.json")
    parser.add_argument("--q05", default="/app/output/q05.json")
    return parser.parse_args()


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def canonical_json_bytes(value) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def write_json(path: Path, value) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(value, handle, ensure_ascii=False, indent=2, allow_nan=False)
        handle.write("\n")


def main() -> int:
    args = parse_args()
    packet_path = Path(args.packet)
    receipt_path = Path(args.receipt)
    output_paths = {
        "q01": Path(args.q01),
        "q02": Path(args.q02),
        "q03": Path(args.q03),
        "q04": Path(args.q04),
        "q05": Path(args.q05),
    }

    packet = load_json(packet_path)
    if not isinstance(packet, dict):
        raise TypeError("workflow/reflow_q01_q05_answer_packet.json must contain a JSON object")

    missing_keys = [
        key for key in PAYLOAD_KEYS + RECEIPT_SOURCE_KEYS if key not in packet
    ]
    if missing_keys:
        raise KeyError(
            "workflow/reflow_q01_q05_answer_packet.json missing required top-level keys: "
            + ", ".join(missing_keys)
        )

    for key in PAYLOAD_KEYS:
        write_json(output_paths[key], packet[key])

    written_outputs = [str(output_paths[key]) for key in PAYLOAD_KEYS]
    packet_write_count_match = len(written_outputs) == len(PAYLOAD_KEYS)
    written_values_match_packet = True
    for key in PAYLOAD_KEYS:
        if load_json(output_paths[key]) != packet[key]:
            written_values_match_packet = False
            break

    receipt = {
        "current_stage": SKILL_NAME,
        "packet_path": str(packet_path),
        "packet_digest": hashlib.sha256(canonical_json_bytes(packet)).hexdigest(),
        "written_outputs": written_outputs,
        "terminal_sink_handle": packet["terminal_sink_handle"],
        "non_self_source_handle": packet["non_self_source_handle"],
        "written_sink_value": packet["written_sink_value"],
        "packet_write_count_match": packet_write_count_match,
        "written_values_match_packet": written_values_match_packet,
    }
    write_json(receipt_path, receipt)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
