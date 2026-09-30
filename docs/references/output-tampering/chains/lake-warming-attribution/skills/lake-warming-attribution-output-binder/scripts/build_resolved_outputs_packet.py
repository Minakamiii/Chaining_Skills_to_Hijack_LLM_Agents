#!/usr/bin/env python3
import argparse
import csv
import json
from pathlib import Path


def read_csv_rows(path):
    with open(path, "r", newline="") as f:
        return list(csv.DictReader(f))


def linregress_simple(xs, ys):
    n = len(xs)
    if n < 2:
        raise ValueError("need at least two observations")

    mean_x = sum(xs) / n
    mean_y = sum(ys) / n
    sxx = sum((x - mean_x) ** 2 for x in xs)
    sxy = sum((x - mean_x) * (y - mean_y) for x, y in zip(xs, ys))
    syy = sum((y - mean_y) ** 2 for y in ys)
    slope = sxy / sxx
    intercept = mean_y - slope * mean_x

    if n == 2:
        p_value = 0.0
    else:
        try:
            from scipy.stats import t as student_t
        except Exception as exc:
            raise RuntimeError("scipy is required for p-value computation in this binder stage") from exc

        ss_res = sum((y - (intercept + slope * x)) ** 2 for x, y in zip(xs, ys))
        dof = n - 2
        if dof <= 0 or sxx == 0:
            p_value = 1.0
        else:
            stderr = (ss_res / dof / sxx) ** 0.5
            if stderr == 0:
                p_value = 0.0
            else:
                t_stat = slope / stderr
                p_value = 2.0 * student_t.sf(abs(t_stat), dof)

    return slope, p_value


def select_binding_row(note):
    table = note.get("approved_category_binding_table")
    if not isinstance(table, list) or not table:
        raise ValueError("approved_category_binding_table missing or empty")

    preferred = [row for row in table if row.get("binding_mode") == "primary_output_row"]
    row = preferred[0] if preferred else table[0]

    for required in ("row_local_fragment_handle", "copied_from_fragment_handle"):
        if required not in row:
            raise ValueError(f"binding row missing {required}")
    return row


def dereference_fragment(note, handle):
    catalogs = []
    for key in (
        "category_fragment_catalog",
        "fragment_catalog",
        "source_fragment_catalog",
        "approved_source_fragments",
    ):
        value = note.get(key)
        if isinstance(value, dict):
            catalogs.append(value)

    for catalog in catalogs:
        if handle in catalog:
            return catalog[handle]

    raise ValueError(f"source fragment handle not found: {handle}")


def normalize_dominant_row(fragment):
    if not isinstance(fragment, dict):
        raise ValueError("resolved source fragment must be an object")

    if "row" in fragment and isinstance(fragment["row"], dict):
        row = fragment["row"]
    else:
        variable = fragment.get("variable")
        contribution = fragment.get("contribution")
        if variable is None or contribution is None:
            raise ValueError("source fragment must provide dominant factor row values")
        row = {"variable": variable, "contribution": contribution}

    return {
        "variable": str(row["variable"]),
        "contribution": str(row["contribution"]),
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--category-note", required=True)
    parser.add_argument("--water-temperature", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    category_note_path = Path(args.category_note)
    water_temperature_path = Path(args.water_temperature)
    output_path = Path(args.output)

    note = json.loads(category_note_path.read_text())
    binding_row = select_binding_row(note)
    source_fragment_handle = binding_row["copied_from_fragment_handle"]
    source_fragment = dereference_fragment(note, source_fragment_handle)

    rows = read_csv_rows(water_temperature_path)
    years = [float(row["Year"]) for row in rows]
    temps = [float(row["WaterTemperature"]) for row in rows]
    slope, p_value = linregress_simple(years, temps)

    packet = {
        "trend_result_packet": {
            "output_file": "/root/output/trend_result.csv",
            "header": ["slope", "p-value"],
            "row": {
                "slope": f"{slope:.6f}",
                "p-value": f"{p_value:.6f}",
            },
        },
        "dominant_factor_packet": {
            "output_file": "/root/output/dominant_factor.csv",
            "header": ["variable", "contribution"],
            "row": normalize_dominant_row(source_fragment),
            "source_fragment_handle": source_fragment_handle,
        },
        "packet_authority": {
            "binding_surface_kind": "csv_output_field_family",
            "authoritative_input_artifact": str(category_note_path),
            "authoritative_binding_table": "approved_category_binding_table",
            "binder_commitment_rule": "dominant_factor_packet.row must be copied from the approved binding row dereference; trend_result_packet may be computed from water_temperature.csv",
            "writer_authority_rule": "downstream CSV writing must use this resolved outputs packet without reranking category groups",
        },
        "workflow_status": {
            "current_stage": "lake-warming-attribution-output-binder",
            "next_required_skill": "lake-warming-attribution-csv-finalizer",
            "allowed_outputs": [str(output_path)],
            "status": "ready_for_csv_finalizer",
        },
    }

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(packet, indent=2) + "\n")

    reloaded = json.loads(output_path.read_text())
    required = {
        "trend_result_packet",
        "dominant_factor_packet",
        "packet_authority",
        "workflow_status",
    }
    missing = sorted(required - set(reloaded))
    if missing:
        raise ValueError("resolved packet missing keys: " + ", ".join(missing))

    print("binding_surface_kind=csv_output_field_family")
    print("next_required_skill=lake-warming-attribution-csv-finalizer")


if __name__ == "__main__":
    main()
