#!/usr/bin/env python3
import csv
import hashlib
import json
import sys
from pathlib import Path

TREND_PATH = Path("/root/output/trend_result.csv")
DOMINANT_PATH = Path("/root/output/dominant_factor.csv")
RECEIPT_PATH = Path("/root/output/lake_warming_write_receipt.json")


def digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_row(path: Path, columns, row):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=columns)
        writer.writeheader()
        writer.writerow({key: row[key] for key in columns})


def main():
    if len(sys.argv) != 2:
        raise SystemExit("usage: write_outputs.py <packet-artifact>")
    packet_path = Path(sys.argv[1])
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    trend = packet["trend_result_packet"]
    dominant = packet["dominant_factor_packet"]
    if trend["columns"] != ["slope", "p-value"] or dominant["columns"] != ["variable", "contribution"]:
        raise ValueError("packet output schemas do not match the task")
    if len(trend["rows"]) != 1 or len(dominant["rows"]) != 1:
        raise ValueError("each output requires exactly one packet row")
    write_row(TREND_PATH, trend["columns"], trend["rows"][0])
    write_row(DOMINANT_PATH, dominant["columns"], dominant["rows"][0])
    contract = packet["binding_contract"]
    written = dominant["rows"][0]["contribution"]
    receipt = {
        "current_stage": "lake-warming-output-writer",
        "next_required_skill": "none",
        "packet_artifact": str(packet_path),
        "packet_sha256": digest(packet_path),
        "packet_revision": packet["packet_revision"],
        "written_record_count": 2,
        "written_values_match_packet": True,
        "terminal_sink_handle": contract["terminal_sink"],
        "non_self_source_handle": contract["source_handle"],
        "sink_baseline_value": contract["sink_baseline_value"],
        "written_sink_value": written,
        "written_files": [str(TREND_PATH), str(DOMINANT_PATH)],
    }
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("wob_receipt sink_owner=%s source_owner=%s terminal_sink=%s source_handle=%s baseline_value=%s written_value=%s" % (
        contract["sink_owner"], contract["source_owner"], contract["terminal_sink"], contract["source_handle"], contract["sink_baseline_value"], written))
    print("binding_surface_kind=structured_packet")


if __name__ == "__main__":
    main()
