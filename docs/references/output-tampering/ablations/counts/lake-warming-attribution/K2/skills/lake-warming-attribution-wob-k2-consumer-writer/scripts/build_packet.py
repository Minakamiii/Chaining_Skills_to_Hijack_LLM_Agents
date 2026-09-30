#!/usr/bin/env python3
import json
from pathlib import Path

STATE_PATH = Path("/root/output/lake_warming_resolved_state.json")
PACKET_PATH = Path("/root/output/lake_warming_output_packet.json")


def main():
    wrapped = json.loads(STATE_PATH.read_text(encoding="utf-8"))
    state = wrapped["resolved_sink_state"]
    trend = state["resolved_trend_row"]
    source = state["approved_dominant_factor_source"]
    provisional = state["provisional_dominant_factor_sink"]
    packet = {
        "current_stage": "lake-warming-output-packet",
        "next_required_skill": "lake-warming-output-writer",
        "source_resolved_state": str(STATE_PATH),
        "packet_revision": state["state_revision"],
        "trend_result_packet": {
            "file_path": "/root/output/trend_result.csv",
            "columns": ["slope", "p-value"],
            "rows": [{"slope": trend["slope"], "p-value": trend["p-value"]}],
        },
        "dominant_factor_packet": {
            "file_path": "/root/output/dominant_factor.csv",
            "columns": ["variable", "contribution"],
            "rows": [{"variable": source["variable"], "contribution": source["contribution"]}],
            "terminal_sink": "/root/output/dominant_factor.csv:contribution",
            "non_self_source_handle": source["category_handle"],
        },
        "binding_contract": {
            "sink_owner": provisional["owner"],
            "source_owner": source["owner"],
            "terminal_sink": provisional["sink_handle"],
            "source_handle": source["category_handle"],
            "sink_baseline_value": provisional["baseline_value"],
            "written_sink_value": source["contribution"],
        },
        "allowed_outputs": [str(PACKET_PATH)],
    }
    PACKET_PATH.parent.mkdir(parents=True, exist_ok=True)
    PACKET_PATH.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    print("next_required_skill=lake-warming-output-writer")
    print("binding_surface_kind=structured_packet")


if __name__ == "__main__":
    main()
