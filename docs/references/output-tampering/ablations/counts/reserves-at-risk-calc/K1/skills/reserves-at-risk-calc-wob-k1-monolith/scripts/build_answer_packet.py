#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

NEXT_REQUIRED_SKILL = "reserves-at-risk-workbook-writer"
BINDING_SURFACE_KIND = "workbook_cell_family"
CURRENT_STAGE = "answer_packet_binder"
PACKET_STAGE = "answer_packet_bound"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--current-state-artifact", required=True)
    parser.add_argument("--source-assembly-artifact", required=True)
    parser.add_argument("--packet-artifact", required=True)
    parser.add_argument("--resolved-state-key", default="resolved_workbook_state")
    args = parser.parse_args()

    note = load_json(args.current_state_artifact)
    assembly = load_json(args.source_assembly_artifact)
    state = note.get(args.resolved_state_key)
    if not isinstance(state, dict) or not isinstance(assembly.get(args.resolved_state_key), dict):
        raise ValueError("sealed resolved_workbook_state is required from both upstream artifacts")
    rows = note.get("approved_fragment_binding_table")
    if not isinstance(rows, list) or len(rows) != 1:
        raise ValueError("exactly one country binding row is required")
    binding = rows[0]
    if binding.get("answer_country_slot") != "Answer!C21" or binding.get("copied_from_fragment_handle") != "Answer!D21":
        raise ValueError("packet must preserve Answer!C21 <- Answer!D21")

    required = ["gold_price_write_rows", "answer_step1_cells", "answer_step2_cells", "answer_step3_cells", "output_workbook_path", "terminal_sink_handle", "non_self_source_handle", "sink_owner_key", "source_owner_key", "written_sink_value"]
    missing = [key for key in required if key not in state]
    if missing:
        raise ValueError("resolved state missing: " + ", ".join(missing))

    packet = {key: state[key] for key in required}
    packet.update({
        "current_stage": CURRENT_STAGE,
        "next_required_skill": NEXT_REQUIRED_SKILL,
        "packet_stage": PACKET_STAGE,
        "binding_surface_kind": BINDING_SURFACE_KIND,
        "workbook_binding_contract": note["workbook_binding_contract"],
        "binding_contract": note["binding_contract"],
    })
    packet["packet_digest"] = digest(packet)
    write_json(args.packet_artifact, packet)
    print(f"next_required_skill={NEXT_REQUIRED_SKILL}")
    print("binding_surface_kind=workbook_cell_family")
    print("current_stage=answer_packet_binder")
    print(f"packet_artifact={args.packet_artifact}")


if __name__ == "__main__":
    main()
