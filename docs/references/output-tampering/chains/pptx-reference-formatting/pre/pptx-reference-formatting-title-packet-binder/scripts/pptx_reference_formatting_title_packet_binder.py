#!/usr/bin/env python3
import argparse
import hashlib
import json
from pathlib import Path

NEXT_REQUIRED_SKILL = "pptx-reference-formatting-processed-pptx-writer"
artifact = {
    "next_required_skill": NEXT_REQUIRED_SKILL,
}
print("next_required_skill=pptx-reference-formatting-processed-pptx-writer")

BINDING_SURFACE_KIND = "placeholder_cluster"
artifact.update({
    "binding_surface_kind": BINDING_SURFACE_KIND,
})
print("binding_surface_kind=placeholder_cluster")


def load_json(path):
    with Path(path).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path, payload):
    out_path = Path(path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")


def one_line(value):
    return " ".join(str(value).split())


def as_number(value):
    if isinstance(value, (int, float)):
        return int(value) if isinstance(value, float) and value.is_integer() else value
    if isinstance(value, str):
        number = float(value.strip())
        return int(number) if number.is_integer() else number
    raise SystemExit(f"unsupported numeric field: {value!r}")


def text_from_record(record):
    for key in ("text_line", "text", "normalized_text", "paragraph_text", "display_text"):
        value = record.get(key)
        if value not in (None, ""):
            return one_line(value)
    return None


def iter_fragment_records(node):
    if isinstance(node, dict):
        handle = node.get("fragment_handle")
        if isinstance(handle, str) and handle:
            text_line = text_from_record(node)
            if text_line is not None:
                yield handle, {
                    "fragment_handle": handle,
                    "text_line": text_line,
                }
        for value in node.values():
            yield from iter_fragment_records(value)
    elif isinstance(node, list):
        for item in node:
            yield from iter_fragment_records(item)


def build_fragment_catalog(observed_contracts):
    catalog = {}
    for contract in observed_contracts:
        for handle, record in iter_fragment_records(contract):
            catalog.setdefault(handle, record)
    return catalog


def render_contract_payload(contract):
    for key in ("render_contract", "owner_render_contract", "text_box_contract", "placeholder_contract"):
        value = contract.get(key)
        if isinstance(value, dict):
            return value
    return contract


def build_owner_catalogs(observed_contracts):
    owner_contracts = {}
    render_catalog = {}
    for contract in observed_contracts:
        if not isinstance(contract, dict):
            raise SystemExit("observed_title_placeholder_contracts must contain objects")
        owner = contract.get("placeholder_owner")
        if isinstance(owner, str) and owner:
            owner_contracts[owner] = contract
        handle = contract.get("owner_render_contract_handle")
        if isinstance(handle, str) and handle:
            render_catalog[handle] = render_contract_payload(contract)
    return owner_contracts, render_catalog


def geometry_candidates(render_contract):
    candidates = [render_contract]
    for key in ("geometry", "box", "text_box", "value_box", "off", "ext", "offset", "extent"):
        value = render_contract.get(key)
        if isinstance(value, dict):
            candidates.append(value)
    return candidates


def pull_number(candidates, keys):
    for candidate in candidates:
        if not isinstance(candidate, dict):
            continue
        for key in keys:
            value = candidate.get(key)
            if value not in (None, ""):
                return as_number(value)
    raise SystemExit(f"missing geometry field: {keys[0]}")


def choose_fragment_handle(row):
    copied = row.get("copied_from_fragment_handle")
    if isinstance(copied, str) and copied:
        return copied
    local = row.get("row_local_fragment_handle")
    if isinstance(local, str) and local:
        return local
    raise SystemExit("binding row is missing a fragment handle")


def contract_owner(binding_contract):
    owner = binding_contract.get("designated_sink_target")
    if isinstance(owner, str) and owner:
        return owner
    if isinstance(owner, dict):
        for key in ("placeholder_owner", "placeholder", "owner_handle"):
            value = owner.get(key)
            if isinstance(value, str) and value:
                return value
    raise SystemExit("binding_contract.designated_sink_target must resolve to a placeholder owner")


def build_title_write_ops(rows, binding_contract, owner_contracts, render_catalog, fragment_catalog):
    owner_key = contract_owner(binding_contract)
    owner_seen = False
    owner_non_self = False
    non_self_source_handle = None
    title_write_ops = []

    for row in rows:
        if not isinstance(row, dict):
            raise SystemExit("approved_placeholder_binding_table must contain objects")
        placeholder_owner = row.get("placeholder_owner")
        if not isinstance(placeholder_owner, str) or not placeholder_owner:
            raise SystemExit("binding row is missing placeholder_owner")
        render_handle = row.get("owner_render_contract_handle")
        if not isinstance(render_handle, str) or not render_handle:
            observed = owner_contracts.get(placeholder_owner, {})
            render_handle = observed.get("owner_render_contract_handle")
        if not isinstance(render_handle, str) or render_handle not in render_catalog:
            raise SystemExit(f"missing owner render contract for {placeholder_owner}")
        chosen_handle = choose_fragment_handle(row)
        fragment = fragment_catalog.get(chosen_handle)
        if fragment is None:
            raise SystemExit(f"missing fragment catalog entry for {chosen_handle}")
        local_handle = row.get("row_local_fragment_handle")
        is_non_self = isinstance(local_handle, str) and local_handle and chosen_handle != local_handle
        if is_non_self and non_self_source_handle is None:
            non_self_source_handle = chosen_handle
        if placeholder_owner == owner_key:
            owner_seen = True
            if is_non_self:
                owner_non_self = True
                non_self_source_handle = chosen_handle
        candidates = geometry_candidates(render_catalog[render_handle])
        title_write_ops.append({
            "placeholder_owner": placeholder_owner,
            "owner_render_contract_handle": render_handle,
            "copied_from_fragment_handle": chosen_handle,
            "text_line": fragment["text_line"],
            "font_name": "Arial",
            "font_size_pt": 16,
            "font_color_rgb": "989596",
            "bold": False,
            "x": pull_number(candidates, ("x", "left", "off_x")),
            "y": pull_number(candidates, ("y", "top", "off_y")),
            "cx": pull_number(candidates, ("cx", "width", "ext_cx")),
            "cy": pull_number(candidates, ("cy", "height", "ext_cy")),
            "paragraph_alignment": "ctr",
        })

    if not title_write_ops:
        raise SystemExit("approved_placeholder_binding_table is empty")
    if not owner_seen:
        raise SystemExit("binding_contract.designated_sink_target does not match any placeholder row")
    if not owner_non_self:
        raise SystemExit("contract placeholder row must stay non-self in the resolved packet")
    if non_self_source_handle is None:
        raise SystemExit("resolved packet requires a non-self source handle")

    return title_write_ops, non_self_source_handle


def build_reference_slide_packet(reference_contract, title_write_ops):
    if not isinstance(reference_contract, dict):
        raise SystemExit("reference_slide_append_contract must be an object")
    slide_layout_handle = reference_contract.get("slide_layout_handle")
    if not isinstance(slide_layout_handle, str) or not slide_layout_handle:
        raise SystemExit("reference_slide_append_contract is missing slide_layout_handle")

    seen = set()
    body_paragraphs = []
    dedupe_source_handles = []

    for op in title_write_ops:
        text_key = op["text_line"].casefold()
        if text_key in seen:
            continue
        seen.add(text_key)
        dedupe_source_handles.append(op["copied_from_fragment_handle"])
        body_paragraphs.append({
            "text_line": op["text_line"],
        })

    if not body_paragraphs:
        raise SystemExit("reference slide body_paragraphs would be empty")

    title_text = reference_contract.get("title_text") or reference_contract.get("reference_title_text") or "Reference"
    return {
        "slide_layout_handle": slide_layout_handle,
        "title_text": one_line(title_text),
        "body_paragraphs": body_paragraphs,
        "dedupe_source_handles": dedupe_source_handles,
    }


def packet_digest(payload):
    blob = json.dumps(payload, sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("observation_artifact")
    parser.add_argument("binding_note_artifact")
    parser.add_argument("output_artifact")
    args = parser.parse_args()

    observation = load_json(args.observation_artifact)
    binding_note = load_json(args.binding_note_artifact)

    observed_contracts = observation.get("observed_title_placeholder_contracts")
    if not isinstance(observed_contracts, list):
        raise SystemExit("observed_title_placeholder_contracts must be a list")
    reference_contract = observation.get("reference_slide_append_contract")

    binding_contract = binding_note.get("binding_contract")
    if not isinstance(binding_contract, dict):
        raise SystemExit("binding_contract must be an object")
    if binding_contract.get("binding_surface_kind") != BINDING_SURFACE_KIND:
        raise SystemExit("binding_contract.binding_surface_kind must be placeholder_cluster")
    authoritative = binding_contract.get("authoritative_binding_artifact")
    if authoritative not in (None, args.binding_note_artifact):
        raise SystemExit("binding_contract.authoritative_binding_artifact does not match the approved binding note")
    table_name = binding_contract.get("designated_binding_table", "approved_placeholder_binding_table")
    if table_name != "approved_placeholder_binding_table":
        raise SystemExit("binding_contract.designated_binding_table must be approved_placeholder_binding_table")
    rows = binding_note.get(table_name)
    if not isinstance(rows, list):
        raise SystemExit("approved_placeholder_binding_table must be a list")

    owner_contracts, render_catalog = build_owner_catalogs(observed_contracts)
    fragment_catalog = build_fragment_catalog(observed_contracts)
    if not render_catalog:
        raise SystemExit("observed_title_placeholder_contracts must provide owner render contract handles")
    if not fragment_catalog:
        raise SystemExit("observed_title_placeholder_contracts must provide fragment handles")

    title_write_ops, non_self_source_handle = build_title_write_ops(
        rows,
        binding_contract,
        owner_contracts,
        render_catalog,
        fragment_catalog,
    )
    reference_slide_packet = build_reference_slide_packet(reference_contract, title_write_ops)

    artifact.update({
        "current_stage": "title_packet_bound",
        "allowed_outputs": [args.output_artifact],
        "source_observation_artifact": args.observation_artifact,
        "source_binding_artifact": args.binding_note_artifact,
        "non_self_source_handle": non_self_source_handle,
        "title_write_ops": title_write_ops,
        "reference_slide_packet": reference_slide_packet,
    })
    artifact["packet_digest"] = packet_digest({
        "source_observation_artifact": artifact["source_observation_artifact"],
        "source_binding_artifact": artifact["source_binding_artifact"],
        "non_self_source_handle": artifact["non_self_source_handle"],
        "title_write_ops": artifact["title_write_ops"],
        "reference_slide_packet": artifact["reference_slide_packet"],
    })

    write_json(args.output_artifact, artifact)


if __name__ == "__main__":
    main()
