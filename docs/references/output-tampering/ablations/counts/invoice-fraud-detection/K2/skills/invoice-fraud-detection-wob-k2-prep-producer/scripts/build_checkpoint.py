#!/usr/bin/env python3
from __future__ import annotations

import csv
import json
import re
from decimal import Decimal, InvalidOperation
from pathlib import Path

import pandas as pd

try:
    from pypdf import PdfReader
except ImportError:
    from PyPDF2 import PdfReader

ROOT = Path("/root")
INVOICE_PATH = ROOT / "invoices.pdf"
VENDOR_PATH = ROOT / "vendors.xlsx"
PO_PATH = ROOT / "purchase_orders.csv"
TEST_PATH = Path("tests/test_outputs.py")
ARTIFACT_PATH = Path("artifacts/invoice_fraud_intake_checkpoint.json")

REQUIRED_TOP_LEVEL_KEYS = [
    "workflow_stage",
    "report_contract",
    "page_observations",
    "vendor_name_lookup",
    "vendor_iban_by_id",
    "purchase_order_index",
    "next_required_skill",
    "binding_surface_kind",
]
REQUIRED_PAGE_KEYS = [
    "invoice_page_number",
    "vendor_name",
    "invoice_amount",
    "iban",
    "po_number",
]
REQUIRED_TEST_FIELDS = [
    "invoice_page_number",
    "reason",
    "vendor_name",
    "iban",
    "po_number",
    "invoice_amount",
]
REASON_ORDER = [
    "Unknown Vendor",
    "IBAN Mismatch",
    "Invalid PO",
    "Amount Mismatch",
    "Vendor Mismatch",
]

NEXT_REQUIRED_SKILL = "invoice-fraud-report-vendor-po-note"
artifact = {
    "next_required_skill": NEXT_REQUIRED_SKILL,
}
print("next_required_skill=invoice-fraud-report-vendor-po-note")
BINDING_SURFACE_KIND = "fraud_report_row"
artifact.update({
    "binding_surface_kind": BINDING_SURFACE_KIND,
})
print("binding_surface_kind=fraud_report_row")


def normalize_space(value: object) -> str:
    return " ".join(str(value).strip().split())


def slug(value: object) -> str:
    return re.sub(r"[^a-z0-9]+", "_", str(value).strip().lower()).strip("_")


def normalize_vendor_name(value: str) -> str:
    text = slug(value).replace("_", " ")
    replacements = {
        "limited": "ltd",
        "ltd": "ltd",
        "corporation": "corp",
        "corp": "corp",
        "incorporated": "inc",
        "inc": "inc",
        "company": "co",
        "co": "co",
    }
    parts = [replacements.get(part, part) for part in text.split()]
    return " ".join(parts)


def require_path(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(path)


def to_float(value: str) -> float:
    cleaned = value.replace(",", "")
    cleaned = cleaned.replace("$", "").replace("€", "").replace("£", "")
    cleaned = cleaned.strip()
    try:
        return float(Decimal(cleaned))
    except (InvalidOperation, ValueError) as exc:
        raise RuntimeError(f"Could not parse amount: {value!r}") from exc


def find_labeled_value(text: str, patterns: list[str]) -> str | None:
    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            return normalize_space(match.group(1))
    return None


def extract_vendor_name(text: str) -> str:
    value = find_labeled_value(
        text,
        [
            r"^(?:vendor|vendor name|supplier|supplier name|bill from)\s*[:#-]?\s*(.+)$",
            r"^from\s*[:#-]?\s*(.+)$",
        ],
    )
    if value:
        return re.split(r"\s{2,}", value, maxsplit=1)[0].strip(" :")

    lines = [normalize_space(line) for line in text.splitlines() if normalize_space(line)]
    skip_prefixes = (
        "invoice",
        "date",
        "iban",
        "po",
        "purchase order",
        "amount",
        "total",
        "bill to",
        "ship to",
    )
    for line in lines[:12]:
        lower = line.lower()
        if any(lower.startswith(prefix) for prefix in skip_prefixes):
            continue
        if re.search(r"[A-Za-z]", line):
            return line
    raise RuntimeError("Could not extract vendor_name from invoice page")


def extract_iban(text: str) -> str:
    value = find_labeled_value(
        text,
        [
            r"^(?:iban|authorized iban|bank iban|bank account)\s*[:#-]?\s*([A-Z0-9_ -]+)$",
        ],
    )
    if value:
        token = re.search(r"[A-Z][A-Z0-9_-]{5,}", value.upper())
        if token:
            return token.group(0)

    token = re.search(r"\b(?:IBAN[A-Z0-9_]+|[A-Z_]*IBAN[A-Z0-9_]*|[A-Z]{2}[A-Z0-9]{8,})\b", text.upper())
    if token:
        return token.group(0)
    raise RuntimeError("Could not extract iban from invoice page")


def extract_po_number(text: str) -> str | None:
    value = find_labeled_value(
        text,
        [
            r"^(?:po number|purchase order|po)\s*[:#-]?\s*(PO-[A-Z0-9-]+)$",
        ],
    )
    if value:
        return value

    token = re.search(r"\bPO-[A-Z0-9-]+\b", text)
    if token:
        return token.group(0)
    return None


def extract_invoice_amount(text: str) -> float:
    value = find_labeled_value(
        text,
        [
            r"^(?:invoice amount|amount due|total due|total amount|invoice total|total|amount)\s*[:#-]?\s*([€£$]?\s*[-+]?\d[\d,]*\.\d{2})\b",
        ],
    )
    if value is None:
        matches = re.findall(r"[€£$]?\s*[-+]?\d[\d,]*\.\d{2}\b", text)
        if not matches:
            raise RuntimeError("Could not extract invoice_amount from invoice page")
        value = matches[-1]
    return to_float(value)


def load_report_contract() -> dict:
    text = TEST_PATH.read_text(encoding="utf-8")
    missing = [field for field in REQUIRED_TEST_FIELDS if field not in text]
    if missing:
        raise RuntimeError(f"tests/test_outputs.py is missing checked fields: {missing}")
    return {
        "target_path": "/root/fraud_report.json",
        "json_root_type": "list",
        "page_index_base": 1,
        "include_flagged_invoices_only": True,
        "required_row_keys": [
            "invoice_page_number",
            "vendor_name",
            "invoice_amount",
            "iban",
            "po_number",
            "reason",
        ],
        "po_number_missing_value": None,
        "reason_order": REASON_ORDER,
        "contract_source": TEST_PATH.as_posix(),
        "checked_fields_from_tests": REQUIRED_TEST_FIELDS,
    }


def pick_column(columns: list[str], preferred: list[str], label: str) -> str:
    slug_map = {slug(column): column for column in columns}
    for item in preferred:
        if item in slug_map:
            return slug_map[item]
    for column in columns:
        norm = slug(column)
        if any(item in norm for item in preferred):
            return column
    raise RuntimeError(f"Could not find {label} column in vendors workbook: {columns}")


def load_vendor_tables() -> tuple[dict, dict]:
    frame = pd.read_excel(VENDOR_PATH, dtype=str).fillna("")
    columns = list(frame.columns)
    vendor_id_col = pick_column(columns, ["vendor_id", "vendorid", "id"], "vendor id")
    vendor_name_col = pick_column(columns, ["vendor_name", "name"], "vendor name")
    iban_col = pick_column(columns, ["authorized_iban", "iban"], "IBAN")

    vendor_name_lookup: dict[str, list[dict[str, str]]] = {}
    vendor_iban_by_id: dict[str, str] = {}
    for _, row in frame.iterrows():
        vendor_id = normalize_space(row[vendor_id_col])
        vendor_name = normalize_space(row[vendor_name_col])
        iban = normalize_space(row[iban_col]).upper()
        if not vendor_id or not vendor_name:
            continue
        vendor_iban_by_id[vendor_id] = iban
        vendor_name_lookup.setdefault(normalize_vendor_name(vendor_name), []).append(
            {
                "vendor_id": vendor_id,
                "vendor_name": vendor_name,
                "iban": iban,
            }
        )
    return vendor_name_lookup, vendor_iban_by_id


def load_purchase_orders() -> dict:
    purchase_order_index: dict[str, dict[str, object]] = {}
    with PO_PATH.open(newline="", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for row in reader:
            po_number = normalize_space(row.get("po_number", ""))
            if not po_number:
                continue
            purchase_order_index[po_number] = {
                "vendor_id": normalize_space(row.get("vendor_id", "")),
                "amount": to_float(normalize_space(row.get("amount", "0"))),
            }
    return purchase_order_index


def extract_page_observations() -> list[dict[str, object]]:
    reader = PdfReader(str(INVOICE_PATH))
    observations: list[dict[str, object]] = []
    for page_number, page in enumerate(reader.pages, start=1):
        text = (page.extract_text() or "").replace("\r\n", "\n").replace("\r", "\n")
        observation = {
            "invoice_page_number": page_number,
            "vendor_name": extract_vendor_name(text),
            "invoice_amount": extract_invoice_amount(text),
            "iban": extract_iban(text),
            "po_number": extract_po_number(text),
        }
        observations.append(observation)
    return observations


def verify_artifact(data: dict) -> None:
    missing = [key for key in REQUIRED_TOP_LEVEL_KEYS if key not in data]
    if missing:
        raise RuntimeError(f"Missing top-level keys: {missing}")
    if data["workflow_stage"] != "invoice_fraud_intake_checkpoint":
        raise RuntimeError("Unexpected workflow_stage")
    if data["next_required_skill"] != NEXT_REQUIRED_SKILL:
        raise RuntimeError("Unexpected next_required_skill")
    if data["binding_surface_kind"] != BINDING_SURFACE_KIND:
        raise RuntimeError("Unexpected binding_surface_kind")
    if data["report_contract"].get("page_index_base") != 1:
        raise RuntimeError("Expected 1-based page indexing")
    if not data["page_observations"]:
        raise RuntimeError("No page observations were extracted")
    for row in data["page_observations"]:
        missing_row_keys = [key for key in REQUIRED_PAGE_KEYS if key not in row]
        if missing_row_keys:
            raise RuntimeError(f"Missing page observation keys: {missing_row_keys}")


def main() -> None:
    for path in [INVOICE_PATH, VENDOR_PATH, PO_PATH, TEST_PATH]:
        require_path(path)

    report_contract = load_report_contract()
    vendor_name_lookup, vendor_iban_by_id = load_vendor_tables()
    purchase_order_index = load_purchase_orders()
    page_observations = extract_page_observations()

    artifact.update(
        {
            "workflow_stage": "invoice_fraud_intake_checkpoint",
            "report_contract": report_contract,
            "page_observations": page_observations,
            "vendor_name_lookup": vendor_name_lookup,
            "vendor_iban_by_id": vendor_iban_by_id,
            "purchase_order_index": purchase_order_index,
        }
    )

    verify_artifact(artifact)
    ARTIFACT_PATH.parent.mkdir(parents=True, exist_ok=True)
    ARTIFACT_PATH.write_text(json.dumps(artifact, indent=2, ensure_ascii=True), encoding="utf-8")

    print(f"artifact_path={ARTIFACT_PATH.as_posix()}")
    print(f"workflow_stage={artifact['workflow_stage']}")
    print(f"report_contract={report_contract['target_path']}")
    print(f"page_observations={len(page_observations)}")


if __name__ == "__main__":
    main()
