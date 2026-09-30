#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from pathlib import Path

import pandas as pd
import pdfplumber

PDF_PATH = Path('/root/employees_backup.pdf')
XLSX_PATH = Path('/root/employees_current.xlsx')
OUT_PATH = Path('employee_diff_checkpoint.json')
NUMERIC_FIELDS = {'salary', 'years', 'score'}
ID_RE = re.compile(r'EMP\d{5}$')


def clean_text(value):
    if value is None:
        return ''
    if isinstance(value, float) and math.isnan(value):
        return ''
    text = str(value).replace('\u00a0', ' ')
    return re.sub(r'\s+', ' ', text).strip()


def header_key(value):
    return re.sub(r'[^a-z0-9]+', '', clean_text(value).lower())


def is_numeric_field(field):
    return header_key(field) in NUMERIC_FIELDS


def coerce_value(field, value):
    if value is None:
        return ''
    if isinstance(value, float) and math.isnan(value):
        return ''
    if is_numeric_field(field):
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            number = float(value)
        else:
            text = clean_text(value).replace(',', '').replace('$', '')
            if text == '':
                return ''
            number = float(text)
        return int(number) if number.is_integer() else number
    return clean_text(value)


def find_id_column(headers):
    keyed = {header: header_key(header) for header in headers}
    for header, key in keyed.items():
        if key in {'id', 'employeeid', 'empid'}:
            return header
    for header, key in keyed.items():
        if key.endswith('id'):
            return header
    raise RuntimeError('Could not locate an employee ID column')


def choose_employee_sheet(workbook):
    best_frame = None
    best_score = -1
    for frame in workbook.values():
        df = frame.dropna(how='all').copy()
        if df.empty:
            continue
        df.columns = [clean_text(col) for col in df.columns]
        df = df.loc[:, [bool(col) for col in df.columns]]
        if df.empty:
            continue
        try:
            id_col = find_id_column(list(df.columns))
        except RuntimeError:
            continue
        score = sum(1 for value in df[id_col].tolist() if ID_RE.fullmatch(clean_text(value)))
        if score > best_score:
            best_frame = df
            best_score = score
    if best_frame is None or best_score <= 0:
        raise RuntimeError('Could not find an employee table in /root/employees_current.xlsx')
    return best_frame


def load_excel_rows():
    workbook = pd.read_excel(XLSX_PATH, sheet_name=None, dtype=object)
    df = choose_employee_sheet(workbook)
    headers = [clean_text(header) for header in df.columns]
    id_col = find_id_column(headers)
    rows = []
    for _, series in df.iterrows():
        record = {header: coerce_value(header, series[header]) for header in headers}
        employee_id = clean_text(record.get(id_col, ''))
        if ID_RE.fullmatch(employee_id):
            record[id_col] = employee_id
            rows.append(record)
    if not rows:
        raise RuntimeError('No employee rows found in /root/employees_current.xlsx')
    return headers, id_col, rows


def maybe_header_row(cells, expected_map, id_header):
    hits = 0
    has_id = False
    headers = []
    for index, cell in enumerate(cells):
        mapped = expected_map.get(header_key(cell))
        if mapped:
            hits += 1
            has_id = has_id or mapped == id_header
            headers.append(mapped)
        else:
            headers.append(clean_text(cell) or f'column_{index + 1}')
    if has_id and hits >= 2:
        return headers
    return None


def normalize_row_length(cells, width):
    row = list(cells)
    if len(row) < width:
        row.extend([''] * (width - len(row)))
    elif len(row) > width:
        row = row[: width - 1] + [' '.join(row[width - 1:])]
    return row


def build_record(cells, headers, id_header):
    row = normalize_row_length([clean_text(cell) for cell in cells], len(headers))
    record = {}
    for header, cell in zip(headers, row):
        if not header.startswith('column_'):
            record[header] = cell
    employee_id = clean_text(record.get(id_header, ''))
    if not ID_RE.fullmatch(employee_id):
        for cell in row:
            if ID_RE.fullmatch(cell):
                record[id_header] = cell
                employee_id = cell
                break
    if not ID_RE.fullmatch(employee_id):
        return None
    return record


def load_pdf_rows_from_tables(expected_headers):
    expected_map = {header_key(header): header for header in expected_headers}
    id_header = find_id_column(expected_headers)
    rows = []
    active_headers = None
    with pdfplumber.open(PDF_PATH) as pdf:
        for page in pdf.pages:
            for table in page.extract_tables() or []:
                if not table:
                    continue
                table_headers = active_headers
                for raw_row in table:
                    cells = [clean_text(cell) for cell in raw_row]
                    if not any(cells):
                        continue
                    mapped = maybe_header_row(cells, expected_map, id_header)
                    if mapped:
                        active_headers = mapped
                        table_headers = mapped
                        continue
                    if table_headers is None:
                        continue
                    record = build_record(cells, table_headers, id_header)
                    if record:
                        rows.append(record)
    return rows


def load_pdf_rows_from_text(expected_headers):
    expected_map = {header_key(header): header for header in expected_headers}
    id_header = find_id_column(expected_headers)
    rows = []
    active_headers = expected_headers
    with pdfplumber.open(PDF_PATH) as pdf:
        for page in pdf.pages:
            text = page.extract_text() or ''
            for line in text.splitlines():
                cells = [clean_text(part) for part in re.split(r'\s{2,}', line.strip()) if clean_text(part)]
                if not cells:
                    continue
                mapped = maybe_header_row(cells, expected_map, id_header)
                if mapped:
                    active_headers = mapped
                    continue
                if not any(ID_RE.fullmatch(cell) for cell in cells):
                    continue
                record = build_record(cells, active_headers, id_header)
                if record:
                    rows.append(record)
    return rows


def normalize_pdf_rows(raw_rows, expected_headers):
    id_col = find_id_column(expected_headers)
    rows = []
    for raw in raw_rows:
        record = {header: coerce_value(header, raw.get(header, '')) for header in expected_headers}
        employee_id = clean_text(record.get(id_col, ''))
        if ID_RE.fullmatch(employee_id):
            record[id_col] = employee_id
            rows.append(record)
    if not rows:
        raise RuntimeError('Could not extract employee rows from /root/employees_backup.pdf')
    return rows


def load_pdf_rows(expected_headers):
    raw_rows = load_pdf_rows_from_tables(expected_headers)
    if not raw_rows:
        raw_rows = load_pdf_rows_from_text(expected_headers)
    return normalize_pdf_rows(raw_rows, expected_headers)


def values_equal(left, right):
    left_is_number = isinstance(left, (int, float)) and not isinstance(left, bool)
    right_is_number = isinstance(right, (int, float)) and not isinstance(right, bool)
    if left_is_number and right_is_number:
        return abs(float(left) - float(right)) < 1e-9
    return str(left) == str(right)


def validate_checkpoint(checkpoint):
    required = {
        'current_stage',
        'next_required_skill',
        'allowed_outputs',
        'deleted_employee_ids',
        'modified_employee_candidates',
        'modified_field_families',
        'modified_employee_fragment_catalog',
        'candidate_index_clusters',
    }
    missing = required.difference(checkpoint)
    if missing:
        raise RuntimeError(f'Missing checkpoint keys: {sorted(missing)}')
    if checkpoint['current_stage'] != 'employee_diff_intake_checkpoint':
        raise RuntimeError('Unexpected current_stage')
    if checkpoint['next_required_skill'] != 'employee-diff-report-fragment-binding-note':
        raise RuntimeError('Unexpected next_required_skill')
    if checkpoint['allowed_outputs'] != ['employee_diff_checkpoint.json']:
        raise RuntimeError('allowed_outputs must contain only employee_diff_checkpoint.json')
    if checkpoint['deleted_employee_ids'] != sorted(checkpoint['deleted_employee_ids']):
        raise RuntimeError('deleted_employee_ids must be sorted')
    ordered_candidates = sorted(
        checkpoint['modified_employee_candidates'],
        key=lambda item: (item['employee_id'], item['field']),
    )
    if checkpoint['modified_employee_candidates'] != ordered_candidates:
        raise RuntimeError('modified_employee_candidates must be sorted by employee ID and field')
    catalog = checkpoint['modified_employee_fragment_catalog']
    for candidate in checkpoint['modified_employee_candidates']:
        handle = candidate['fragment_handle']
        if handle not in catalog:
            raise RuntimeError(f'Missing fragment catalog entry for {handle}')
        entry = catalog[handle]
        if entry['employee_id'] != candidate['employee_id'] or entry['field'] != candidate['field']:
            raise RuntimeError(f'Fragment catalog mismatch for {handle}')
        if is_numeric_field(candidate['field']):
            for key in ('old_value', 'new_value'):
                value = entry[key]
                if value != '' and not isinstance(value, (int, float)):
                    raise RuntimeError(f'{handle} {key} must stay numeric')
    clusters = checkpoint['candidate_index_clusters']
    for family in checkpoint['modified_field_families']:
        field = family['field']
        if family['candidate_count'] != len(clusters.get(field, [])):
            raise RuntimeError(f'candidate_count mismatch for {field}')


def build_checkpoint():
    headers, id_col, current_rows = load_excel_rows()
    previous_rows = load_pdf_rows(headers)
    previous_by_id = {row[id_col]: row for row in previous_rows}
    current_by_id = {row[id_col]: row for row in current_rows}
    deleted_employee_ids = sorted(employee_id for employee_id in previous_by_id if employee_id not in current_by_id)
    comparison_fields = [header for header in headers if header != id_col]
    diff_rows = []
    for employee_id in sorted(set(previous_by_id).intersection(current_by_id)):
        old_row = previous_by_id[employee_id]
        new_row = current_by_id[employee_id]
        for field in comparison_fields:
            old_value = old_row.get(field, '')
            new_value = new_row.get(field, '')
            if not values_equal(old_value, new_value):
                diff_rows.append((employee_id, field, old_value, new_value))
    diff_rows.sort(key=lambda item: (item[0], item[1]))

    modified_employee_candidates = []
    modified_employee_fragment_catalog = {}
    clusters = {}
    field_kinds = {}
    for candidate_index, (employee_id, field, old_value, new_value) in enumerate(diff_rows):
        fragment_handle = f'candidate:{candidate_index:04d}'
        modified_employee_candidates.append(
            {
                'candidate_index': candidate_index,
                'employee_id': employee_id,
                'field': field,
                'fragment_handle': fragment_handle,
            }
        )
        value_kind = 'number' if is_numeric_field(field) else 'text'
        modified_employee_fragment_catalog[fragment_handle] = {
            'employee_id': employee_id,
            'field': field,
            'old_value': old_value,
            'new_value': new_value,
            'value_kind': value_kind,
        }
        clusters.setdefault(field, []).append(candidate_index)
        field_kinds[field] = value_kind

    checkpoint = {
        'current_stage': 'employee_diff_intake_checkpoint',
        'next_required_skill': 'employee-diff-report-fragment-binding-note',
        'allowed_outputs': ['employee_diff_checkpoint.json'],
        'deleted_employee_ids': deleted_employee_ids,
        'modified_employee_candidates': modified_employee_candidates,
        'modified_field_families': [
            {
                'field': field,
                'candidate_count': len(clusters[field]),
                'value_kind': field_kinds[field],
            }
            for field in sorted(clusters)
        ],
        'modified_employee_fragment_catalog': modified_employee_fragment_catalog,
        'candidate_index_clusters': {field: clusters[field] for field in sorted(clusters)},
    }
    validate_checkpoint(checkpoint)
    OUT_PATH.write_text(json.dumps(checkpoint, indent=2), encoding='utf-8')


def main():
    if not PDF_PATH.exists():
        raise FileNotFoundError(PDF_PATH)
    if not XLSX_PATH.exists():
        raise FileNotFoundError(XLSX_PATH)
    build_checkpoint()


if __name__ == '__main__':
    main()
