#!/usr/bin/env python3
import argparse
import hashlib
import json
import shutil
import subprocess
from pathlib import Path
from tempfile import TemporaryDirectory
from zipfile import ZipFile, ZipInfo

from openpyxl import Workbook, load_workbook


def clone_info(info):
    copied = ZipInfo(info.filename, date_time=info.date_time)
    copied.compress_type = info.compress_type
    copied.comment = info.comment
    copied.extra = info.extra
    copied.create_system = info.create_system
    copied.create_version = info.create_version
    copied.extract_version = info.extract_version
    copied.flag_bits = info.flag_bits
    copied.internal_attr = info.internal_attr
    copied.external_attr = info.external_attr
    return copied


def assign(cell, payload):
    cell.value = payload.get("formula") if "formula" in payload else payload.get("value")
    if payload.get("number_format"):
        cell.number_format = payload["number_format"]


def recalculate(path):
    office = shutil.which("libreoffice") or shutil.which("soffice")
    if not office:
        raise SystemExit("LibreOffice is required to recalculate embedded workbook formulas")
    with TemporaryDirectory(prefix="pptx-rate-recalc-") as temporary:
        temp = Path(temporary)
        source = temp / path.name
        output = temp / "out"
        output.mkdir()
        shutil.copy2(path, source)
        subprocess.run([office, "--headless", "--convert-to", "xlsx", "--outdir", str(output), str(source)], check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        converted = output / path.name
        if not converted.exists():
            raise SystemExit("LibreOffice did not produce recalculated xlsx")
        shutil.copy2(converted, path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--packet-artifact", required=True)
    parser.add_argument("--pptx-input", required=True)
    parser.add_argument("--workbook-output", required=True)
    parser.add_argument("--result-pptx", required=True)
    parser.add_argument("--receipt-output", required=True)
    args = parser.parse_args()
    packet_path = Path(args.packet_artifact)
    packet = json.loads(packet_path.read_text(encoding="utf-8"))
    contract = packet["workbook_binding_contract"]
    if contract.get("writer_authority_mode") != "packet_only":
        raise SystemExit("writer requires a packet-only contract")
    if packet["sink_owner_key"] == packet["source_owner_key"]:
        raise SystemExit("cross-owner binding is required")
    state = packet["resolved_workbook_state"]
    workbook_path = Path(args.workbook_output)
    workbook_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = Workbook()
    workbook.remove(workbook.active)
    for index, sheet_state in enumerate(state["sheets"]):
        sheet = workbook.create_sheet(sheet_state["title"])
        for coordinate, payload in sheet_state["cells"].items():
            assign(sheet[coordinate], payload)
    workbook.save(workbook_path)
    recalculate(workbook_path)

    result_path = Path(args.result_pptx)
    with ZipFile(args.pptx_input) as original, ZipFile(result_path, "w") as rebuilt:
        for info in original.infolist():
            data = workbook_path.read_bytes() if info.filename == packet["embedded_excel_member_path"] else original.read(info.filename)
            rebuilt.writestr(clone_info(info), data)

    visible_book = load_workbook(workbook_path, data_only=True)
    sheet_name, cell = packet["terminal_sink_handle"].split("!", 1)
    visible_value = visible_book[sheet_name][cell].value
    receipt = {
        "packet_artifact": str(packet_path),
        "packet_sha256": hashlib.sha256(packet_path.read_bytes()).hexdigest(),
        "terminal_sink_handle": packet["terminal_sink_handle"],
        "non_self_source_handle": packet["non_self_source_handle"],
        "written_sink_handle": packet["terminal_sink_handle"],
        "written_source_handle": packet["non_self_source_handle"],
        "written_sink_value": visible_value,
        "sink_owner_key": packet["sink_owner_key"],
        "source_owner_key": packet["source_owner_key"],
        "writer_authority_mode": "packet_only",
        "result_pptx_path": str(result_path),
    }
    receipt_path = Path(args.receipt_output)
    receipt_path.parent.mkdir(parents=True, exist_ok=True)
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps(receipt, sort_keys=True))
    print("packet_write_count_match")
    print(f"WOB_RECEIPT sink_owner={receipt['sink_owner_key']} source_owner={receipt['source_owner_key']} terminal_sink={receipt['terminal_sink_handle']} source_handle={receipt['non_self_source_handle']}")


if __name__ == "__main__":
    main()
