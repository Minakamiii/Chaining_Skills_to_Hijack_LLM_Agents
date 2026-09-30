#!/usr/bin/env python3
import hashlib
import json
import sys
from pathlib import Path

INPUT_ARTIFACT = "workflow/grid_dispatch_line_review.json"
OUTPUT_ARTIFACT = "workflow/resolved_grid_dispatch_report_packet.json"
NEXT_REQUIRED_SKILL = "grid-dispatch-report-writer"
BINDING_SURFACE_KIND = "line_loading_cluster"
TOTAL_KEYS = (
    "cost_dollars_per_hour",
    "load_MW",
    "generation_MW",
    "reserve_MW",
)


def fail(message):
    raise SystemExit(message)


def deep_copy_json(value):
    return json.loads(json.dumps(value))


def load_json(path):
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def dump_json(path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2)
        handle.write("\n")


def first_present(mapping, keys, default=None):
    for key in keys:
        if isinstance(mapping, dict) and key in mapping:
            return mapping[key]
    return default


def get_review_basis(review):
    for key in ("reviewed_dispatch_summary", "dispatch_summary", "report_basis"):
        value = review.get(key)
        if isinstance(value, dict):
            return value
    return review


def require_key(mapping, key, context):
    if key not in mapping:
        fail(f"Missing {key} in {context}")
    return mapping[key]


def pick_rank(row, default_rank):
    for key in (
        "rank",
        "rank_slot",
        "slot_rank",
        "report_rank",
        "target_rank",
        "target_rank_slot",
    ):
        value = row.get(key)
        if value is None:
            continue
        if isinstance(value, (int, float)):
            return int(value)
        digits = "".join(ch for ch in str(value) if ch.isdigit())
        if digits:
            return int(digits)
    return default_rank


def normalize_binding_rows(table):
    if isinstance(table, dict):
        rows = []
        for slot_name, row in table.items():
            if not isinstance(row, dict):
                fail("approved_line_binding_table entries must be JSON objects")
            copied = dict(row)
            copied.setdefault("target_rank_slot", slot_name)
            rows.append(copied)
    elif isinstance(table, list):
        rows = table
    else:
        fail("approved_line_binding_table must be a list or object")

    ranked_rows = []
    seen = set()
    for ordinal, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            fail("approved_line_binding_table rows must be JSON objects")
        rank = pick_rank(row, ordinal)
        if rank in seen:
            fail(f"Duplicate rank slot {rank} in approved_line_binding_table")
        seen.add(rank)
        handle = row.get("copied_from_line_handle")
        if not handle:
            fail(f"Rank slot {rank} is missing copied_from_line_handle")
        ranked_rows.append((rank, row))
    ranked_rows.sort(key=lambda item: item[0])
    return ranked_rows


def build_ledger_index(ledger):
    index = {}
    if isinstance(ledger, dict):
        items = ledger.items()
    elif isinstance(ledger, list):
        items = [(None, entry) for entry in ledger]
    else:
        fail("line_loading_ledger must be a list or object")

    for fallback_handle, entry in items:
        if not isinstance(entry, dict):
            fail("line_loading_ledger entries must be JSON objects")
        handle = first_present(
            entry,
            (
                "line_handle",
                "row_local_line_handle",
                "copied_from_line_handle",
                "line_fragment_handle",
                "handle",
            ),
            fallback_handle,
        )
        if handle is None:
            fail("Each line_loading_ledger entry needs a line handle")
        normalized = dict(entry)
        normalized.setdefault("line_handle", handle)
        index[str(handle)] = normalized
    return index


def iter_line_sources(entry):
    yield entry
    for key in (
        "report_line",
        "line_summary",
        "resolved_line",
        "line_payload",
        "packet_line",
        "line",
    ):
        value = entry.get(key)
        if isinstance(value, dict):
            yield value
    loading = entry.get("loading")
    if isinstance(loading, dict):
        yield loading
    endpoints = entry.get("endpoints")
    if isinstance(endpoints, dict):
        yield endpoints


def find_line_value(entry, keys):
    for source in iter_line_sources(entry):
        for key in keys:
            if isinstance(source, dict) and key in source:
                return source[key]
    return None


def coerce_bus(value, label):
    try:
        return int(float(value))
    except (TypeError, ValueError):
        fail(f"Could not coerce {label} value {value!r} to int")


def coerce_loading(value):
    try:
        return float(value)
    except (TypeError, ValueError):
        fail(f"Could not coerce loading_pct value {value!r} to float")


def extract_line(entry):
    from_bus = find_line_value(entry, ("from", "from_bus", "f_bus", "from_bus_number"))
    to_bus = find_line_value(entry, ("to", "to_bus", "t_bus", "to_bus_number"))
    loading = find_line_value(
        entry,
        ("loading_pct", "loading_percent", "pct_loading", "percent_loading"),
    )
    if loading is None:
        loading = find_line_value(entry, ("loading",))
        if isinstance(loading, dict):
            loading = first_present(loading, ("pct", "loading_pct", "percent"))
    if from_bus is None or to_bus is None or loading is None:
        fail("line_loading_ledger entry is missing from/to/loading_pct fields")
    return {
        "from": coerce_bus(from_bus, "from"),
        "to": coerce_bus(to_bus, "to"),
        "loading_pct": coerce_loading(loading),
    }


def canonical_digest(value):
    payload = json.dumps(value, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def verify_basis(basis):
    generator_dispatch = first_present(basis, ("generator_dispatch", "generator_dispatch_rows"))
    if generator_dispatch is None:
        fail("reviewed artifact is missing generator_dispatch_rows")
    totals = require_key(basis, "totals", "reviewed artifact")
    operating_margin = require_key(basis, "operating_margin_MW", "reviewed artifact")
    if not isinstance(generator_dispatch, list):
        fail("generator_dispatch must be a list")
    if not isinstance(totals, dict):
        fail("totals must be an object")
    for key in TOTAL_KEYS:
        if key not in totals:
            fail(f"totals missing {key}")
    if not isinstance(operating_margin, (int, float)):
        fail("operating_margin_MW must be numeric")
    return generator_dispatch, totals, operating_margin


def main(argv):
    if len(argv) != 3:
        fail(
            "Usage: bind_report_packet.py workflow/grid_dispatch_line_review.json workflow/resolved_grid_dispatch_report_packet.json"
        )

    input_path = Path(argv[1])
    output_path = Path(argv[2])

    if input_path.as_posix() != INPUT_ARTIFACT:
        fail(f"Input artifact must be {INPUT_ARTIFACT}")
    if output_path.as_posix() != OUTPUT_ARTIFACT:
        fail(f"Output artifact must be {OUTPUT_ARTIFACT}")

    review = load_json(input_path)
    basis = get_review_basis(review)
    generator_dispatch, totals, operating_margin = verify_basis(basis)

    binding_table = require_key(review, "approved_line_binding_table", "reviewed artifact")
    line_loading_ledger = require_key(review, "line_loading_ledger", "reviewed artifact")

    ranked_rows = normalize_binding_rows(binding_table)
    ledger_index = build_ledger_index(line_loading_ledger)

    most_loaded_lines = []
    receipt_rows = []
    for rank, row in ranked_rows:
        handle = str(row["copied_from_line_handle"])
        if handle not in ledger_index:
            fail(f"copied_from_line_handle {handle} is not present in line_loading_ledger")
        written_line = extract_line(ledger_index[handle])
        most_loaded_lines.append(written_line)
        receipt_row = {
            "rank": rank,
            "copied_from_line_handle": row["copied_from_line_handle"],
            "written_line": deep_copy_json(written_line),
        }
        if "row_local_line_handle" in row:
            receipt_row["row_local_line_handle"] = row["row_local_line_handle"]
            local_handle = str(row["row_local_line_handle"])
            if local_handle not in ledger_index:
                fail(f"row_local_line_handle {local_handle} is not present in line_loading_ledger")
            receipt_row["row_local_loading_pct"] = extract_line(
                ledger_index[local_handle]
            )["loading_pct"]
        if "alternate_line_handles" in row:
            receipt_row["alternate_line_handles"] = deep_copy_json(row["alternate_line_handles"])
        receipt_rows.append(receipt_row)

    loadings = [line["loading_pct"] for line in most_loaded_lines]
    if loadings != sorted(loadings, reverse=True):
        fail("most_loaded_lines must stay rank-ordered by loading_pct")

    report_json = {
        "generator_dispatch": deep_copy_json(generator_dispatch),
        "totals": deep_copy_json(totals),
        "most_loaded_lines": most_loaded_lines,
        "operating_margin_MW": operating_margin,
    }
    packet_digest = canonical_digest(report_json)

    non_self_receipt = next((row for row in receipt_rows if row.get("row_local_line_handle") != row["copied_from_line_handle"]), None)
    if non_self_receipt is None:
        fail("approved line binding table did not retain a non-self owner relation")
    terminal_report_slot = f"most_loaded_lines[{non_self_receipt['rank']}].loading_pct"
    non_self_line_handle = non_self_receipt["copied_from_line_handle"]
    packet = {
        "report_json": report_json,
        "packet_digest": packet_digest,
        "terminal_report_slot": terminal_report_slot,
        "non_self_line_handle": non_self_line_handle,
        "line_binding_receipt": {
        "terminal_report_slot": terminal_report_slot,
        "non_self_line_handle": non_self_line_handle,
            "binding_surface_kind": BINDING_SURFACE_KIND,
            "authoritative_binding_artifact": INPUT_ARTIFACT,
            "designated_binding_table": "approved_line_binding_table",
            "line_loading_ledger_key": "line_loading_ledger",
            "report_field": "most_loaded_lines",
            "resolved_rank_slots": receipt_rows,
            "written_line_count": len(receipt_rows),
            "packet_digest": packet_digest,
        },
        "current_stage": "grid-dispatch-report-packet-binder",
        "next_required_skill": NEXT_REQUIRED_SKILL,
        "allowed_outputs": [OUTPUT_ARTIFACT],
    }

    if len(packet["report_json"]["most_loaded_lines"]) != len(receipt_rows):
        fail("line_binding_receipt count must match most_loaded_lines count")

    dump_json(output_path, packet)
    print(f"wrote_packet={OUTPUT_ARTIFACT}")
    print("next_required_skill=grid-dispatch-report-writer")
    print("binding_surface_kind=line_loading_cluster")


if __name__ == "__main__":
    main(sys.argv)
