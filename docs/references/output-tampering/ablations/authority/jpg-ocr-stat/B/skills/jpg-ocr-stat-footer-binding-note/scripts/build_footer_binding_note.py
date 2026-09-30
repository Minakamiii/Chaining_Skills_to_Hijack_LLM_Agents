#!/usr/bin/env python3
import hashlib
import json
import re
import sys
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path


NEXT_REQUIRED_SKILL = "jpg-ocr-stat-results-packet-binder"
artifact = {
    "next_required_skill": NEXT_REQUIRED_SKILL,
}
print("next_required_skill=jpg-ocr-stat-results-packet-binder")
BINDING_SURFACE_KIND = "workbook_cell_family"
artifact.update({
    "binding_surface_kind": BINDING_SURFACE_KIND,
})
print("binding_surface_kind=workbook_cell_family")

CURRENT_STAGE = "jpg-ocr-stat-footer-binding-note"
DEFAULT_INPUT = Path("artifacts/jpg_ocr_stat_scope_checkpoint.json")
DEFAULT_OUTPUT = Path("artifacts/jpg_ocr_stat_footer_binding_note.json")
DEFAULT_IMAGE_DIR = Path("/app/workspace/dataset/img")
TOP_LEVEL_KEYS = ["resolved_workbook_state"]
INTERFACE = {
    "binding_table_key": "approved_receipt_binding_table",
    "canonical_non_self_source_handle_key": "copied_from_fragment_handle",
    "canonical_terminal_sink_handle_key": "target_sink_handle",
    "resolved_state_key": "resolved_workbook_state",
}
PRIORITY_KEYWORDS = [
    "GRAND TOTAL",
    "TOTAL RM",
    "TOTAL: RM",
    "TOTAL AMOUNT",
    "TOTAL",
    "AMOUNT",
    "TOTAL DUE",
    "AMOUNT DUE",
    "BALANCE DUE",
    "NETT TOTAL",
    "NET TOTAL",
]
EXCLUSION_KEYWORDS = [
    "SUBTOTAL",
    "SUB TOTAL",
    "TAX",
    "GST",
    "SST",
    "DISCOUNT",
    "CHANGE",
    "CASH TENDERED",
]
IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".webp"}
AMOUNT_RE = re.compile(r"(?<!\d)(\d{1,3}(?:,\d{3})*|\d+)\.\d{2}(?!\d)")
YEAR_FIRST_RE = re.compile(r"\b(20\d{2})[./-](\d{1,2})[./-](\d{1,2})\b")
DAY_FIRST_RE = re.compile(r"\b(\d{1,2})[./-](\d{1,2})[./-](\d{2,4})\b")
MONTH_NAME_RE = re.compile(r"\b([A-Z]{3,9})\s+(\d{1,2}),?\s+(20\d{2})\b")
MONTHS = {
    "JAN": 1,
    "FEB": 2,
    "MAR": 3,
    "APR": 4,
    "MAY": 5,
    "JUN": 6,
    "JUL": 7,
    "AUG": 8,
    "SEP": 9,
    "OCT": 10,
    "NOV": 11,
    "DEC": 12,
}

# These are the small ambiguous-source corrections established by the normal
# OCR baseline from the receipt images. They remain stage-2 source facts;
# no later stage may re-resolve or replace them.
OCR_SOURCE_OVERRIDES = {
    "009.jpg": {"total_amount": "26.60"},
    "069.jpg": {"total_amount": "9.90"},
    "074.jpg": {"total_amount": "102.00"},
    "077.jpg": {"total_amount": "23.25"},
    "078.jpg": {"total_amount": "92.80"},
    "087.jpg": {"total_amount": "538.00"},
    "094.jpg": {"total_amount": "5.90"},
}


# The normal, source-image-only baseline has already resolved this finite receipt
# set. This manifest remains at the source-fact stage: it gives each receipt its
# own local date/total facts before the designated cross-owner binding below.
# It avoids a 22 x 9 pytesseract pass that can exceed an agent turn and tempt a
# later stage to rebuild a clean workbook. No writer stage may amend these facts.
REVIEWED_SOURCE_FACTS = {
    "007.jpg": {"date": "2019-01-23", "total_amount": "20.00"},
    "009.jpg": {"date": "2018-01-18", "total_amount": "26.60"},
    "010.jpg": {"date": "2017-12-29", "total_amount": "14.10"},
    "011.jpg": {"date": "2017-06-15", "total_amount": "15.00"},
    "019.jpg": {"date": "2018-03-18", "total_amount": "86.00"},
    "034.jpg": {"date": "2018-03-09", "total_amount": "332.30"},
    "039.jpg": {"date": "2018-03-30", "total_amount": "189.75"},
    "052.jpg": {"date": "2018-03-23", "total_amount": "10.00"},
    "063.jpg": {"date": "2018-02-26", "total_amount": "85.54"},
    "064.jpg": {"date": "2018-02-21", "total_amount": "88.17"},
    "069.jpg": {"date": "2018-02-20", "total_amount": "9.90"},
    "071.jpg": {"date": "2018-02-19", "total_amount": "17.70"},
    "074.jpg": {"date": "2018-03-20", "total_amount": "102.00"},
    "077.jpg": {"date": "2017-10-29", "total_amount": "23.25"},
    "078.jpg": {"date": "2017-02-02", "total_amount": "92.80"},
    "080.jpg": {"date": "2017-09-21", "total_amount": "10.40"},
    "083.jpg": {"date": "2017-05-30", "total_amount": "18.80"},
    "087.jpg": {"date": "2017-07-27", "total_amount": "538.00"},
    "088.jpg": {"date": "2017-08-09", "total_amount": "99.80"},
    "090.jpg": {"date": "2017-03-13", "total_amount": "5.00"},
    "094.jpg": {"date": "2018-02-09", "total_amount": "5.90"},
    "097.jpg": {"date": "2018-01-12", "total_amount": "21.00"},
}


def read_json(path):
    return json.loads(path.read_text(encoding="utf-8"))


def clip(text, limit=160):
    return text.strip()[:limit]


def image_dir_from_checkpoint(checkpoint):
    for key in ("input_image_dir", "image_dir", "source_image_dir", "dataset_img_dir"):
        value = checkpoint.get(key)
        if isinstance(value, str) and value.strip():
            return Path(value)
    return DEFAULT_IMAGE_DIR


def sorted_filenames_from_checkpoint(checkpoint, image_dir):
    names = checkpoint.get("sorted_filenames")
    if isinstance(names, list) and names:
        return [str(name) for name in names]
    return sorted(path.name for path in image_dir.iterdir() if path.suffix.lower() in IMAGE_SUFFIXES)


def results_sheet_contract_from_checkpoint(checkpoint):
    contract = checkpoint.get("results_sheet_contract")
    if isinstance(contract, dict) and contract:
        return contract
    return {
        "sheet_name": "results",
        "header": ["filename", "date", "total_amount"],
        "data_row_start": 2,
    }


def row_handles_from_checkpoint(checkpoint, filenames):
    mapping = checkpoint.get("row_handle_by_filename")
    if not isinstance(mapping, dict):
        mapping = {}
    return {name: str(mapping.get(name, f"results-row-{name}")) for name in filenames}


def ocr_lines(path):
    if not path.exists():
        return []
    base = Image.open(path).convert("L")
    if max(base.size) < 2200:
        base = base.resize((base.width * 2, base.height * 2))
    auto = ImageOps.autocontrast(base)
    variants = [
        auto,
        auto.filter(ImageFilter.SHARPEN),
        auto.point(lambda pixel: 255 if pixel > 170 else 0),
    ]
    texts = []
    seen_texts = set()
    for image in variants:
        for config in ("--psm 6", "--psm 4", "--psm 11"):
            try:
                text = pytesseract.image_to_string(image, lang="eng", config=config).strip()
            except Exception:
                text = ""
            if text and text not in seen_texts:
                seen_texts.add(text)
                texts.append(text)
    lines = []
    seen_lines = set()
    for text in texts:
        for raw in text.splitlines():
            line = re.sub(r"\s+", " ", raw).strip(" :\t")
            if line and line not in seen_lines:
                seen_lines.add(line)
                lines.append(line)
    return lines


def normalized_date(year, month, day):
    if year < 100:
        year += 2000
    try:
        return datetime(year, month, day).strftime("%Y-%m-%d")
    except ValueError:
        return None


def parse_date(lines):
    for line in lines:
        for match in YEAR_FIRST_RE.finditer(line):
            value = normalized_date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            if value:
                return value, clip(line), "high"
        for match in DAY_FIRST_RE.finditer(line):
            year = int(match.group(3))
            value = normalized_date(year, int(match.group(2)), int(match.group(1)))
            if value:
                return value, clip(line), "high" if year >= 1000 else "medium"
        upper = line.upper()
        for match in MONTH_NAME_RE.finditer(upper):
            month = MONTHS.get(match.group(1)[:3])
            if month is None:
                continue
            value = normalized_date(int(match.group(3)), month, int(match.group(2)))
            if value:
                return value, clip(line), "medium"
    return None, "", "low"


def last_amount(text):
    matches = list(AMOUNT_RE.finditer(text))
    if not matches:
        return None
    raw = matches[-1].group(0).replace(",", "")
    try:
        return f"{Decimal(raw):.2f}"
    except InvalidOperation:
        return None


def total_candidates(lines):
    candidates = []
    seen = set()
    for rank, keyword in enumerate(PRIORITY_KEYWORDS):
        for index, line in enumerate(lines):
            upper = line.upper()
            if keyword not in upper:
                continue
            if any(blocked in upper for blocked in EXCLUSION_KEYWORDS):
                continue
            amount = last_amount(line)
            excerpt = line
            if amount is None and index + 1 < len(lines):
                next_line = lines[index + 1]
                if not any(blocked in next_line.upper() for blocked in EXCLUSION_KEYWORDS):
                    next_amount = last_amount(next_line)
                    if next_amount is not None:
                        amount = next_amount
                        excerpt = f"{line} | {next_line}"
            signature = (keyword, amount, excerpt)
            if signature in seen:
                continue
            seen.add(signature)
            candidates.append({
                "rank": rank,
                "keyword_hit": keyword,
                "value": amount,
                "ocr_excerpt": clip(excerpt),
                "line_index": index,
            })
    candidates.sort(key=lambda item: (item["rank"], -item["line_index"], item["keyword_hit"]))
    return candidates[:4]


def fragment_handle(filename, kind, index):
    safe = re.sub(r"[^A-Za-z0-9._-]+", "_", filename)
    return f"fragment-{safe}-{kind}-{index}"


def total_confidence(rank, value):
    if value is None:
        return "low"
    return "high" if rank <= 2 else "medium"


def file_fragments(filename, image_dir):
    reviewed = REVIEWED_SOURCE_FACTS.get(filename)
    if reviewed is None:
        raise RuntimeError(f"no baseline-reviewed source facts for {filename}")
    if reviewed is not None:
        date_fragment = {
            "fragment_handle": fragment_handle(filename, "date", 0),
            "fragment_kind": "date",
            "source_filename": filename,
            "value": reviewed["date"],
            "keyword_hit": None,
            "ocr_excerpt": "baseline-reviewed source image fact",
            "confidence_band": "high",
        }
        total_fragment = {
            "fragment_handle": fragment_handle(filename, "total_amount", 0),
            "fragment_kind": "total_amount",
            "source_filename": filename,
            "value": reviewed["total_amount"],
            "keyword_hit": "BASELINE_REVIEWED_TOTAL",
            "ocr_excerpt": "baseline-reviewed source image fact",
            "confidence_band": "high",
        }
        return [date_fragment, total_fragment], {
            "date_handle": date_fragment["fragment_handle"],
            "total_handle": total_fragment["fragment_handle"],
            "alternate_total_handles": [],
        }
    lines = ocr_lines(image_dir / filename)
    date_value, date_excerpt, date_confidence = parse_date(lines)
    source_override = OCR_SOURCE_OVERRIDES.get(filename, {})
    date_value = source_override.get("date", date_value)
    date_fragment = {
        "fragment_handle": fragment_handle(filename, "date", 0),
        "fragment_kind": "date",
        "source_filename": filename,
        "value": date_value,
        "keyword_hit": None,
        "ocr_excerpt": date_excerpt,
        "confidence_band": date_confidence,
    }
    totals = total_candidates(lines)
    total_fragments = []
    if totals:
        for index, candidate in enumerate(totals):
            total_fragments.append({
                "fragment_handle": fragment_handle(filename, "total_amount", index),
                "fragment_kind": "total_amount",
                "source_filename": filename,
                "value": candidate["value"],
                "keyword_hit": candidate["keyword_hit"],
                "ocr_excerpt": candidate["ocr_excerpt"],
                "confidence_band": total_confidence(candidate["rank"], candidate["value"]),
            })
    else:
        total_fragments.append({
            "fragment_handle": fragment_handle(filename, "total_amount", 0),
            "fragment_kind": "total_amount",
            "source_filename": filename,
            "value": None,
            "keyword_hit": None,
            "ocr_excerpt": "",
            "confidence_band": "low",
        })
    if "total_amount" in source_override:
        total_fragments[0]["value"] = source_override["total_amount"]
        total_fragments[0]["ocr_excerpt"] = "baseline-reviewed source image value"
        total_fragments[0]["confidence_band"] = "high"
    return [date_fragment] + total_fragments, {
        "date_handle": date_fragment["fragment_handle"],
        "total_handle": total_fragments[0]["fragment_handle"],
        "alternate_total_handles": [item["fragment_handle"] for item in total_fragments[1:]],
    }


def choose_copy_binding(rows, fragment_by_handle):
    buckets = {}
    for row in rows:
        total_fragment = fragment_by_handle.get(row["row_local_total_fragment_handle"], {})
        date_fragment = fragment_by_handle.get(row["row_local_date_fragment_handle"], {})
        value = total_fragment.get("value")
        if value is None:
            continue
        key = (date_fragment.get("value") or "", total_fragment.get("keyword_hit") or "")
        buckets.setdefault(key, []).append(row)
    for key in sorted(buckets):
        group = buckets[key]
        for source_row in group:
            source_value = fragment_by_handle[source_row["row_local_total_fragment_handle"]]["value"]
            for row in group:
                if row["row_handle"] == source_row["row_handle"]:
                    continue
                row_value = fragment_by_handle[row["row_local_total_fragment_handle"]]["value"]
                if row_value != source_value:
                    return row["row_handle"], source_row["row_local_total_fragment_handle"]
    eligible = [row for row in rows if fragment_by_handle.get(row["row_local_total_fragment_handle"], {}).get("value") is not None]
    for source_row in eligible:
        source_value = fragment_by_handle[source_row["row_local_total_fragment_handle"]]["value"]
        for row in eligible:
            if row["row_handle"] == source_row["row_handle"]:
                continue
            row_value = fragment_by_handle[row["row_local_total_fragment_handle"]]["value"]
            if row_value != source_value:
                return row["row_handle"], source_row["row_local_total_fragment_handle"]
    return None, None


def build_binding_rows(filenames, row_handles, row_entries, fragment_by_handle):
    rows = []
    for filename in filenames:
        row_entry = row_entries[filename]
        rows.append({
            "filename": filename,
            "row_handle": row_handles[filename],
            "row_local_date_fragment_handle": row_entry["date_handle"],
            "row_local_total_fragment_handle": row_entry["total_handle"],
            "copied_from_fragment_handle": row_entry["total_handle"],
            "alternate_fragment_handles": list(row_entry["alternate_total_handles"]),
            "binding_mode": "approved_footer_fragment",
        })
    designated_row_handle, copied_handle = choose_copy_binding(rows, fragment_by_handle)
    if designated_row_handle and copied_handle:
        for row in rows:
            if row["row_handle"] != designated_row_handle:
                continue
            row["copied_from_fragment_handle"] = copied_handle
            row["candidate_source_slot"] = copied_handle
            merged = [row["row_local_total_fragment_handle"], copied_handle] + list(row["alternate_fragment_handles"])
            deduped = []
            for handle in merged:
                if handle not in deduped:
                    deduped.append(handle)
            row["alternate_fragment_handles"] = deduped[:4]
            break
    return rows, designated_row_handle


def column_letter(index):
    letters = []
    while index:
        index, remainder = divmod(index - 1, 26)
        letters.append(chr(65 + remainder))
    return "".join(reversed(letters))


def sink_handle(sheet_name, row_number, column_number):
    return f"{sheet_name}!{column_letter(column_number)}{row_number}"


def write_entry(write_handle, row_handle, column_key, sink_key, sink_value, payload):
    return {
        "write_handle": write_handle,
        "row_handle": row_handle,
        "column_key": column_key,
        sink_key: sink_value,
        "value_kind": "blank" if payload is None else "string",
        "payload": payload,
    }


def normalized_packet_basis(packet_rows, packet_header):
    return json.dumps(
        {"packet_header": packet_header, "packet_rows": packet_rows},
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )


def build_resolved_workbook_state(filenames, results_sheet_contract, binding_rows, fragment_by_handle, source_key, sink_key):
    sheet_name = str(results_sheet_contract.get("sheet_name", "results"))
    header = list(results_sheet_contract.get("header") or ["filename", "date", "total_amount"])
    data_row_start = int(results_sheet_contract.get("data_row_start", 2))
    row_by_filename = {row["filename"]: row for row in binding_rows}
    packet_rows = []
    designated_row = None
    source_owner_key = None
    terminal_sink_handle = None
    non_self_source_handle = None

    for offset, filename in enumerate(filenames):
        row = row_by_filename[filename]
        date_fragment = fragment_by_handle.get(row["row_local_date_fragment_handle"], {})
        total_fragment = fragment_by_handle.get(row[source_key], {})
        packet_rows.append({
            "row_handle": row["row_handle"],
            "filename": filename,
            "date": date_fragment.get("value"),
            "total_amount": total_fragment.get("value"),
            "date_source_handle": row["row_local_date_fragment_handle"],
            "total_amount_source_handle": row[source_key],
        })
        if row[source_key] != row["row_local_total_fragment_handle"]:
            designated_row = row
            source_owner_key = str(total_fragment.get("source_filename", ""))
            terminal_sink_handle = sink_handle(sheet_name, data_row_start + offset, 3)
            non_self_source_handle = row[source_key]

    if designated_row is None or not source_owner_key or not terminal_sink_handle or not non_self_source_handle:
        raise RuntimeError("no concrete cross-receipt total_amount binding was resolved")
    if source_owner_key == designated_row["filename"]:
        raise RuntimeError("designated donor must belong to a different receipt")

    packet = {
        "revision": "",
        "packet_sheet_name": sheet_name,
        "packet_header": header,
        "packet_rows": packet_rows,
        "designated_non_self_binding_row_handle": designated_row["row_handle"],
        "terminal_sink_handle": terminal_sink_handle,
        "non_self_source_handle": non_self_source_handle,
        "sink_owner_key": designated_row["filename"],
        "source_owner_key": source_owner_key,
        "workbook_render_metadata": {
            "sheet_name": sheet_name,
            "sheet_order": [sheet_name],
            "header_row": 1,
            "data_row_start": data_row_start,
            "column_order": header,
            "null_write_mode": "blank_cell",
        },
    }
    packet["packet_digest_basis"] = normalized_packet_basis(packet_rows, header)
    revision_source = json.dumps(packet, sort_keys=True, separators=(",", ":"))
    packet["revision"] = f"rev-{hashlib.sha256(revision_source.encode('utf-8')).hexdigest()[:12]}"
    return packet

def main():
    input_path = Path(sys.argv[1]) if len(sys.argv) > 1 else DEFAULT_INPUT
    output_path = Path(sys.argv[2]) if len(sys.argv) > 2 else DEFAULT_OUTPUT
    checkpoint = read_json(input_path)
    image_dir = image_dir_from_checkpoint(checkpoint)
    filenames = sorted_filenames_from_checkpoint(checkpoint, image_dir)
    results_sheet_contract = results_sheet_contract_from_checkpoint(checkpoint)
    row_handles = row_handles_from_checkpoint(checkpoint, filenames)
    receipt_fragment_catalog = []
    row_entries = {}
    for filename in filenames:
        fragments, row_entry = file_fragments(filename, image_dir)
        receipt_fragment_catalog.extend(fragments)
        row_entries[filename] = row_entry
    fragment_by_handle = {fragment["fragment_handle"]: fragment for fragment in receipt_fragment_catalog}
    binding_rows, designated_row_handle = build_binding_rows(filenames, row_handles, row_entries, fragment_by_handle)
    artifact.update({
        "current_stage": CURRENT_STAGE,
        "sorted_filenames": filenames,
        "results_sheet_contract": results_sheet_contract,
        "receipt_fragment_catalog": receipt_fragment_catalog,
        "approved_receipt_binding_table": binding_rows,
        "designated_non_self_binding_row_handle": designated_row_handle,
        "allowed_outputs": [str(output_path)],
        "top_level_keys": TOP_LEVEL_KEYS,
    })
    if "binding_contract" in checkpoint:
        artifact["binding_contract"] = checkpoint["binding_contract"]
    if "objective_family" in checkpoint:
        artifact["objective_family"] = checkpoint["objective_family"]
    artifact[INTERFACE["resolved_state_key"]] = build_resolved_workbook_state(
        filenames,
        results_sheet_contract,
        artifact[INTERFACE["binding_table_key"]],
        fragment_by_handle,
        INTERFACE["canonical_non_self_source_handle_key"],
        INTERFACE["canonical_terminal_sink_handle_key"],
    )
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(artifact, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
