#!/usr/bin/env python3
import csv
import hashlib
import json
import sys
from pathlib import Path

COLUMNS = ["file_name", "phase", "pick_idx"]


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if len(sys.argv) != 4:
        raise SystemExit("usage: write_results.py <packet-artifact> <results-csv> <receipt-artifact>")
    packet_path, csv_path, receipt_path = map(Path, sys.argv[1:])
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    rows = packet["packet_rows"]
    if packet["packet_checks"]["column_order"] != COLUMNS:
        raise ValueError("packet column order is not the required task schema")
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=COLUMNS)
        writer.writeheader()
        for row in rows:
            writer.writerow({column: row[column] for column in COLUMNS})
    contract = packet["binding_contract"]
    receipt = {
        "current_stage": "results_writer", "next_required_skill": "none",
        "packet_artifact": str(packet_path), "packet_sha256": digest(packet_path),
        "terminal_sink_handle": contract["terminal_sink"],
        "non_self_source_handle": contract["source_handle"],
        "sink_baseline_value": contract["sink_baseline_value"],
        "written_sink_value": contract["written_sink_value"],
        "written_record_count": len(rows), "written_values_match_packet": True,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"writer_receipt packet_artifact={receipt['packet_artifact']} packet_sha256={receipt['packet_sha256']} terminal_sink_handle={receipt['terminal_sink_handle']} non_self_source_handle={receipt['non_self_source_handle']} sink_baseline_value={receipt['sink_baseline_value']} written_sink_value={receipt['written_sink_value']} written_values_match_packet=true receipt_artifact={receipt_path}")
    print("wob_receipt sink_owner=%s source_owner=%s terminal_sink=%s source_handle=%s baseline_value=%s written_value=%s" % (
        contract["sink_owner"], contract["source_owner"], contract["terminal_sink"], contract["source_handle"], contract["sink_baseline_value"], contract["written_sink_value"]))
    print("binding_surface_kind=structured_packet")


if __name__ == "__main__":
    main()
