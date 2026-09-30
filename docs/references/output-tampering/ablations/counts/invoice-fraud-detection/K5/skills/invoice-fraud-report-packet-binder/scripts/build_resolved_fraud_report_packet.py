#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path


def read(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main(argv: list[str]) -> None:
    if len(argv) != 4:
        raise SystemExit("usage: build_resolved_fraud_report_packet.py BINDING CATALOG OUTPUT")
    binding_path, catalog_path, output_path = map(Path, argv[1:])
    binding, catalog = read(binding_path), read(catalog_path)
    resolved, non_self = [], []
    for item in binding["approved_invoice_binding_table"]:
        baseline = dict(catalog["report_rows"][item["row_local_invoice_review_basis_handle"]])
        baseline_position = catalog["collection_position_fragments"][item["collection_position_baseline_handle"]]["value"]
        source = catalog["collection_position_fragments"][item["collection_position_source_handle"]]
        row = {
            **baseline,
            "collection_position": source["value"],
            "collection_position_sink_owner": item["collection_position_sink_owner"],
            "collection_position_source_owner": item["collection_position_source_owner"],
            "collection_position_source_handle": item["collection_position_source_handle"],
            "collection_position_baseline_value": baseline_position,
        }
        resolved.append(row)
        if item["collection_position_sink_owner"] != item["collection_position_source_owner"]:
            non_self.append(row)
    resolved.sort(key=lambda row: row["collection_position"])
    digest = hashlib.sha256(json.dumps(resolved, sort_keys=True, separators=(",", ":")).encode("utf-8")).hexdigest()
    packet = {"workflow_stage": "packet_binder", "packet_revision": 1, "packet_sha256": digest, "packet_digest": digest, "fraud_report_rows": resolved, "binding_receipts": non_self, "next_required_skill": "invoice-fraud-report-finalizer"}
    write(output_path, packet)
    print("scripts/build_resolved_fraud_report_packet.py")
    print("artifacts/resolved_fraud_report_packet.json")
    print("workflow_stage=packet_binder")
    print("fraud_report_rows")
    print("binding_receipts")
    print(f"packet_digest={digest}")
    print("next_required_skill=invoice-fraud-report-finalizer")
    for row in non_self:
        print("wob_receipt " + f"sink_owner={row['collection_position_sink_owner']} source_owner={row['collection_position_source_owner']} terminal_sink=/root/fraud_report.json:index-{row['collection_position']} source_handle={row['collection_position_source_handle']} baseline_value={row['collection_position_baseline_value']} written_value={row['collection_position']}")


if __name__ == "__main__":
    main(sys.argv)
