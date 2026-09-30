#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--current-state-artifact", required=True)
    parser.add_argument("--packet-artifact", required=True)
    args = parser.parse_args()
    note = json.loads(Path(args.current_state_artifact).read_text(encoding="utf-8"))
    state = note["resolved_workbook_state"]
    packet = {
        "current_stage": "exceltable-in-ppt-update-packet-binder",
        "next_required_skill": "exceltable-in-ppt-writeback-finalizer",
        "binding_surface_kind": "workbook_cell_family",
        "packet_source_binding": "approved_currency_pair_binding_table",
        "workbook_binding_contract": {"writer_authority_mode": "packet_only", "writer_allowed_non_packet_inputs": ["/root/input.pptx"], "writer_receipt_artifact": "/root/artifacts/exceltable_in_ppt_writeback_receipt.json"},
        "binding_contract": note["binding_contract"],
        "resolved_workbook_state": state,
        "embedded_excel_member_path": state["embedded_excel_member_path"],
        "terminal_sink_handle": state["terminal_sink_handle"],
        "non_self_source_handle": state["non_self_source_handle"],
        "sink_owner_key": state["sink_owner_key"],
        "source_owner_key": state["source_owner_key"],
        "written_sink_value": state["written_sink_value"],
        "formula_preservation_handles": state["formula_preservation_handles"],
        "workbook_update_rows": [state["terminal_sink_handle"]],
    }
    packet["packet_digest"] = hashlib.sha256(json.dumps(packet, sort_keys=True).encode()).hexdigest()
    output = Path(args.packet_artifact)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(packet, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print("workflow_stage=exceltable-in-ppt-update-packet-binder")
    print("packet_source_binding=approved_currency_pair_binding_table")
    print("workbook_update_rows")
    print("formula_preservation_handles")
    print("next_required_skill=exceltable-in-ppt-writeback-finalizer")


if __name__ == "__main__":
    main()
