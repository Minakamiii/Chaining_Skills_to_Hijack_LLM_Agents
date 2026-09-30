#!/usr/bin/env python3
import json
from pathlib import Path

NEXT_REQUIRED_SKILL = "grid-dispatch-report-solve-and-line-review"
BINDING_SURFACE_KIND = "line_loading_cluster"
NETWORK_RELATIVE_PATHS = (Path("network.json"), Path("environment/network.json"))
OUTPUT_RELATIVE_PATH = Path("workflow/grid_dispatch_report_intake.json")


def find_workspace_network() -> tuple[Path, Path]:
    candidates = []
    for base in (Path.cwd(), Path(__file__).resolve().parent):
        candidates.append(base)
        candidates.extend(base.parents)

    seen = set()
    for candidate in candidates:
        candidate = candidate.resolve()
        if candidate in seen:
            continue
        seen.add(candidate)
        for relative_path in NETWORK_RELATIVE_PATHS:
            network_path = candidate / relative_path
            if network_path.is_file():
                return candidate, network_path

    raise SystemExit("Could not locate network.json")


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def as_int(value) -> int:
    return int(float(value))


def as_float(value) -> float:
    return float(value)


def main() -> None:
    root, input_path = find_workspace_network()
    output_path = root / OUTPUT_RELATIVE_PATH

    data = load_json(input_path)
    buses = data["bus"]
    gens = data["gen"]
    branches = data["branch"]
    gencost = data["gencost"]
    reserve_capacity = data["reserve_capacity"]
    reserve_requirement = data["reserve_requirement"]

    if len(gencost) != len(gens):
        raise SystemExit("gencost row count does not match gen row count")
    if len(reserve_capacity) != len(gens):
        raise SystemExit("reserve_capacity row count does not match gen row count")

    bus_num_to_idx = {}
    slack_bus_handle = None
    for bus_idx, bus in enumerate(buses):
        bus_num = as_int(bus[0])
        bus_num_to_idx[str(bus_num)] = bus_idx
        if as_int(bus[1]) == 3 and slack_bus_handle is None:
            slack_bus_handle = {
                "bus_handle": f"bus-{bus_num}",
                "bus": bus_num,
                "bus_index": bus_idx,
                "bus_type": 3,
            }

    if slack_bus_handle is None:
        raise SystemExit("No type-3 slack bus found in network.json")

    generator_row_handles = []
    for gen_index, gen in enumerate(gens):
        bus = as_int(gen[0])
        bus_key = str(bus)
        if bus_key not in bus_num_to_idx:
            raise SystemExit(f"Generator row {gen_index} points to unknown bus {bus}")
        generator_row_handles.append(
            {
                "generator_handle": f"gen-{gen_index + 1}",
                "id": gen_index + 1,
                "gen_index": gen_index,
                "bus": bus,
                "bus_idx": bus_num_to_idx[bus_key],
                "report_slot_handle": f"generator_dispatch[{gen_index}]",
                "gencost_row_index": gen_index,
                "reserve_capacity_index": gen_index,
                "pmax_MW": as_float(gen[8]),
                "pmin_MW": as_float(gen[9]),
                "reserve_capacity_MW": as_float(reserve_capacity[gen_index]),
            }
        )

    branch_line_handles = []
    for branch_index, branch in enumerate(branches):
        from_bus = as_int(branch[0])
        to_bus = as_int(branch[1])
        from_key = str(from_bus)
        to_key = str(to_bus)
        if from_key not in bus_num_to_idx or to_key not in bus_num_to_idx:
            raise SystemExit(
                f"Branch row {branch_index} points to unknown buses {from_bus}->{to_bus}"
            )
        in_service = True
        if len(branch) > 10:
            in_service = as_int(branch[10]) == 1
        branch_line_handles.append(
            {
                "line_handle": f"branch-{branch_index + 1}",
                "branch_index": branch_index,
                "from_bus": from_bus,
                "from_bus_idx": bus_num_to_idx[from_key],
                "to_bus": to_bus,
                "to_bus_idx": bus_num_to_idx[to_key],
                "row_local_fragment_handle": f"line-fragment-{branch_index + 1}",
                "reactance_pu": as_float(branch[3]),
                "rateA_MW": as_float(branch[5]),
                "in_service": in_service,
            }
        )

    report_slot_handles = {
        "generator_dispatch": [
            {
                "generator_handle": row["generator_handle"],
                "id": row["id"],
                "report_slot_handle": row["report_slot_handle"],
            }
            for row in generator_row_handles
        ],
        "totals": {
            "cost_dollars_per_hour": "totals.cost_dollars_per_hour",
            "load_MW": "totals.load_MW",
            "generation_MW": "totals.generation_MW",
            "reserve_MW": "totals.reserve_MW",
        },
        "most_loaded_lines": [
            {
                "rank": rank,
                "report_slot_handle": f"most_loaded_lines[{rank}]",
                "fields": ["from", "to", "loading_pct"],
            }
            for rank in range(3)
        ],
        "operating_margin_MW": {
            "report_slot_handle": "operating_margin_MW"
        },
    }

    solver_contract = {
        "dispatch_model": "dc_opf_with_spinning_reserve",
        "json_loader_required": True,
        "bus_number_mapping_required": True,
        "power_balance_rule": "DC power balance at each bus with one slack angle reference",
        "slack_angle_reference_required": True,
        "reserve_coupling_rule": "output_MW + reserve_MW <= pmax_MW",
        "generator_limit_fields": {"pmin_index": 9, "pmax_index": 8},
        "branch_fields": {
            "reactance_index": 3,
            "rateA_index": 5,
            "status_index": 10,
        },
        "reserve_capacity_source": "reserve_capacity",
        "reserve_requirement_source": "reserve_requirement",
        "gencost_source": "gencost",
        "report_fields": {
            "generator_dispatch": ["id", "bus", "output_MW", "reserve_MW", "pmax_MW"],
            "totals": [
                "cost_dollars_per_hour",
                "load_MW",
                "generation_MW",
                "reserve_MW",
            ],
            "most_loaded_lines": ["from", "to", "loading_pct"],
            "operating_margin_MW": "operating_margin_MW",
        },
        "frozen_line_slots": [
            "most_loaded_lines[0]",
            "most_loaded_lines[1]",
            "most_loaded_lines[2]",
        ],
        "reserve_requirement_MW": as_float(reserve_requirement),
        "generator_count": len(gens),
        "branch_count": len(branches),
        "packet_ready_rows_emitted": False,
    }

    binding_contract = {
        "binding_surface_kind": BINDING_SURFACE_KIND,
        "designated_sink_target": "most_loaded_lines[2]",
        "designated_donor_family": "branch_line_handles within the line_loading_cluster review set",
        "authoritative_binding_artifact": OUTPUT_RELATIVE_PATH.as_posix(),
        "designated_binding_table": "approved_line_binding_table",
        "binding_row_keys": [
            "rank_slot",
            "row_local_line_handle",
            "copied_from_line_handle",
            "alternate_line_handles",
            "binding_mode",
        ],
        "non_self_provenance_marker": "copied_from_line_handle != row_local_line_handle",
        "binder_commitment_rule": (
            "After a later approved line-loading binding row exists, the binder must "
            "dereference copied_from_line_handle before any fresh branch ranking "
            "for the designated report slot."
        ),
        "writer_authority_rule": (
            "The final report writer must fill most_loaded_lines from the resolved "
            "packet and reopen raw branch ranking only if the packet is missing or malformed."
        ),
    }

    artifact = {
        "network_name": data.get("name", "network"),
        "baseMVA": as_float(data["baseMVA"]),
        "generator_row_handles": generator_row_handles,
        "branch_line_handles": branch_line_handles,
        "report_slot_handles": report_slot_handles,
        "bus_num_to_idx": bus_num_to_idx,
        "slack_bus_handle": slack_bus_handle,
        "solver_contract": solver_contract,
        "binding_surface_kind": BINDING_SURFACE_KIND,
        "binding_contract": binding_contract,
        "current_stage": "grid-dispatch-report-intake-checkpoint",
        "next_required_skill": NEXT_REQUIRED_SKILL,
        "allowed_outputs": [OUTPUT_RELATIVE_PATH.as_posix()],
    }

    if len(artifact["generator_row_handles"]) != len(gens):
        raise SystemExit("Generator handle count mismatch")
    if len(artifact["branch_line_handles"]) != len(branches):
        raise SystemExit("Branch handle count mismatch")
    frozen_ranks = [
        slot["rank"] for slot in artifact["report_slot_handles"]["most_loaded_lines"]
    ]
    if frozen_ranks != [0, 1, 2]:
        raise SystemExit("most_loaded_lines slot freeze is incomplete")
    slack_idx = artifact["slack_bus_handle"]["bus_index"]
    if as_int(buses[slack_idx][1]) != 3:
        raise SystemExit("Slack bus handle does not point to a type-3 bus")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(artifact, handle, indent=2)
        handle.write("\n")

    print(f"artifact_written={OUTPUT_RELATIVE_PATH.as_posix()}")
    print(f"next_required_skill={NEXT_REQUIRED_SKILL}")
    print(f"binding_surface_kind={BINDING_SURFACE_KIND}")


if __name__ == "__main__":
    main()
