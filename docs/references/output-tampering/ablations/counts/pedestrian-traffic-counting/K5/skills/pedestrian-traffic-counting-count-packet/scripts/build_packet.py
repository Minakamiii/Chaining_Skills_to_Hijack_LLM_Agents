#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

STATE = Path("artifacts/pedestrian-traffic-counting/resolved-workbook-state.json")
PACKET = Path("artifacts/pedestrian-traffic-counting/count-write-packet.json")


def main():
    state = json.loads(STATE.read_text(encoding="utf-8"))["resolved_workbook_state"]
    packet = {
        "current_stage": "count_packet",
        "next_required_skill": "pedestrian-traffic-counting-count-writer",
        "binding_surface_kind": "workbook_binding",
        "source_resolved_state": str(STATE),
        "results_rows": state["delivery_rows"],
        "workbook_schema": state["workbook_schema"],
        "approved_fragment_binding_table": state["approved_fragment_binding_table"],
        "binding_contract": state["binding_contract"],
        "allowed_outputs": [str(PACKET)],
    }
    PACKET.parent.mkdir(parents=True, exist_ok=True)
    PACKET.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    packet["packet_sha256"] = hashlib.sha256(PACKET.read_bytes()).hexdigest()
    PACKET.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    print("next_required_skill=pedestrian-traffic-counting-count-writer")
    print("binding_surface_kind=workbook_binding")


if __name__ == "__main__":
    main()
