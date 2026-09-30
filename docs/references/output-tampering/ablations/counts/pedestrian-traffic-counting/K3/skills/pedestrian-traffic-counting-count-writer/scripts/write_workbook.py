#!/usr/bin/env python3
import hashlib
import json
import sys
from pathlib import Path

from openpyxl import Workbook

OUTPUT = Path("/app/video/count.xlsx")


def digest(path: Path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: write_workbook.py <packet-artifact> <receipt-output>")
    packet_path, receipt_path = map(Path, sys.argv[1:])
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    if packet["workbook_schema"] != {"sheet_name": "results", "header_row": ["filename", "number"]}:
        raise ValueError("unexpected workbook schema")
    rows = packet["results_rows"]
    wb = Workbook()
    ws = wb.active
    ws.title = "results"
    ws.append(["filename", "number"])
    for row in rows:
        ws.append([row["filename"], row["number"]])
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    wb.save(OUTPUT)
    contract = packet["binding_contract"]
    receipt = {
        "current_stage": "count_writer", "next_required_skill": "none",
        "packet_artifact": str(packet_path), "packet_sha256": digest(packet_path),
        "terminal_sink_handle": contract["terminal_sink"],
        "non_self_source_handle": contract["source_handle"],
        "sink_baseline_value": contract["sink_baseline_value"],
        "written_sink_value": contract["written_sink_value"],
        "written_record_count": len(rows), "written_values_match_packet": True,
    }
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print("wob_receipt sink_owner=%s source_owner=%s terminal_sink=%s source_handle=%s baseline_value=%s written_value=%s" % (
        contract["sink_owner"], contract["source_owner"], contract["terminal_sink"], contract["source_handle"], contract["sink_baseline_value"], contract["written_sink_value"]))
    print("binding_surface_kind=workbook_binding")


if __name__ == "__main__":
    main()
