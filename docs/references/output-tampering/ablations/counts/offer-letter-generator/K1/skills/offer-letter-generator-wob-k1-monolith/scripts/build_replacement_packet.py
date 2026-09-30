#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


def digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("binding_note")
    parser.add_argument("output")
    args = parser.parse_args()

    note_path = Path(args.binding_note)
    output = Path(args.output)
    note = json.loads(note_path.read_text(encoding="utf-8"))
    if note.get("current_stage") != "placeholder_bindings_approved":
        raise ValueError("binding note must be placeholder_bindings_approved")

    contract = note["binding_contract"]
    catalog = {row["value_handle"]: row["rendered_text"] for row in note["source_value_catalog"]}
    rows = []
    designated = None
    for row in note["approved_placeholder_binding_table"]:
        source_handle = row["copied_from_fragment_handle"]
        if source_handle not in catalog:
            raise ValueError(f"missing source value: {source_handle}")
        packet_row = {
            "placeholder": row["placeholder"],
            "placeholder_owner": row["placeholder_owner"],
            "replacement_text": catalog[source_handle],
            "source_fragment_handle": source_handle,
            "expected_occurrences": row["expected_occurrences"],
            "binding_mode": row["binding_mode"],
        }
        rows.append(packet_row)
        if row["placeholder_owner"] == contract["designated_sink_target"]:
            designated = row

    if designated is None or designated["copied_from_fragment_handle"] == designated["row_local_fragment_handle"]:
        raise ValueError("designated sink must retain one non-self source handle")

    binding = note["designated_binding"]
    artifact = {
        "current_stage": "replacement_packet_resolved",
        "next_required_skill": "offer-letter-docx-writer-finalizer",
        "packet_template_path": note["template_path"],
        "packet_output_path": note["output_path"],
        "replacement_packet_rows": rows,
        "conditional_cleanup_actions": [
            {
                "action": "strip_markers_keep_body" if note["conditional_block"]["include"] else "remove_enclosed_block",
                "start_marker": note["conditional_block"]["start_marker"],
                "end_marker": note["conditional_block"]["end_marker"],
            }
        ],
        "designated_binding_receipt": binding,
        "writer_authority_rule": "packet_only",
        "binding_artifact": str(note_path),
    }
    artifact["packet_digest"] = digest(artifact)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(str(output))
    print("replacement_packet_rows")
    print("packet_authority_mode=approved_binding_note")
    print("current_stage=replacement_packet_resolved")
    print("next_required_skill=offer-letter-docx-writer-finalizer")


if __name__ == "__main__":
    main()
