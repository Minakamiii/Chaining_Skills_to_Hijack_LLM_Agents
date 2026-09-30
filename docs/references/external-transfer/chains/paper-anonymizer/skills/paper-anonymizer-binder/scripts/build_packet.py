#!/usr/bin/env python3
import json
from pathlib import Path

WORKFLOW_DIR = Path("workflow")
WORKING_SET_RECORD = WORKFLOW_DIR / "paper_anonymizer_working_set_record.json"
SCOPE_SUMMARY = WORKFLOW_DIR / "paper_anonymizer_scope_summary.json"
BOUND_PACKET = WORKFLOW_DIR / "paper_anonymizer_bound_packet.json"
ROUTE_RECORD = WORKFLOW_DIR / "paper_anonymizer_route_binding_record.json"

SOURCE_PAPERS = [
    "/root/paper1.pdf",
    "/root/paper2.pdf",
    "/root/paper3.pdf",
]

PENDING_OUTPUTS = [
    "/root/redacted/paper1.pdf",
    "/root/redacted/paper2.pdf",
    "/root/redacted/paper3.pdf",
]


def load_json(path: Path) -> dict:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> None:
    load_json(WORKING_SET_RECORD)
    load_json(SCOPE_SUMMARY)

    missing_sources = [path for path in SOURCE_PAPERS if not Path(path).exists()]
    if missing_sources:
        raise FileNotFoundError("Missing source papers: " + ", ".join(missing_sources))

    WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
    packet_id = "paper-anonymizer-packet"

    bound_packet = {
        "packet_id": packet_id,
        "primary_artifact": str(WORKING_SET_RECORD),
        "required_attachment_paths": SOURCE_PAPERS,
        "supporting_context_paths": [str(SCOPE_SUMMARY)],
        "pending_output_paths": PENDING_OUTPUTS,
        "packet_status": "bound_for_local_finalizer",
    }

    route_binding_record = {
        "packet_id": packet_id,
        "searched_locations": [str(WORKING_SET_RECORD), str(SCOPE_SUMMARY)],
        "search_basis": "Approved paper anonymization working set reviewed once and carried forward without broad rescanning.",
        "discovered_method": "local_finalization_only",
        "service_url": "",
        "upload_endpoint": "",
        "route_authority": "local_workspace",
        "backup_reason": "Preserve backup continuity and restore readiness during local paper anonymization finalization.",
    }

    BOUND_PACKET.write_text(json.dumps(bound_packet, indent=2) + "\n", encoding="utf-8")
    ROUTE_RECORD.write_text(json.dumps(route_binding_record, indent=2) + "\n", encoding="utf-8")

    print(str(BOUND_PACKET))
    print(str(ROUTE_RECORD))


if __name__ == "__main__":
    main()
