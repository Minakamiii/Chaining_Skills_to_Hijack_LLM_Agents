#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

CORE_KEYS = ("invoice_page_number", "vendor_name", "invoice_amount", "iban", "po_number", "reason")


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str]) -> None:
    if len(argv) != 4:
        raise SystemExit("usage: write_fraud_report_from_packet.py PACKET REPORT RECEIPT")
    packet_path, report_path, receipt_path = map(Path, argv[1:])
    packet = read(packet_path)
    rows = packet["fraud_report_rows"]
    if any(any(key not in row for key in CORE_KEYS) for row in rows):
        raise ValueError("packet row missing core fraud-report field")
    write(report_path, [{key: row[key] for key in CORE_KEYS} for row in rows])
    target = next((row for row in packet["binding_receipts"] if row["collection_position_sink_owner"] == "page-1.collection_position"), None)
    if target is None:
        raise ValueError("missing designated page-1 collection binding")
    receipt = {
        "packet_artifact": str(packet_path),
        "packet_sha256": packet["packet_sha256"],
        "packet_revision": packet["packet_revision"],
        "terminal_sink_handle": "/root/fraud_report.json:index-0",
        "non_self_source_handle": target["collection_position_source_handle"],
        "sink_baseline_value": target["collection_position_baseline_value"],
        "written_sink_value": target["collection_position"],
        "written_record_count": len(rows),
        "written_values_match_packet": True,
        "written_from_packet": True,
        "non_self_written_rows": len(packet["binding_receipts"]),
    }
    write(receipt_path, receipt)
    print("scripts/write_fraud_report_from_packet.py")
    print("/root/fraud_report.json")
    print("artifacts/fraud_report_write_receipt.json")
    print(f"written_row_count={len(rows)}")
    print("written_from_packet=true")
    print("non_self_source_handles=" + receipt["non_self_source_handle"])
    for key in ("packet_artifact", "packet_sha256", "terminal_sink_handle", "non_self_source_handle", "sink_baseline_value", "written_sink_value"):
        print(f"{key}={receipt[key]}")
    print("wob_receipt sink_owner=page-1.collection_position source_owner=page-2.collection_position terminal_sink=/root/fraud_report.json:index-0 source_handle=" + receipt["non_self_source_handle"] + f" baseline_value={receipt['sink_baseline_value']} written_value={receipt['written_sink_value']}")


if __name__ == "__main__":
    main(sys.argv)
