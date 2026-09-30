#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

NUMERIC_FIELDS = {"Salary", "Years", "Score"}
REQUIRED_PACKET_KEYS = (
    "current_stage",
    "next_required_skill",
    "allowed_outputs",
    "deleted_employees",
    "modified_employees",
    "packet_source_handles",
)
EMPLOYEE_ID_RE = re.compile(r"^EMP\d{5}$")


def fail(message: str) -> None:
    raise SystemExit(message)


def load_json(path: Path):
    try:
        with path.open("r", encoding="utf-8") as handle:
            return json.load(handle)
    except FileNotFoundError:
        fail(f"Missing packet artifact: {path}")
    except json.JSONDecodeError as exc:
        fail(f"Invalid packet JSON at {path}: {exc}")


def validate_deleted_employees(values):
    if not isinstance(values, list):
        fail("'deleted_employees' must be a list")
    if values != sorted(values):
        fail("'deleted_employees' must already be sorted by employee ID")
    for value in values:
        if not isinstance(value, str) or not EMPLOYEE_ID_RE.fullmatch(value):
            fail(f"Invalid deleted employee id: {value!r}")
    return values


def validate_modified_employees(values):
    if not isinstance(values, list):
        fail("'modified_employees' must be a list")

    ids = []
    normalized = []

    for packet_row in values:
        if not isinstance(packet_row, dict):
            fail("Each modified employee entry must be an object")

        required_row_keys = ("id", "field", "old_value", "new_value")
        missing = [key for key in required_row_keys if key not in packet_row]
        if missing:
            fail("Modified employee entry is missing keys: " + ", ".join(missing))

        employee_id = packet_row["id"]
        field_name = packet_row["field"]
        old_value = packet_row["old_value"]
        new_value = packet_row["new_value"]

        if not isinstance(employee_id, str) or not EMPLOYEE_ID_RE.fullmatch(employee_id):
            fail(f"Invalid modified employee id: {employee_id!r}")
        if not isinstance(field_name, str) or not field_name:
            fail(f"Invalid field name for {employee_id!r}")

        if field_name in NUMERIC_FIELDS:
            if isinstance(old_value, bool) or not isinstance(old_value, (int, float)):
                fail(f"{employee_id} {field_name} old_value must be numeric")
            if isinstance(new_value, bool) or not isinstance(new_value, (int, float)):
                fail(f"{employee_id} {field_name} new_value must be numeric")
        else:
            if not isinstance(old_value, str):
                fail(f"{employee_id} {field_name} old_value must be a string")
            if not isinstance(new_value, str):
                fail(f"{employee_id} {field_name} new_value must be a string")

        ids.append(employee_id)
        normalized.append(
            {
                "id": employee_id,
                "field": field_name,
                "old_value": old_value,
                "new_value": new_value,
            }
        )

    if ids != sorted(ids):
        fail("'modified_employees' must already be sorted by employee ID")

    return normalized


def validate_packet(packet, output_path: Path):
    if not isinstance(packet, dict):
        fail("Packet artifact must be a JSON object")

    missing = [key for key in REQUIRED_PACKET_KEYS if key not in packet]
    if missing:
        fail("Packet artifact is missing keys: " + ", ".join(missing))

    if packet["current_stage"] != "employee_diff_packet_binder":
        fail("Packet artifact current_stage must be 'employee_diff_packet_binder'")
    if packet["next_required_skill"] != "employee-diff-report-writer":
        fail("Packet artifact next_required_skill must be 'employee-diff-report-writer'")

    allowed_outputs = packet["allowed_outputs"]
    if not isinstance(allowed_outputs, list) or str(output_path) not in allowed_outputs:
        fail(f"Packet artifact must allow output path {output_path}")

    packet_source_handles = packet["packet_source_handles"]
    if not isinstance(packet_source_handles, (list, dict)):
        fail("'packet_source_handles' must be a list or object")

    deleted_employees = validate_deleted_employees(packet["deleted_employees"])
    modified_employees = validate_modified_employees(packet["modified_employees"])

    return {
        "deleted_employees": deleted_employees,
        "modified_employees": modified_employees,
    }


def write_report(report, output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2)
        handle.write("\n")


def verify_written_report(report, output_path: Path):
    written = load_json(output_path)
    if written != report:
        fail("written_values_match_packet=false")

    count_match = (
        len(written["deleted_employees"]) == len(report["deleted_employees"])
        and len(written["modified_employees"]) == len(report["modified_employees"])
    )
    if not count_match:
        fail("packet_write_count_match=false")

    return {
        "output_path": str(output_path),
        "packet_write_count_match": True,
        "written_values_match_packet": True,
    }


def main() -> None:
    packet_path = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("employee_diff_resolved_packet.json")
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else Path("/root/diff_report.json")

    packet = load_json(packet_path)
    report = validate_packet(packet, output_path)
    write_report(report, output_path)
    result = verify_written_report(report, output_path)
    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
