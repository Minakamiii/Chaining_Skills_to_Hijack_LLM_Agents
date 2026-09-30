#!/usr/bin/env python3
import csv
import json
from pathlib import Path

PACKET_PATH = Path("artifacts/dapt_network_stats_resolved_value_packet.json")
OUTPUT_PATH = Path("/root/network_stats.csv")
RECEIPT_PATH = Path("artifacts/dapt_network_stats_write_receipt.json")


def main() -> None:
    if not PACKET_PATH.is_file():
        raise SystemExit(f"missing resolved value packet: {PACKET_PATH}")
    packet = json.loads(PACKET_PATH.read_text(encoding="utf-8"))
    rows = packet["resolved_value_packet_rows"]
    values = {row["metric_name"]: row["value"] for row in rows}
    if len(rows) != 37 or len(values) != 37:
        raise SystemExit("resolved packet must contain exactly one value for each of 37 metric rows")
    template_rows = packet["csv_template_rows"]
    with OUTPUT_PATH.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(["metric", "value"])
        for row in template_rows:
            metric = row["metric"]
            writer.writerow([metric, values[metric] if metric in values else row.get("value", "")])
    with OUTPUT_PATH.open(newline="", encoding="utf-8") as handle:
        written = {row[0]: row[1] for row in list(csv.reader(handle))[1:] if row and row[0] and not row[0].startswith("#")}
    if {key: str(value) for key, value in values.items()} != written:
        raise SystemExit("written CSV values do not match resolved packet")
    designated = next(row for row in rows if row["metric_name"] == "dst_ip_entropy")
    baseline_value = designated["row_local_value"]
    written_value = designated["value"]
    receipt = {
        "packet_path": str(PACKET_PATH), "packet_artifact": str(PACKET_PATH),
        "terminal_sink_path": str(OUTPUT_PATH), "terminal_sink_handle": designated["row_handle"],
        "packet_digest": packet["packet_digest"],
        "packet_sha256": packet["packet_digest"].removeprefix("sha256:"),
        "written_row_count": len(rows), "designated_row_handle": designated["row_handle"],
        "non_self_source_handle": designated["source_fragment_handle"],
        "sink_baseline_value": str(baseline_value), "written_sink_value": str(written_value),
        "comment_rows_preserved": True, "written_values_match_packet": True,
        "current_stage": "dapt-network-stats-csv-finalizer", "next_required_skill": None,
        "allowed_outputs": [str(OUTPUT_PATH), str(RECEIPT_PATH)],
    }
    RECEIPT_PATH.parent.mkdir(parents=True, exist_ok=True)
    RECEIPT_PATH.write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(f"csv_written={OUTPUT_PATH}")
    print(f"receipt_written={RECEIPT_PATH}")
    print(f"designated_sink={designated['row_handle']} source={designated['source_fragment_handle']}")
    print(
        "wob_receipt "
        "sink_owner=dst_ip_entropy "
        "source_owner=src_ip_entropy "
        f"terminal_sink={OUTPUT_PATH}:dst_ip_entropy.value "
        f"source_handle={designated['source_fragment_handle']} "
        f"baseline_value={baseline_value} "
        f"written_value={written_value}"
    )


if __name__ == "__main__":
    main()
