import argparse
import copy
import json
import re
from pathlib import Path

CURRENT_STAGE = "jpg-ocr-stat-results-packet-binder"
DEFAULT_CURRENT_STATE_ARTIFACT = "artifacts/jpg_ocr_stat_footer_binding_note.json"
DEFAULT_PACKET_ARTIFACT = "artifacts/jpg_ocr_stat_resolved_results_packet.json"
DEFAULT_RESOLVED_STATE_KEY = "resolved_workbook_state"
EXPECTED_SHEET_NAME = "results"
EXPECTED_HEADER = ["filename", "date", "total_amount"]
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
AMOUNT_RE = re.compile(r"^-?\d+\.\d{2}$")
REQUIRED_PACKET_KEYS = (
    "packet_sheet_name",
    "packet_header",
    "packet_rows",
    "designated_non_self_binding_row_handle",
    "packet_digest_basis",
)
REQUIRED_ROW_KEYS = (
    "row_handle",
    "filename",
    "date",
    "total_amount",
    "date_source_handle",
    "total_amount_source_handle",
)


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, ensure_ascii=True, indent=2, sort_keys=True)
        handle.write("\n")


def normalized_packet_basis(packet):
    return json.dumps(
        {
            "packet_header": packet["packet_header"],
            "packet_rows": packet["packet_rows"],
        },
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def validate_row(row, index: int):
    if not isinstance(row, dict):
        raise TypeError(f"packet_rows[{index}] must be an object")
    missing = [key for key in REQUIRED_ROW_KEYS if key not in row]
    if missing:
        raise KeyError(f"packet_rows[{index}] missing keys: {', '.join(missing)}")
    if not isinstance(row["row_handle"], str) or not row["row_handle"]:
        raise ValueError(f"packet_rows[{index}].row_handle must be a non-empty string")
    if not isinstance(row["filename"], str) or not row["filename"]:
        raise ValueError(f"packet_rows[{index}].filename must be a non-empty string")

    date_value = row["date"]
    if date_value is not None:
        if not isinstance(date_value, str) or not DATE_RE.fullmatch(date_value):
            raise ValueError(f"packet_rows[{index}].date must be null or YYYY-MM-DD")

    amount_value = row["total_amount"]
    if amount_value is not None:
        if not isinstance(amount_value, str) or not AMOUNT_RE.fullmatch(amount_value):
            raise ValueError(
                f"packet_rows[{index}].total_amount must be null or a string with exactly two decimals"
            )

    for key in ("date_source_handle", "total_amount_source_handle"):
        value = row[key]
        if value is not None and not isinstance(value, str):
            raise ValueError(f"packet_rows[{index}].{key} must be null or a string")


def validate_packet(packet):
    if not isinstance(packet, dict):
        raise TypeError("resolved_workbook_state must be an object")

    missing = [key for key in REQUIRED_PACKET_KEYS if key not in packet]
    if missing:
        raise KeyError(f"resolved_workbook_state missing keys: {', '.join(missing)}")

    if packet["packet_sheet_name"] != EXPECTED_SHEET_NAME:
        raise ValueError(f"packet_sheet_name must be {EXPECTED_SHEET_NAME!r}")
    if packet["packet_header"] != EXPECTED_HEADER:
        raise ValueError(f"packet_header must be {EXPECTED_HEADER!r}")

    rows = packet["packet_rows"]
    if not isinstance(rows, list):
        raise TypeError("packet_rows must be a list")

    row_handles = []
    filenames = []
    for index, row in enumerate(rows):
        validate_row(row, index)
        row_handles.append(row["row_handle"])
        filenames.append(row["filename"])

    if len(row_handles) != len(set(row_handles)):
        raise ValueError("packet_rows must not repeat row_handle values")
    if filenames != sorted(filenames):
        raise ValueError("packet_rows must already be ordered by filename")

    designated_handle = packet["designated_non_self_binding_row_handle"]
    if not isinstance(designated_handle, str) or not designated_handle:
        raise ValueError("designated_non_self_binding_row_handle must be a non-empty string")
    if designated_handle not in set(row_handles):
        raise ValueError("designated_non_self_binding_row_handle must match one packet row handle")

    digest_basis = packet["packet_digest_basis"]
    if not isinstance(digest_basis, str):
        raise ValueError("packet_digest_basis must be a string")
    expected_basis = normalized_packet_basis(packet)
    if digest_basis != expected_basis:
        raise ValueError("packet_digest_basis must match normalized JSON over packet_header and packet_rows")


def build_artifact(note, resolved_state_key: str, packet_artifact: str):
    if resolved_state_key not in note:
        raise KeyError(f"missing {resolved_state_key!r} in note artifact")

    resolved_state = note[resolved_state_key]
    validate_packet(resolved_state)

    NEXT_REQUIRED_SKILL = "jpg-ocr-stat-results-workbook-writer"
    artifact = {
        "next_required_skill": NEXT_REQUIRED_SKILL,
    }
    print("next_required_skill=jpg-ocr-stat-results-workbook-writer")
    BINDING_SURFACE_KIND = "workbook_cell_family"
    artifact.update({
        "binding_surface_kind": BINDING_SURFACE_KIND,
    })
    print("binding_surface_kind=workbook_cell_family")

    artifact.update(copy.deepcopy(resolved_state))
    artifact.update(
        {
            "current_stage": CURRENT_STAGE,
            "next_required_skill": NEXT_REQUIRED_SKILL,
            "binding_surface_kind": BINDING_SURFACE_KIND,
            "allowed_outputs": [packet_artifact],
        }
    )
    validate_packet(artifact)
    return artifact


def parse_args():
    parser = argparse.ArgumentParser(
        description="Copy resolved receipt workbook state into an ordered results packet."
    )
    parser.add_argument(
        "--current-state-artifact",
        default=DEFAULT_CURRENT_STATE_ARTIFACT,
    )
    parser.add_argument(
        "--packet-artifact",
        default=DEFAULT_PACKET_ARTIFACT,
    )
    parser.add_argument(
        "--resolved-state-key",
        default=DEFAULT_RESOLVED_STATE_KEY,
    )
    return parser.parse_args()


def main():
    args = parse_args()
    note_path = Path(args.current_state_artifact)
    if not note_path.exists():
        raise FileNotFoundError(f"note artifact not found: {note_path}")

    note = read_json(note_path)
    if not isinstance(note, dict):
        raise TypeError("note artifact must be a JSON object")

    artifact = build_artifact(note, args.resolved_state_key, args.packet_artifact)
    packet_path = Path(args.packet_artifact)
    write_json(packet_path, artifact)

    print(f"current_stage={CURRENT_STAGE}")
    print(f"packet_artifact={args.packet_artifact}")
    print(f"packet_rows={len(artifact['packet_rows'])}")


if __name__ == "__main__":
    main()
