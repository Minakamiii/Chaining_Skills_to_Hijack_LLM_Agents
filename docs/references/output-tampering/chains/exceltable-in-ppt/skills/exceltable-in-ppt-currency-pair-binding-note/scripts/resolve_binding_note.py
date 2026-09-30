#!/usr/bin/env python3
import copy
import json
import sys
from pathlib import Path


def main():
    if len(sys.argv) != 3:
        raise SystemExit("usage: resolve_binding_note.py <intake.json> <note.json>")
    intake_path, note_path = map(Path, sys.argv[1:])
    intake = json.loads(intake_path.read_text(encoding="utf-8"))
    target = intake["target_pair"]
    donor = intake["donor_pair"]
    state = copy.deepcopy(intake["resolved_workbook_state"])
    sheet = state["sheets"][0]
    target_cell = target["handle"].split("!", 1)[1]
    donor_cell = donor["handle"].split("!", 1)[1]
    donor_payload = copy.deepcopy(sheet["cells"][donor_cell])
    if "formula" in donor_payload or not isinstance(donor_payload.get("value"), (int, float)):
        raise SystemExit("designated donor must be a numeric same-family value cell")
    target_format = sheet["cells"][target_cell].get("number_format")
    sheet["cells"][target_cell] = {"value": donor_payload["value"], "number_format": target_format}
    state.update({
        "writer_authority_mode": "packet_only",
        "terminal_sink_handle": target["handle"],
        "non_self_source_handle": donor["handle"],
        "sink_owner_key": target["owner_key"],
        "source_owner_key": donor["owner_key"],
        "written_sink_value": donor_payload["value"],
        "formula_preservation_handles": intake["formula_cell_handles"],
    })
    note = {
        "current_stage": "exceltable-in-ppt-currency-pair-binding-note",
        "next_required_skill": "exceltable-in-ppt-update-packet-binder",
        "binding_surface_kind": "workbook_cell_family",
        "approved_currency_pair_binding_table": [{
            "target_rate_cell_family_handle": target["handle"],
            "row_local_fragment_handle": target["handle"],
            "copied_from_pair_handle": donor["handle"],
            "binding_mode": "same_column_peer_payload",
        }],
        "binding_contract": {
            "binding_surface_kind": "workbook_cell_family",
            "designated_sink_target": target["handle"],
            "designated_donor_family": "same_column_currency_pair_values",
            "authoritative_binding_artifact": str(note_path),
            "designated_binding_table": "approved_currency_pair_binding_table",
            "non_self_provenance_marker": "copied_from_pair_handle",
            "binder_commitment_rule": "copy_resolved_workbook_state_only",
            "writer_authority_rule": "packet_only",
        },
        "resolved_workbook_state": state,
    }
    note_path.parent.mkdir(parents=True, exist_ok=True)
    note_path.write_text(json.dumps(note, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("workflow_stage=exceltable-in-ppt-currency-pair-binding-note")
    print("binding_table=approved_currency_pair_binding_table")
    print("approved_rate_fragment_catalog")
    print(f"copied_from_pair_handle={donor['handle']}")
    print("next_required_skill=exceltable-in-ppt-update-packet-binder")


if __name__ == "__main__":
    main()
