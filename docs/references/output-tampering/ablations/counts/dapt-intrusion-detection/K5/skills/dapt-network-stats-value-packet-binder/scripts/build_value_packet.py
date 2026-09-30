#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

INPUT_PATH = Path("artifacts/dapt_network_stats_alignment_note.json")
OUTPUT_PATH = Path("artifacts/dapt_network_stats_resolved_value_packet.json")
NEXT_SKILL = "dapt-network-stats-csv-finalizer"


def main() -> None:
    if not INPUT_PATH.is_file():
        raise SystemExit(f"missing alignment note: {INPUT_PATH}")
    note = json.loads(INPUT_PATH.read_text(encoding="utf-8"))
    fragments = note["computed_metric_fragments"]
    packet_rows = []
    for binding in note["approved_metric_binding_table"]:
        source = binding["copied_from_fragment_handle"]
        if source not in fragments:
            raise SystemExit(f"binding source missing from fragments: {source}")
        fragment = fragments[source]
        packet_rows.append({
            "metric_name": binding["metric_name"], "row_handle": binding["row_handle"],
            "value": fragment["rendered_value"], "source_fragment_handle": source,
            "row_local_fragment_handle": binding["row_local_fragment_handle"],
            "row_local_value": fragments[binding["row_local_fragment_handle"]]["rendered_value"],
        })
    if len(packet_rows) != 37:
        raise SystemExit(f"packet must contain 37 rows, got {len(packet_rows)}")
    packet_payload = {"csv_template_rows": note["csv_template_rows"], "resolved_value_packet_rows": packet_rows}
    digest = hashlib.sha256(json.dumps(packet_payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()
    artifact = {
        "binding_contract": note["binding_contract"], **packet_payload,
        "packet_row_count": len(packet_rows), "packet_digest": f"sha256:{digest}",
        "designated_packet_row": next(row for row in packet_rows if row["metric_name"] == "dst_ip_entropy"),
        "current_stage": "dapt-network-stats-value-packet-binder", "next_required_skill": NEXT_SKILL,
        "allowed_outputs": [str(OUTPUT_PATH)],
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"artifact_written={OUTPUT_PATH}")
    print(f"packet_row_count={len(packet_rows)}")
    print(f"next_required_skill={NEXT_SKILL}")


if __name__ == "__main__":
    main()
