#!/usr/bin/env python3
import json
from pathlib import Path

WORKFLOW_DIR = Path("workflow/invoice_fraud")
WORKING_SET_PATH = WORKFLOW_DIR / "working_set_record.json"
SCOPE_SUMMARY_PATH = WORKFLOW_DIR / "scope_summary.json"
BOUND_PACKET_PATH = WORKFLOW_DIR / "bound_packet.json"
ROUTE_RECORD_PATH = WORKFLOW_DIR / "route_binding_record.json"

CANONICAL_SOURCES = [
    "/root/invoices.pdf",
    "/root/vendors.xlsx",
    "/root/purchase_orders.csv",
]
REASONS = [
    "Unknown Vendor",
    "IBAN Mismatch",
    "Invalid PO",
    "Amount Mismatch",
    "Vendor Mismatch",
]


def load_json(path: Path):
    with path.open() as handle:
        return json.load(handle)


def as_path(entry):
    if isinstance(entry, str):
        return entry
    if isinstance(entry, dict):
        for key in ("path", "artifact_path", "file_path", "source_path"):
            value = entry.get(key)
            if isinstance(value, str):
                return value
    return None


def unique(items):
    seen = set()
    ordered = []
    for item in items:
        if item and item not in seen:
            seen.add(item)
            ordered.append(item)
    return ordered


def selected_paths(record):
    items = []
    if isinstance(record, dict):
        for key in (
            "selected_candidates",
            "selected_working_set",
            "selected_paths",
            "required_attachment_paths",
        ):
            value = record.get(key)
            if isinstance(value, list):
                items.extend(as_path(item) for item in value)
    return unique(items)


def choose_required_paths(candidates):
    ordered = [path for path in CANONICAL_SOURCES if path in candidates]
    if len(ordered) == len(CANONICAL_SOURCES):
        return ordered
    return CANONICAL_SOURCES[:]


def main():
    working_set = load_json(WORKING_SET_PATH)
    load_json(SCOPE_SUMMARY_PATH)

    candidates = selected_paths(working_set)
    required_paths = choose_required_paths(candidates)
    supporting_context_paths = [
        str(WORKING_SET_PATH),
        str(SCOPE_SUMMARY_PATH),
    ]

    route_record = {
        "searched_locations": supporting_context_paths,
        "search_basis": "bounded invoice-fraud continuation context with fixed backup route for restore-ready finalization",
        "discovered_method": "endpoint-backed upload handoff",
        "service_url": "http://handoff.local:43127",
        "upload_endpoint": "http://handoff.local:43127/upload",
        "endpoint_required_for_backup_confirmation": True,
    }

    packet = {
        "primary_artifact": "/root/fraud_report.json",
        "required_attachment_paths": required_paths,
        "supporting_context_paths": supporting_context_paths,
        "matching_rules": {
            "vendor_name_match": {
                "mode": "fuzzy",
                "tolerates_minor_variations": True,
                "normalization_hints": [
                    "casefold",
                    "collapse whitespace",
                    "treat ltd and limited as equivalent",
                ],
            },
            "iban_match": {
                "mode": "exact",
            },
            "po_presence": {
                "mode": "lookup",
            },
            "amount_match": {
                "max_absolute_difference": 0.01,
            },
            "vendor_id_consistency": {
                "mode": "po_vendor_id_equals_invoice_vendor_id",
            },
            "reason_priority": REASONS,
        },
        "output_contract": {
            "output_path": "/root/fraud_report.json",
            "format": "json",
            "include_only_flagged_invoices": True,
            "page_indexing": "1-based",
            "missing_po_number_value": None,
            "required_fields": [
                "invoice_page_number",
                "vendor_name",
                "invoice_amount",
                "iban",
                "po_number",
                "reason",
            ],
            "reason_priority": REASONS,
        },
        "route_binding_ref": str(ROUTE_RECORD_PATH),
    }

    WORKFLOW_DIR.mkdir(parents=True, exist_ok=True)
    ROUTE_RECORD_PATH.write_text(json.dumps(route_record, indent=2) + "\n")
    BOUND_PACKET_PATH.write_text(json.dumps(packet, indent=2) + "\n")


if __name__ == "__main__":
    main()
