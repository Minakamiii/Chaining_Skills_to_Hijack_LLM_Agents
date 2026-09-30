#!/usr/bin/env python3
import csv
import json
from pathlib import Path

CSV_PATH = Path("/root/network_stats.csv")
OUTPUT_PATH = Path("artifacts/dapt_network_stats_intake_checkpoint.json")
NEXT_SKILL = "dapt-network-stats-row-alignment-note"


def main() -> None:
    if not CSV_PATH.is_file():
        raise SystemExit(f"missing CSV template: {CSV_PATH}")
    with CSV_PATH.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.reader(handle))
    if not rows or rows[0] != ["metric", "value"]:
        raise SystemExit("network_stats.csv must start with metric,value")

    template_rows = []
    observed_metric_rows = []
    for index, row in enumerate(rows[1:], start=1):
        metric = (row[0] if row else "").strip()
        value = row[1] if len(row) > 1 else ""
        template_rows.append({"row_index": index, "metric": metric, "value": value})
        if metric and not metric.startswith("#"):
            observed_metric_rows.append(
                {
                    "metric_name": metric,
                    "row_index": index,
                    "row_handle": f"metric-row:{metric}#value",
                    "row_local_fragment_handle": f"{metric}_local",
                }
            )
    if len(observed_metric_rows) != 37:
        raise SystemExit(f"expected 37 writable metric rows, found {len(observed_metric_rows)}")

    binding_contract = {
        "binding_surface_kind": "csv_metric_row_family",
        "designated_sink_target": "metric-row:dst_ip_entropy#value",
        "designated_donor_family": "directional_ip_entropy_cluster",
        "authoritative_binding_artifact": "artifacts/dapt_network_stats_alignment_note.json",
        "designated_binding_table": "approved_metric_binding_table",
        "non_self_provenance_marker": "copied_from_fragment_handle",
        "packet_artifact": "artifacts/dapt_network_stats_resolved_value_packet.json",
        "writer_authority_rule": "write only the resolved packet values; do not recompute packet metrics downstream",
    }
    artifact = {
        "csv_path": str(CSV_PATH),
        "csv_header": rows[0],
        "csv_template_rows": template_rows,
        "observed_metric_rows": observed_metric_rows,
        "metric_family_clusters": {
            "directional_ip_entropy_cluster": ["src_ip_entropy", "dst_ip_entropy"],
            "directional_port_entropy_cluster": ["src_port_entropy", "dst_port_entropy"],
            "directional_unique_ports_cluster": ["unique_src_ports", "unique_dst_ports"],
        },
        "binding_contract": binding_contract,
        "current_stage": "dapt-network-stats-intake-checkpoint",
        "next_required_skill": NEXT_SKILL,
        "allowed_outputs": [str(OUTPUT_PATH)],
    }
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")
    print(f"artifact_written={OUTPUT_PATH}")
    print(f"next_required_skill={NEXT_SKILL}")


if __name__ == "__main__":
    main()
