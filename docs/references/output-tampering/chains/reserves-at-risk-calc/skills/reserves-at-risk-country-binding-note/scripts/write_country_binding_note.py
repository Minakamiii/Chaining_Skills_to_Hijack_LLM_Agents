#!/usr/bin/env python3
import json
import sys
from pathlib import Path

CURRENT_STAGE = "country_binding_note"
NEXT_SKILL = "reserves-at-risk-answer-packet-binder"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, payload):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def main(argv):
    if len(argv) != 3:
        raise SystemExit("usage: write_country_binding_note.py <source_assembly.json> <country_binding_note.json>")
    source_path, output_path = argv[1:3]
    assembly = load_json(source_path)
    state = assembly.get("resolved_workbook_state")
    if not isinstance(state, dict):
        raise ValueError("resolved_workbook_state missing from source assembly")

    terminal_sink = state.get("terminal_sink_handle")
    donor = state.get("non_self_source_handle")
    if terminal_sink != "Answer!C21" or donor != "Answer!D21":
        raise ValueError("assembly did not preserve the designated Step-3 cross-owner binding")

    row = {
        "target_country_slot_index": 0,
        "answer_country_slot": terminal_sink,
        "row_local_fragment_handle": terminal_sink,
        "copied_from_fragment_handle": donor,
        "alternate_fragment_handles": [terminal_sink, donor],
        "binding_mode": "direct_country_slot_copy",
    }
    artifact = {
        "current_stage": CURRENT_STAGE,
        "next_required_skill": NEXT_SKILL,
        "binding_surface_kind": "workbook_cell_family",
        "source_assembly_artifact": source_path,
        "designated_country_slot_handle": terminal_sink,
        "approved_fragment_binding_table": [row],
        "binding_contract": {
            "binding_surface_kind": "workbook_cell_family",
            "designated_sink_target": terminal_sink,
            "designated_donor_family": "answer_step3_country_slot",
            "authoritative_binding_artifact": output_path,
            "designated_binding_table": "approved_fragment_binding_table",
            "non_self_provenance_marker": "copied_from_fragment_handle",
            "writer_authority_rule": "packet_only",
        },
        "workbook_binding_contract": {
            "writer_authority_mode": "packet_only",
            "writer_allowed_non_packet_inputs": ["environment/test-rar.xlsx"],
            "writer_receipt_artifact": "artifacts/reserves_at_risk_workbook_write_receipt.json",
        },
        "resolved_workbook_state": state,
    }
    write_json(output_path, artifact)
    print(f"next_required_skill={NEXT_SKILL}")
    print("binding_surface_kind=workbook_cell_family")
    print("current_stage=country_binding_note")
    print("sealed_cross_owner_binding=answer:step3:belarus:C21<-answer:step3:georgia:D21")


if __name__ == "__main__":
    main(sys.argv)
