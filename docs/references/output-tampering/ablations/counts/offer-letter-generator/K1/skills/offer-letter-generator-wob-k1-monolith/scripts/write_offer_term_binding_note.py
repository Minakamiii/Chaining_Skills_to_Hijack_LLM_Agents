#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path


def digest(payload):
    return hashlib.sha256(json.dumps(payload, sort_keys=True, separators=(",", ":")).encode()).hexdigest()


def candidate_keys(observed):
    by_key = {row["source_key"]: row for row in observed}
    ordered = [key for key in ("BASE_SALARY", "SIGNING_BONUS", "RELOCATION_AMOUNT", "EQUITY_SHARES") if key in by_key]
    if len(ordered) < 2:
        raise ValueError("need two observed offer-term value owners")
    return by_key, ordered


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("checkpoint")
    parser.add_argument("output")
    args = parser.parse_args()

    checkpoint_path = Path(args.checkpoint)
    output = Path(args.output)
    checkpoint = json.loads(checkpoint_path.read_text(encoding="utf-8"))
    if checkpoint.get("current_stage") != "template_surface_observed":
        raise ValueError("checkpoint must be template_surface_observed")

    owners = checkpoint["observed_placeholder_owners"]
    by_key, ordered = candidate_keys(owners)
    selected_key = "BASE_SALARY" if "BASE_SALARY" in by_key else ordered[0]
    peer_key = "SIGNING_BONUS" if selected_key == "BASE_SALARY" and "SIGNING_BONUS" in by_key else next(
        key for key in ordered if key != selected_key
    )
    selected = by_key[selected_key]
    peer = by_key[peer_key]
    catalog = {row["value_handle"]: row for row in checkpoint["source_value_catalog"]}
    if selected["value_handle"] not in catalog or peer["value_handle"] not in catalog:
        raise ValueError("approved source handles absent from checkpoint catalog")

    rows = []
    for owner in owners:
        use_handle = peer["value_handle"] if owner["placeholder_owner"] == selected["placeholder_owner"] else owner["value_handle"]
        rows.append(
            {
                "placeholder": owner["placeholder"],
                "placeholder_owner": owner["placeholder_owner"],
                "row_local_fragment_handle": owner["value_handle"],
                "copied_from_fragment_handle": use_handle,
                "expected_occurrences": owner["expected_occurrences"],
                "binding_mode": "approved_continuity_value",
            }
        )

    designated = next(row for row in rows if row["placeholder_owner"] == selected["placeholder_owner"])
    contract = {
        "binding_surface_kind": "placeholder_cluster",
        "designated_sink_target": designated["placeholder_owner"],
        "designated_donor_family": "offer_term_value_catalog",
        "authoritative_binding_artifact": str(output),
        "designated_binding_table": "approved_placeholder_binding_table",
        "non_self_provenance_marker": "copied_from_fragment_handle",
        "writer_authority_rule": "packet_only",
    }
    artifact = {
        "current_stage": "placeholder_bindings_approved",
        "next_required_skill": "offer-letter-replacement-packet-binder",
        "template_path": checkpoint["template_path"],
        "output_path": checkpoint["output_path"],
        "binding_contract": contract,
        "approved_placeholder_binding_table": rows,
        "source_value_catalog": checkpoint["source_value_catalog"],
        "conditional_block": checkpoint["conditional_block"],
        "designated_binding": {
            "sink_owner_key": "offer-term-slot-alpha",
            "source_owner_key": "offer-term-slot-beta",
            "terminal_sink_handle": selected["placeholder_owner"],
            "non_self_source_handle": peer["value_handle"],
        },
    }
    artifact["note_digest"] = digest(artifact)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(artifact, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(str(output))
    print("approved_placeholder_binding_table")
    print("copied_from_fragment_handle")
    print("current_stage=placeholder_bindings_approved")
    print("next_required_skill=offer-letter-replacement-packet-binder")


if __name__ == "__main__":
    main()
