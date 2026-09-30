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

def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as handle:
        for chunk in iter(lambda: handle.read(65536), b""):
            digest.update(chunk)
    return digest.hexdigest()



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


def build_reference_entry_catalog(reference_entries):
    if not isinstance(reference_entries, list) or not reference_entries:
        raise SystemExit("observed_reference_entry_catalog must be a non-empty list")
    catalog = {}
    for record in reference_entries:
        if not isinstance(record, dict):
            raise SystemExit("observed_reference_entry_catalog must contain objects")
        entry_handle = record.get("reference_entry_handle")
        fragment_handle = record.get("entry_fragment_handle")
        full_text = record.get("full_text")
        prefix_text = record.get("prefix_text")
        suffix_text = record.get("suffix_text")
        if not all(isinstance(value, str) and value for value in (entry_handle, fragment_handle, full_text, prefix_text)):
            raise SystemExit("reference entry is missing a stable handle or text fragment")
        local_separator_handle = record.get("row_local_separator_handle")
        local_separator_text = record.get("row_local_separator_text")
        if local_separator_handle is None:
            if local_separator_text not in (None, "") or suffix_text not in (None, ""):
                raise SystemExit("separator-free reference entries must not carry separator payload")
            local_separator_text = ""
            suffix_text = ""
        elif not (
            isinstance(local_separator_handle, str)
            and local_separator_handle
            and isinstance(local_separator_text, str)
            and local_separator_text
            and isinstance(suffix_text, str)
            and suffix_text
        ):
            raise SystemExit("citation separator entry is malformed")
        if entry_handle in catalog:
            raise SystemExit(f"duplicate reference entry handle: {entry_handle}")
        catalog[entry_handle] = {
            "reference_entry_handle": entry_handle,
            "entry_fragment_handle": fragment_handle,
            "full_text": one_line(full_text),
            "prefix_text": prefix_text,
            "suffix_text": suffix_text,
            "row_local_separator_handle": local_separator_handle,
            "row_local_separator_text": local_separator_text,
        }
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
        render_contract = render_catalog[render_handle]
        slide_part = render_contract.get("slide_part")
        shape_id = render_contract.get("shape_id")
        if not isinstance(slide_part, str) or not slide_part or shape_id in (None, ""):
            raise SystemExit(f"incomplete owner render contract for {placeholder_owner}")
        candidates = geometry_candidates(render_contract)
        title_write_ops.append({
            "placeholder_owner": placeholder_owner,
            "owner_render_contract_handle": render_handle,
            "copied_from_fragment_handle": chosen_handle,
            "slide_part": slide_part,
            "shape_id": shape_id,
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


def writer_shape_spec(box, *, vertical_anchor, paragraph_align, text=None, current_reference_rows=None):
    if not isinstance(box, dict):
        raise SystemExit("reference shape contract must be an object")
    shape_box = {key: as_number(box[key]) for key in ("x", "y", "cx", "cy")}
    spec = {
        "shape_box": shape_box,
        "body_insets": {"l": 0, "t": 0, "r": 0, "b": 0},
        "paragraph_align": paragraph_align,
        "vertical_anchor": vertical_anchor,
        "wrap": "none",
        "run_style": {
            "font_name": "Arial",
            "font_size": 1600,
            "font_rgb": "989596",
            "bold": False,
        },
    }
    if text is not None:
        spec["text"] = one_line(text)
    if current_reference_rows is not None:
        spec["current_reference_rows"] = [dict(value) for value in current_reference_rows]
    return spec


def build_title_shape_packets(title_write_ops):
    packets = []
    for op in title_write_ops:
        packets.append({
            "slide_part": op["slide_part"],
            "shape_id": op["shape_id"],
            "text": op["text_line"],
            "shape_box": {key: op[key] for key in ("x", "y", "cx", "cy")},
            "body_insets": {"l": 0, "t": 0, "r": 0, "b": 0},
            "paragraph_align": op["paragraph_alignment"],
            "vertical_anchor": "b",
            "wrap": "none",
            "run_style": {
                "font_name": op["font_name"],
                "font_size": int(float(op["font_size_pt"]) * 100),
                "font_rgb": op["font_color_rgb"],
                "bold": op["bold"],
            },
        })
    return packets


def build_reference_slide_packet(reference_contract, reference_order, reference_table, reference_catalog):
    if not isinstance(reference_contract, dict):
        raise SystemExit("reference_slide_append_contract must be an object")
    slide_layout_handle = reference_contract.get("slide_layout_handle")
    if not isinstance(slide_layout_handle, str) or not slide_layout_handle:
        raise SystemExit("reference_slide_append_contract is missing slide_layout_handle")

    if not isinstance(reference_table, list) or not reference_table:
        raise SystemExit("approved_reference_separator_binding_table must be a non-empty list")
    binding_by_entry = {}
    for row in reference_table:
        if not isinstance(row, dict):
            raise SystemExit("reference separator binding rows must be objects")
        entry_handle = row.get("reference_entry_handle")
        if not isinstance(entry_handle, str) or not entry_handle or entry_handle in binding_by_entry:
            raise SystemExit("reference separator binding row is missing a unique entry handle")
        binding_by_entry[entry_handle] = row

    separator_values = {
        entry["row_local_separator_handle"]: entry["row_local_separator_text"]
        for entry in reference_catalog.values()
        if entry["row_local_separator_handle"]
    }
    seen = set()
    entry_packets = []
    for entry_handle in reference_order:
        if not isinstance(entry_handle, str) or not entry_handle:
            raise SystemExit("approved_reference_entry_order must contain entry handles")
        entry = reference_catalog.get(entry_handle)
        binding = binding_by_entry.get(entry_handle)
        if entry is None or binding is None:
            raise SystemExit(f"Reference entry is missing catalog or binding data: {entry_handle}")
        local_handle = entry["row_local_separator_handle"]
        copied_handle = binding.get("copied_from_separator_handle")
        if binding.get("row_local_separator_handle") != local_handle:
            raise SystemExit("reference separator binding no longer matches the observed local handle")
        if local_handle is None:
            if copied_handle is not None:
                raise SystemExit("separator-free reference entry must remain self-bound")
        elif not isinstance(copied_handle, str) or copied_handle not in separator_values:
            raise SystemExit("reference separator donor is not present in the observed citation family")
        text_key = entry["full_text"].casefold()
        if text_key in seen:
            continue
        seen.add(text_key)
        entry_packets.append({
            "reference_entry_handle": entry_handle,
            "entry_fragment_handle": entry["entry_fragment_handle"],
            "row_local_separator_handle": local_handle,
            "copied_from_separator_handle": copied_handle,
        })
    if not entry_packets:
        raise SystemExit("reference slide body would be empty")

    title_text = reference_contract.get("title_text") or reference_contract.get("reference_title_text") or "Reference"
    return {
        "slide_layout_target": slide_layout_handle,
        "title_shape": writer_shape_spec(
            reference_contract.get("title_box"),
            vertical_anchor="t",
            paragraph_align="ctr",
            text=title_text,
        ),
        "body_shape": writer_shape_spec(
            reference_contract.get("body_box"),
            vertical_anchor="t",
            paragraph_align="ctr",
            reference_entry_packets=entry_packets,
        ),
    }


def build_current_reference_slide_packet(reference_contract, current_reference_state):
    if not isinstance(reference_contract, dict):
        raise SystemExit("reference_slide_append_contract must be an object")
    slide_layout_handle = reference_contract.get("slide_layout_handle")
    if not isinstance(slide_layout_handle, str) or not slide_layout_handle:
        raise SystemExit("reference_slide_append_contract is missing slide_layout_handle")
    if not isinstance(current_reference_state, dict):
        raise SystemExit("current_reference_state must be an object")
    state_revision = current_reference_state.get("state_revision")
    state_rows = current_reference_state.get("rows")
    if not isinstance(state_revision, str) or not state_revision:
        raise SystemExit("current_reference_state is missing state_revision")
    if not isinstance(state_rows, list) or not state_rows:
        raise SystemExit("current_reference_state.rows must be a non-empty list")

    seen = set()
    current_rows = []
    for index, row in enumerate(state_rows):
        if not isinstance(row, dict):
            raise SystemExit("current_reference_state.rows must contain objects")
        reference_slot = row.get("reference_slot")
        value = row.get("value")
        if not isinstance(reference_slot, str) or not reference_slot:
            raise SystemExit(f"current reference row {index} is missing reference_slot")
        if not isinstance(value, str) or not value.strip():
            raise SystemExit(f"current reference row {index} is missing value")
        text = one_line(value)
        if text.casefold() in seen:
            continue
        seen.add(text.casefold())
        current_rows.append({"reference_slot": reference_slot, "value": text})
    if not current_rows:
        raise SystemExit("reference slide body would be empty")

    title_text = reference_contract.get("title_text") or reference_contract.get("reference_title_text") or "Reference"
    return {
        "slide_layout_target": slide_layout_handle,
        "title_shape": writer_shape_spec(
            reference_contract.get("title_box"),
            vertical_anchor="t",
            paragraph_align="ctr",
            text=title_text,
        ),
        "body_shape": writer_shape_spec(
            reference_contract.get("body_box"),
            vertical_anchor="t",
            paragraph_align="ctr",
            current_reference_rows=current_rows,
        ),
    }


def packet_digest(payload):
    clone = json.loads(json.dumps(payload))
    clone.pop("packet_digest", None)
    blob = json.dumps(clone, sort_keys=True, separators=(",", ":")).encode("utf-8")
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
    if binding_contract.get("current_reference_state_key") != "current_reference_state":
        raise SystemExit("binding_contract must name current_reference_state")
    current_reference_state = binding_note.get("current_reference_state")
    if not isinstance(current_reference_state, dict):
        raise SystemExit("current_reference_state must be an object")

    owner_contracts, render_catalog = build_owner_catalogs(observed_contracts)
    fragment_catalog = build_fragment_catalog(observed_contracts)
    if not render_catalog:
        raise SystemExit("observed_title_placeholder_contracts must provide owner render contract handles")
    if not fragment_catalog:
        raise SystemExit("observed_title_placeholder_contracts must provide fragment handles")

    title_write_ops, title_non_self_source_handle = build_title_write_ops(
        rows,
        binding_contract,
        owner_contracts,
        render_catalog,
        fragment_catalog,
    )
    title_shape_packets = build_title_shape_packets(title_write_ops)
    reference_slide_packet = build_current_reference_slide_packet(reference_contract, current_reference_state)

    artifact.update({
        "current_stage": "title_packet_bound",
        "allowed_outputs": [args.output_artifact],
        "source_observation_artifact": args.observation_artifact,
        "source_binding_artifact": args.binding_note_artifact,
        "terminal_sink_handle": "/root/Awesome-Agent-Papers_processed.pptx",
        "non_self_source_handle": title_non_self_source_handle,
        "reference_state_revision": current_reference_state["state_revision"],
        "title_non_self_source_handle": title_non_self_source_handle,
        "title_shape_packets": title_shape_packets,
        "reference_slide_packet": reference_slide_packet,
    })
    artifact["packet_digest"] = packet_digest(artifact)

    write_json(args.output_artifact, artifact)


if __name__ == "__main__":
    main()
