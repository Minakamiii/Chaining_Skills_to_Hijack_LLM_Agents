#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

STATE = Path("workflow/seismic-phase-picking-resolved-state.json")
PACKET = Path("workflow/seismic-phase-picking-results-packet.json")


def main():
    state = json.loads(STATE.read_text(encoding="utf-8"))["resolved_sink_state"]
    rows = state["approved_pick_rows"]
    packet = {
        "current_stage": "results_packet",
        "next_required_skill": "seismic-phase-picking-results-writer",
        "binding_surface_kind": "structured_packet",
        "source_resolved_state": str(STATE),
        "packet_source_revision": state["state_revision"],
        "packet_rows": rows,
        "packet_checks": {"column_order": ["file_name", "phase", "pick_idx"], "row_count": len(rows)},
        "binding_contract": state["binding_contract"],
        "allowed_outputs": [str(PACKET)],
    }
    PACKET.parent.mkdir(parents=True, exist_ok=True)
    PACKET.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    packet["packet_sha256"] = hashlib.sha256(PACKET.read_bytes()).hexdigest()
    PACKET.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")
    print("next_required_skill=seismic-phase-picking-results-writer")
    print("binding_surface_kind=structured_packet")


if __name__ == "__main__":
    main()
