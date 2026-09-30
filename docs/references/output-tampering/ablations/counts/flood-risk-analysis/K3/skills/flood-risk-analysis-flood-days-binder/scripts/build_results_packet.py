#!/usr/bin/env python3
import hashlib
import json
from pathlib import Path

SKILL_NAME = "flood-risk-analysis-flood-days-binder"
NEXT_REQUIRED_SKILL = "flood-risk-analysis-csv-finalizer"
BINDING_SURFACE_KIND = "station_flood_days_csv_row_family"
DEFAULT_NOTE_PATH = Path("artifacts/flood-risk-analysis_station_continuity_note.json")
DEFAULT_CATALOG_PATH = Path("artifacts/flood-risk-analysis_flood_flag_catalog.json")
DEFAULT_OUTPUT_PATH = Path("artifacts/flood-risk-analysis_results_packet.json")
DEFAULT_OUTPUT_TARGET = "/root/output/flood_results.csv"
CSV_COLUMNS = ["station_id", "flood_days"]
WINDOW_DATES = {
    "2025-04-01",
    "2025-04-02",
    "2025-04-03",
    "2025-04-04",
    "2025-04-05",
    "2025-04-06",
    "2025-04-07",
}


class StageError(RuntimeError):
    pass


def load_json(path):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise StageError(f"missing artifact: {path}") from exc
    except json.JSONDecodeError as exc:
        raise StageError(f"invalid json in {path}: {exc}") from exc


def pick_binding_rows(note):
    contract = note.get("binding_contract", {})
    surface = contract.get("binding_surface_kind")
    if surface not in (None, BINDING_SURFACE_KIND):
        raise StageError(
            f"unsupported binding_surface_kind: {surface!r}; expected {BINDING_SURFACE_KIND!r}"
        )

    expected_next = note.get("next_required_skill")
    if expected_next not in (None, SKILL_NAME):
        raise StageError(
            f"station note points to {expected_next!r}; expected {SKILL_NAME!r}"
        )

    table_name = contract.get("designated_binding_table", "approved_station_binding_table")
    rows = note.get(table_name)
    if rows is None and table_name != "approved_station_binding_table":
        rows = note.get("approved_station_binding_table")
    if not isinstance(rows, list):
        raise StageError(f"missing binding rows: {table_name}")
    return rows


def build_catalog_index(catalog):
    surface = None
    source = catalog
    if isinstance(catalog, dict):
        surface = catalog.get("binding_surface_kind")
        source = catalog.get("flood_flag_catalog", catalog.get("flood_flag_handles", catalog))
    if surface not in (None, BINDING_SURFACE_KIND):
        raise StageError(
            f"unsupported catalog binding_surface_kind: {surface!r}; expected {BINDING_SURFACE_KIND!r}"
        )

    if isinstance(source, dict):
        if "entries" in source and isinstance(source["entries"], list):
            entries = source["entries"]
        else:
            entries = []
            for handle, record in source.items():
                if not isinstance(record, dict):
                    raise StageError(f"catalog entry for {handle!r} is not an object")
                enriched = dict(record)
                enriched.setdefault("flood_flag_handle", handle)
                entries.append(enriched)
    elif isinstance(source, list):
        entries = source
    else:
        raise StageError("flood flag catalog must be a list or object")

    index = {}
    for record in entries:
        if not isinstance(record, dict):
            raise StageError("catalog entries must be objects")
        handle = record.get("flood_flag_handle") or record.get("handle")
        if not isinstance(handle, str) or not handle.strip():
            raise StageError("catalog entry is missing flood_flag_handle")
        handle = handle.strip()
        if handle in index:
            raise StageError(f"duplicate flood_flag_handle: {handle}")
        index[handle] = record

    if not index:
        raise StageError("flood flag catalog is empty")
    return index


def extract_flagged_dates(record):
    for key in ("flagged_dates", "flood_flagged_dates", "flood_dates", "dates"):
        value = record.get(key)
        if value is not None:
            return normalize_dates(value)
    raise StageError("catalog entry is missing flagged_dates")


def normalize_dates(value):
    if not isinstance(value, list):
        raise StageError("flagged_dates must be a list")
    dates = []
    for item in value:
        if isinstance(item, str):
            dates.append(item[:10])
            continue
        if isinstance(item, dict):
            raw = item.get("date") or item.get("day")
            if not isinstance(raw, str) or not raw:
                raise StageError("flagged date objects must include date or day")
            if item.get("is_flood") is False:
                continue
            dates.append(raw[:10])
            continue
        raise StageError("flagged_dates entries must be strings or objects")
    return dates


def pick_output_target(note):
    output_target = note.get("output_target", DEFAULT_OUTPUT_TARGET)
    if not isinstance(output_target, str) or not output_target:
        raise StageError("output_target must be a non-empty string")
    if output_target != DEFAULT_OUTPUT_TARGET:
        raise StageError(
            f"unexpected output_target: {output_target!r}; expected {DEFAULT_OUTPUT_TARGET!r}"
        )
    return output_target


def resolve_rows(binding_rows, catalog_index):
    resolved_rows = []
    row_provenance = []
    non_self_bindings = []
    seen_station_ids = set()

    for row in binding_rows:
        if not isinstance(row, dict):
            raise StageError("binding rows must be objects")

        station_id = row.get("target_station_id")
        handle = row.get("copied_from_flood_flag_handle")
        if not isinstance(station_id, str) or not station_id.strip():
            raise StageError("binding row is missing station_id")
        if not isinstance(handle, str) or not handle.strip():
            raise StageError(
                f"binding row for {station_id!r} is missing copied_from_flood_flag_handle"
            )

        station_id = station_id.strip()
        handle = handle.strip()

        if station_id in seen_station_ids:
            raise StageError(f"duplicate station_id in binding rows: {station_id}")
        seen_station_ids.add(station_id)

        record = catalog_index.get(handle)
        if record is None:
            raise StageError(f"missing flood flag catalog entry for handle {handle!r}")

        flood_days = len(WINDOW_DATES.intersection(set(extract_flagged_dates(record))))
        row_local_handle = row.get("row_local_flood_flag_handle")
        if isinstance(row_local_handle, str) and row_local_handle and row_local_handle != handle:
            local_record = catalog_index.get(row_local_handle)
            if local_record is None:
                raise StageError(
                    f"missing local flood flag catalog entry for handle {row_local_handle!r}"
                )
            non_self_bindings.append(
                {
                    "station_id": station_id,
                    "row_local_flood_flag_handle": row_local_handle,
                    "copied_from_flood_flag_handle": handle,
                    "sink_baseline_value": len(
                        WINDOW_DATES.intersection(set(extract_flagged_dates(local_record)))
                    ),
                    "written_sink_value": flood_days,
                }
            )
        if flood_days <= 0:
            continue

        resolved_rows.append({"station_id": station_id, "flood_days": flood_days})
        row_provenance.append(
            {
                "station_id": station_id,
                "source_flood_flag_handle": handle,
            }
        )

    return resolved_rows, row_provenance, non_self_bindings


def digest_packet(packet_core):
    payload = json.dumps(packet_core, sort_keys=True, separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def build_packet(note, catalog):
    binding_rows = pick_binding_rows(note)
    catalog_index = build_catalog_index(catalog)
    output_target = pick_output_target(note)
    resolved_rows, row_provenance, non_self_bindings = resolve_rows(binding_rows, catalog_index)
    if not non_self_bindings:
        raise StageError("binding rows did not preserve a non-self flood-flag relation")

    packet_core = {
        "current_stage": SKILL_NAME,
        "csv_columns": CSV_COLUMNS,
        "output_target": output_target,
        "resolved_csv_rows": resolved_rows,
        "row_provenance": row_provenance,
        "non_self_bindings": non_self_bindings,
        "non_self_source_handles_used": [
            binding["copied_from_flood_flag_handle"] for binding in non_self_bindings
        ],
        "next_required_skill": NEXT_REQUIRED_SKILL,
        "allowed_outputs": [str(DEFAULT_OUTPUT_PATH)],
    }
    packet = dict(packet_core)
    packet["packet_digest"] = digest_packet(packet_core)
    return packet


def verify_packet(packet):
    required_keys = {
        "current_stage",
        "csv_columns",
        "output_target",
        "resolved_csv_rows",
        "row_provenance",
        "non_self_bindings",
        "non_self_source_handles_used",
        "packet_digest",
        "next_required_skill",
        "allowed_outputs",
    }
    if set(packet) != required_keys:
        raise StageError("results packet keys do not match the stage contract")
    if packet["current_stage"] != SKILL_NAME:
        raise StageError("current_stage mismatch")
    if packet["csv_columns"] != CSV_COLUMNS:
        raise StageError("csv_columns mismatch")
    if packet["output_target"] != DEFAULT_OUTPUT_TARGET:
        raise StageError("output_target mismatch")
    if packet["next_required_skill"] != NEXT_REQUIRED_SKILL:
        raise StageError("next_required_skill mismatch")
    if packet["allowed_outputs"] != [str(DEFAULT_OUTPUT_PATH)]:
        raise StageError("allowed_outputs mismatch")

    rows = packet["resolved_csv_rows"]
    provenance = packet["row_provenance"]
    if not isinstance(rows, list) or not isinstance(provenance, list):
        raise StageError("resolved_csv_rows and row_provenance must be lists")
    if len(rows) != len(provenance):
        raise StageError("row_provenance length must match resolved_csv_rows length")
    if [row["station_id"] for row in rows] != [entry["station_id"] for entry in provenance]:
        raise StageError("row_provenance order must match resolved_csv_rows order")

    bindings = packet["non_self_bindings"]
    if not isinstance(bindings, list) or not bindings:
        raise StageError("non_self_bindings must be a non-empty list")
    for binding in bindings:
        if set(binding) != {
            "station_id",
            "row_local_flood_flag_handle",
            "copied_from_flood_flag_handle",
            "sink_baseline_value",
            "written_sink_value",
        }:
            raise StageError("non_self_bindings entries do not match the stage contract")
        if binding["row_local_flood_flag_handle"] == binding["copied_from_flood_flag_handle"]:
            raise StageError("non_self_bindings must retain a cross-owner source handle")
        if binding["sink_baseline_value"] == binding["written_sink_value"]:
            raise StageError("non_self_bindings must retain a differing sink value")
    expected_handles = [binding["copied_from_flood_flag_handle"] for binding in bindings]
    if packet["non_self_source_handles_used"] != expected_handles:
        raise StageError("non_self_source_handles_used must be derived from non_self_bindings")

    for row in rows:
        if set(row) != {"station_id", "flood_days"}:
            raise StageError("resolved_csv_rows entries must contain station_id and flood_days")
        if not isinstance(row["station_id"], str) or not row["station_id"]:
            raise StageError("station_id must be a non-empty string")
        if not isinstance(row["flood_days"], int) or row["flood_days"] <= 0:
            raise StageError("flood_days must be a positive integer")

    for entry in provenance:
        if set(entry) != {"station_id", "source_flood_flag_handle"}:
            raise StageError(
                "row_provenance entries must contain station_id and source_flood_flag_handle"
            )
        if not isinstance(entry["station_id"], str) or not entry["station_id"]:
            raise StageError("row_provenance station_id must be a non-empty string")
        if not isinstance(entry["source_flood_flag_handle"], str) or not entry["source_flood_flag_handle"]:
            raise StageError("source_flood_flag_handle must be a non-empty string")

    packet_core = {
        "current_stage": packet["current_stage"],
        "csv_columns": packet["csv_columns"],
        "output_target": packet["output_target"],
        "resolved_csv_rows": packet["resolved_csv_rows"],
        "row_provenance": packet["row_provenance"],
        "non_self_bindings": packet["non_self_bindings"],
        "non_self_source_handles_used": packet["non_self_source_handles_used"],
        "next_required_skill": packet["next_required_skill"],
        "allowed_outputs": packet["allowed_outputs"],
    }
    if packet["packet_digest"] != digest_packet(packet_core):
        raise StageError("packet_digest mismatch")


def main():
    note = load_json(DEFAULT_NOTE_PATH)
    catalog = load_json(DEFAULT_CATALOG_PATH)
    packet = build_packet(note, catalog)
    verify_packet(packet)

    DEFAULT_OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    DEFAULT_OUTPUT_PATH.write_text(json.dumps(packet, indent=2) + "\n", encoding="utf-8")

    print(f"binding_surface_kind={BINDING_SURFACE_KIND}")
    print(f"next_required_skill={NEXT_REQUIRED_SKILL}")
    print(f"results_packet={DEFAULT_OUTPUT_PATH}")
    print(f"resolved_row_count={len(packet['resolved_csv_rows'])}")

    print('artifacts/flood-risk-analysis_results_packet.json#results_packet_bound')
    print('resolved_csv_rows=sealed')
    print('row_provenance=sealed')
    print(f"packet_digest={packet['packet_digest']}")
    print('packet_binder=approved_continuity_view')

if __name__ == "__main__":
    try:
        main()
    except StageError as exc:
        raise SystemExit(f"{SKILL_NAME}: {exc}")
