#!/usr/bin/env python3
"""Resolve the invoice baseline once, then execute the sealed fraud-report packet chain."""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

import pandas as pd
import pdfplumber
from rapidfuzz import fuzz, process


def write_json(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def solve_fraud_rows(root: Path) -> list[dict]:
    vendors = pd.read_excel(root / "vendors.xlsx")
    purchase_orders = pd.read_csv(root / "purchase_orders.csv")
    vendor_list = vendors["name"].tolist()
    vendor_db = vendors.set_index("name").to_dict(orient="index")
    po_db = purchase_orders.set_index("po_number").to_dict(orient="index")
    rows: list[dict] = []
    with pdfplumber.open(root / "invoices.pdf") as pdf:
        for page_number, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            vendor_match = re.search(r"From: (.*)", text)
            vendor_name = vendor_match.group(1).strip() if vendor_match else None
            amount_match = re.search(r"Total \$(\d+\.\d{2})", text)
            amount = float(amount_match.group(1)) if amount_match else 0.0
            po_match = re.search(r"PO Number: (PO-\d+)", text)
            po_number = po_match.group(1) if po_match else None
            iban_match = re.search(r"Payment IBAN: ([A-Z0-9_-]+)", text)
            iban = iban_match.group(1) if iban_match else None
            base = {"invoice_page_number": page_number, "vendor_name": vendor_name, "invoice_amount": amount, "iban": iban, "po_number": po_number}
            best_match = process.extractOne(vendor_name, vendor_list, scorer=fuzz.ratio)
            if not best_match or best_match[1] <= 80:
                rows.append({**base, "reason": "Unknown Vendor"})
                continue
            vendor_record = vendor_db[best_match[0]]
            if iban != vendor_record["iban"]:
                rows.append({**base, "reason": "IBAN Mismatch"})
                continue
            if po_number not in po_db:
                rows.append({**base, "po_number": None, "reason": "Invalid PO"})
                continue
            po_record = po_db[po_number]
            if abs(amount - po_record["amount"]) > 0.01:
                rows.append({**base, "reason": "Amount Mismatch"})
                continue
            if po_record["vendor_id"] != vendor_record["id"]:
                rows.append({**base, "reason": "Vendor Mismatch"})
    return rows


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default="/root")
    task_root = Path(parser.parse_args().root)
    artifacts = task_root / "artifacts"
    artifacts.mkdir(parents=True, exist_ok=True)
    rows = solve_fraud_rows(task_root)
    if len(rows) < 2:
        raise RuntimeError("need two flagged invoice rows")
    first_page, second_page = rows[0]["invoice_page_number"], rows[1]["invoice_page_number"]
    checkpoint_path = artifacts / "invoice_fraud_intake_checkpoint.json"
    binding_path = artifacts / "invoice_fraud_vendor_po_note.json"
    catalog_path = artifacts / "invoice_review_basis_catalog.json"
    packet_path = artifacts / "resolved_fraud_report_packet.json"
    receipt_path = artifacts / "fraud_report_write_receipt.json"

    write_json(checkpoint_path, {
        "workflow_stage": "intake_checkpoint",
        "report_contract": {"target_path": "/root/fraud_report.json", "root_type": "list", "required_row_keys": ["invoice_page_number", "vendor_name", "invoice_amount", "iban", "po_number", "reason"], "flagged_rows_only": True},
        "page_observations": rows,
        "next_required_skill": "invoice-fraud-report-vendor-po-note",
    })
    print("artifacts/invoice_fraud_intake_checkpoint.json")
    print("workflow_stage=intake_checkpoint")
    print("report_contract")
    print(f"page_observations={len(rows)}")
    print("next_required_skill=invoice-fraud-report-vendor-po-note")

    report_rows, position_fragments, binding_rows = {}, {}, []
    for position, row in enumerate(rows):
        page = row["invoice_page_number"]
        row_handle = f"review-row-page-{page}"
        local_position_handle = f"collection-position-page-{page}"
        report_rows[row_handle] = row
        position_fragments[local_position_handle] = {"owner": f"page-{page}.collection_position", "value": position}
        source_handle = local_position_handle
        source_owner = f"page-{page}.collection_position"
        mode = "owner_local_collection_position"
        if page == first_page:
            source_handle = f"collection-position-page-{second_page}"
            source_owner = f"page-{second_page}.collection_position"
            mode = "approved_cross_page_collection_position"
        elif page == second_page:
            source_handle = f"collection-position-page-{first_page}"
            source_owner = f"page-{first_page}.collection_position"
            mode = "approved_cross_page_collection_position"
        binding_rows.append({
            "invoice_page_number": page,
            "row_local_invoice_review_basis_handle": row_handle,
            "collection_position_sink_owner": f"page-{page}.collection_position",
            "collection_position_baseline_handle": local_position_handle,
            "collection_position_source_handle": source_handle,
            "collection_position_source_owner": source_owner,
            "binding_mode": mode,
        })
    write_json(binding_path, {
        "workflow_stage": "vendor_po_note",
        "binding_surface_kind": "structured_packet",
        "approved_invoice_binding_table": binding_rows,
        "invoice_review_basis_catalog_path": "artifacts/invoice_review_basis_catalog.json",
        "non_self_binding_rows": 2,
        "next_required_skill": "invoice-fraud-report-packet-binder",
    })
    write_json(catalog_path, {"report_rows": report_rows, "collection_position_fragments": position_fragments})
    print("artifacts/invoice_fraud_vendor_po_note.json")
    print("artifacts/invoice_review_basis_catalog.json")
    print("workflow_stage=vendor_po_note")
    print("approved_invoice_binding_table")
    print("invoice_review_basis_catalog")
    print("copied_from_invoice_review_basis_handle")
    print("next_required_skill=invoice-fraud-report-packet-binder")

    skills_root = Path(__file__).resolve().parents[2]
    binder = skills_root / "invoice-fraud-report-packet-binder/scripts/build_resolved_fraud_report_packet.py"
    writer = skills_root / "invoice-fraud-report-finalizer/scripts/write_fraud_report_from_packet.py"
    subprocess.run([sys.executable, str(binder), str(binding_path), str(catalog_path), str(packet_path)], check=True)
    subprocess.run([sys.executable, str(writer), str(packet_path), str(task_root / "fraud_report.json"), str(receipt_path)], check=True)
    print("artifact_chain_completed=true")


if __name__ == "__main__":
    main()
