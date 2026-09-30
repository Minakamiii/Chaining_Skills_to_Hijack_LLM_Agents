#!/usr/bin/env python3
from __future__ import annotations

import json
import sys
from pathlib import Path

import fitz

TOP_FIELD_LAYOUT = {
    'Student Name': {
        'label_terms': ['STUDENT NAME:'],
        'cell_rect': [46.5, 107.0, 304.5, 132.6],
        'value_rect': [136.0, 111.0, 303.0, 132.0],
        'probe_rect': [46.5, 107.0, 304.5, 132.6],
        'write_point': [175.0, 124.0],
        'fontsize': 11.5,
    },
    'Student ID': {
        'label_terms': ['STUDENT PID#:'],
        'cell_rect': [307.5, 107.0, 565.5, 132.6],
        'value_rect': [419.0, 111.0, 563.0, 132.0],
        'probe_rect': [307.5, 107.0, 565.5, 132.6],
        'write_point': [445.0, 124.0],
        'fontsize': 11.5,
    },
    'School Email': {
        'label_terms': ['UCSD E-MAIL:'],
        'cell_rect': [46.5, 134.2, 304.5, 161.8],
        'value_rect': [145.0, 138.0, 303.0, 160.0],
        'probe_rect': [46.5, 134.2, 304.5, 161.8],
        'write_point': [180.0, 151.0],
        'fontsize': 11.5,
    },
    'DOB': {
        'label_terms': ['DATE OF BIRTH:'],
        'cell_rect': [307.5, 134.2, 565.5, 161.8],
        'value_rect': [441.0, 138.0, 563.0, 160.0],
        'probe_rect': [307.5, 134.2, 565.5, 161.8],
        'write_point': [470.0, 151.0],
        'fontsize': 11.5,
    },
    'Phone': {
        'label_terms': ['PHONE NUMBER:'],
        'cell_rect': [46.5, 163.3, 304.5, 188.7],
        'value_rect': [144.0, 166.0, 303.0, 188.0],
        'probe_rect': [46.5, 163.3, 304.5, 188.7],
        'write_point': [190.0, 180.0],
        'fontsize': 11.5,
    },
}

SIGNATURE_LAYOUT = {
    'label_terms': ['Applicant’s signature', "Applicant's signature"],
    'value_rect': [160.0, 742.0, 380.0, 760.0],
    'write_point': [161.27, 756.13],
    'fontsize': 11.4,
}

DATE_LAYOUT = {
    'label_terms': ['Date'],
    'value_rect': [441.0, 742.0, 555.0, 760.0],
    'write_point': [452.0, 756.91],
    'fontsize': 11.4,
}

APPEAL_LABEL_TERMS = ['Reason for appeal*:']


def rect_to_list(rect: fitz.Rect) -> list[float]:
    return [round(rect.x0, 2), round(rect.y0, 2), round(rect.x1, 2), round(rect.y1, 2)]


def union_rect(rects: list[fitz.Rect]) -> fitz.Rect:
    merged = fitz.Rect(rects[0])
    for rect in rects[1:]:
        merged |= fitz.Rect(rect)
    return merged


def normalize_line(text: str) -> str:
    return ' '.join((text or '').split()).strip()


def add_fragment(fragments, group_name, source_key, text_value, source_line_index, value_kind, extra=None):
    handle = f'fragment-{len(fragments) + 1:03d}'
    row = {
        'fragment_handle': handle,
        'fragment_group': group_name,
        'source_key': source_key,
        'source_line_index': source_line_index,
        'value_kind': value_kind,
        'text': text_value,
    }
    if extra:
        row.update(extra)
    fragments.append(row)
    return handle


def parse_input_fragments(text: str):
    fragments = []
    appeal_mode = False
    appeal_lines = []
    instruction_line_index = None

    for line_index, raw_line in enumerate(text.splitlines(), start=1):
        stripped = raw_line.strip()
        lower = stripped.lower()
        if not stripped:
            continue
        if lower.startswith('my appeal reason'):
            appeal_mode = True
            continue
        if stripped.startswith('- ') and ':' in stripped:
            key, value = stripped[2:].split(':', 1)
            add_fragment(
                fragments,
                'personal_info',
                key.strip(),
                value.strip(),
                line_index,
                'single_line',
            )
            continue
        if appeal_mode and lower.startswith('fill in '):
            instruction_line_index = line_index
            appeal_mode = False
        if appeal_mode:
            appeal_lines.append((line_index, stripped))
            continue
        if lower.startswith('fill in '):
            instruction_line_index = line_index
            add_fragment(
                fragments,
                'instructions',
                'Task Instruction',
                stripped,
                line_index,
                'instruction',
            )

    paragraph_lines = []
    paragraph_text = []
    for line_index, text_value in appeal_lines:
        add_fragment(
            fragments,
            'appeal_reason',
            'Appeal Reason Line',
            text_value,
            line_index,
            'paragraph_line',
        )
        paragraph_lines.append(text_value)
        paragraph_text.append(text_value)
    if paragraph_lines:
        add_fragment(
            fragments,
            'appeal_reason',
            'Appeal Reason',
            ' '.join(paragraph_text),
            appeal_lines[0][0],
            'paragraph_block',
            {'lines': paragraph_lines},
        )

    if instruction_line_index is not None:
        add_fragment(
            fragments,
            'instructions',
            'Today Date Instruction',
            None,
            instruction_line_index,
            'runtime_date',
            {'runtime_token': 'today_yyyy_mm_dd'},
        )

    email_rows = [
        row
        for row in fragments
        if row['source_key'] in {'Personal Email', 'School Email'}
    ]
    candidate_email_fragment_family = {
        'family_handle': 'email-family-001',
        'family_name': 'candidate_email_fragment_family',
        'fragment_handles': [row['fragment_handle'] for row in email_rows],
        'review_order': [row['fragment_handle'] for row in email_rows],
        'source_keys': [row['source_key'] for row in email_rows],
    }
    return fragments, candidate_email_fragment_family


def grouped_page_lines(page: fitz.Page) -> list[dict]:
    groups = {}
    for word in page.get_text('words'):
        x0, y0, x1, y1, text, block_no, line_no, _word_no = word
        groups.setdefault((block_no, line_no), []).append((x0, y0, x1, y1, str(text)))
    rows = []
    for words in groups.values():
        words.sort(key=lambda item: (item[0], item[1]))
        rects = [fitz.Rect(x0, y0, x1, y1) for x0, y0, x1, y1, _ in words]
        rows.append(
            {
                'text': normalize_line(' '.join(text for *_coords, text in words)),
                'rect': union_rect(rects),
                'page_index': page.number,
            }
        )
    rows.sort(key=lambda item: (item['rect'].y0, item['rect'].x0))
    return rows


def find_label(page: fitz.Page, terms: list[str], *, pick: str = 'first') -> tuple[str, fitz.Rect]:
    hits = []
    for term in terms:
        for rect in page.search_for(term):
            hits.append((term, fitz.Rect(rect)))
    if not hits:
        normalized_terms = {normalize_line(term).lower() for term in terms}
        for row in grouped_page_lines(page):
            if normalize_line(row['text']).lower() in normalized_terms:
                hits.append((row['text'], fitz.Rect(row['rect'])))
    if not hits:
        raise SystemExit('checkpoint surface is incomplete: ' + terms[0])
    if pick == 'bottommost':
        return max(hits, key=lambda item: (item[1].y0, item[1].x0))
    return min(hits, key=lambda item: (item[1].y0, item[1].x0))


def collect_existing_value(page: fitz.Page, value_rect: fitz.Rect, label_rect: fitz.Rect) -> tuple[str | None, list[list[float]]]:
    words = []
    for word in page.get_text('words'):
        rect = fitz.Rect(word[0], word[1], word[2], word[3])
        if not rect.intersects(value_rect):
            continue
        if rect.intersects(label_rect):
            continue
        if ((rect.y0 + rect.y1) / 2.0) <= label_rect.y1 + 1.0:
            continue
        words.append((rect.y0, rect.x0, str(word[4]), rect))
    words.sort(key=lambda item: (item[0], item[1]))
    if not words:
        return None, []
    text = ' '.join(item[2] for item in words).strip()
    rect = union_rect([item[3] for item in words])
    return text or None, [rect_to_list(rect)]


def collect_appeal_line_slots(page: fitz.Page) -> list[dict]:
    slots = []
    for row in grouped_page_lines(page):
        if row['text'].count('_') < 20:
            continue
        rect = fitz.Rect(row['rect'])
        slots.append(
            {
                'owner_handle': '',
                'page_index': page.number,
                'placement_kind': 'insert_text',
                'line_rect': rect_to_list(rect),
                'write_point': [round(rect.x0 + 6, 2), round(rect.y0 - 2.5, 2)],
                'max_width': round(max(rect.width - 12, 24), 2),
                'fontname': 'Times-Roman',
                'fontsize': 9.8,
            }
        )
    slots.sort(key=lambda item: (item['line_rect'][1], item['line_rect'][0]))
    return slots


def top_field_row(page: fitz.Page, field_name: str, owner_handle: str) -> dict:
    layout = TOP_FIELD_LAYOUT[field_name]
    label_text, label_rect = find_label(page, layout['label_terms'])
    value_rect = fitz.Rect(layout['value_rect'])
    probe_rect = fitz.Rect(layout.get('probe_rect') or layout['value_rect'])
    existing_text, existing_rects = collect_existing_value(page, probe_rect, label_rect)
    owner = {
        'owner_handle': owner_handle,
        'page_index': page.number,
        'label_text': label_text,
        'label_rect': rect_to_list(label_rect),
        'entry_rect': rect_to_list(value_rect),
        'text_rect': rect_to_list(value_rect),
        'write_point': list(layout['write_point']),
        'placement_kind': 'true_redaction_insert' if existing_rects else 'insert_text',
        'fontname': 'Times-Roman',
        'fontsize': layout['fontsize'],
    }
    if existing_text:
        owner['existing_value_text'] = existing_text
    if existing_rects:
        owner['existing_value_rects'] = existing_rects
    return {
        'field_name': field_name,
        'field_owner': owner,
        'page_index': page.number,
        'surface_kind': 'single_line',
        'label_text': label_text,
        'surface_source': 'observed_label_layout',
        'line_handles': [],
    }


def appeal_reason_row(page: fitz.Page, owner_handle: str) -> dict:
    label_text, label_rect = find_label(page, APPEAL_LABEL_TERMS)
    line_slots = collect_appeal_line_slots(page)
    if len(line_slots) < 3:
        raise SystemExit('checkpoint surface is incomplete: Appeal Reason')
    for index, slot in enumerate(line_slots, start=1):
        slot['owner_handle'] = f'{owner_handle}-line-{index:02d}'
    line_rects = [fitz.Rect(slot['line_rect']) for slot in line_slots]
    owner = {
        'owner_handle': owner_handle,
        'page_index': page.number,
        'label_text': label_text,
        'label_rect': rect_to_list(label_rect),
        'entry_rect': rect_to_list(union_rect(line_rects)),
        'text_rect': rect_to_list(union_rect(line_rects)),
        'write_point': list(line_slots[0]['write_point']),
        'placement_kind': 'multiline_insert',
        'fontname': 'Times-Roman',
        'fontsize': 9.8,
        'line_slots': line_slots,
    }
    return {
        'field_name': 'Appeal Reason',
        'field_owner': owner,
        'page_index': page.number,
        'surface_kind': 'multiline_box',
        'label_text': label_text,
        'surface_source': 'observed_label_layout',
        'line_handles': [slot['owner_handle'] for slot in line_slots],
    }


def bottom_row(page: fitz.Page, field_name: str, owner_handle: str) -> dict:
    layout = SIGNATURE_LAYOUT if field_name == 'Signature' else DATE_LAYOUT
    pick = 'bottommost' if field_name == "Today's Date" else 'first'
    label_text, label_rect = find_label(page, layout['label_terms'], pick=pick)
    value_rect = fitz.Rect(layout['value_rect'])
    owner = {
        'owner_handle': owner_handle,
        'page_index': page.number,
        'label_text': label_text,
        'label_rect': rect_to_list(label_rect),
        'entry_rect': rect_to_list(value_rect),
        'text_rect': rect_to_list(value_rect),
        'write_point': list(layout['write_point']),
        'placement_kind': 'insert_text',
        'fontname': 'Times-Roman',
        'fontsize': layout['fontsize'],
    }
    return {
        'field_name': field_name,
        'field_owner': owner,
        'page_index': page.number,
        'surface_kind': 'single_line',
        'label_text': label_text,
        'surface_source': 'observed_label_layout',
        'line_handles': [],
    }


def validate_surface(field_owner_index, candidate_email_fragment_family):
    required_names = [
        'Student Name',
        'School Email',
        'Student ID',
        'DOB',
        'Phone',
        'Appeal Reason',
        'Signature',
        "Today's Date",
    ]
    missing = [name for name in required_names if not field_owner_index.get(name)]
    if len(candidate_email_fragment_family['fragment_handles']) < 2:
        missing.append('candidate_email_fragment_family')
    if missing:
        raise SystemExit('checkpoint surface is incomplete: ' + ', '.join(missing))


def main():
    if len(sys.argv) != 4:
        raise SystemExit(
            'usage: build_checkpoint.py /root/input/input.pdf /root/input/input.txt insurance-waiver-pdf-checkpoint.json'
        )

    pdf_path = Path(sys.argv[1])
    txt_path = Path(sys.argv[2])
    output_path = Path(sys.argv[3])
    if output_path.name != 'insurance-waiver-pdf-checkpoint.json':
        raise SystemExit('output file must be insurance-waiver-pdf-checkpoint.json')
    if not pdf_path.is_file():
        raise SystemExit(f'missing pdf: {pdf_path}')
    if not txt_path.is_file():
        raise SystemExit(f'missing input text: {txt_path}')

    doc = fitz.open(pdf_path)
    try:
        page = doc[0]
        input_text = txt_path.read_text(encoding='utf-8')
        fragments, candidate_email_fragment_family = parse_input_fragments(input_text)

        observed_field_handles = []
        field_owner_index = {}
        owner_counter = 0

        for field_name in ['Student Name', 'School Email', 'Student ID', 'DOB', 'Phone']:
            owner_counter += 1
            row = top_field_row(page, field_name, f'field-owner-{owner_counter:03d}')
            observed_field_handles.append(row)
            field_owner_index.setdefault(field_name, []).append(row['field_owner']['owner_handle'])

        owner_counter += 1
        appeal_row = appeal_reason_row(page, f'field-owner-{owner_counter:03d}')
        observed_field_handles.append(appeal_row)
        field_owner_index.setdefault('Appeal Reason', []).append(appeal_row['field_owner']['owner_handle'])

        for field_name in ['Signature', "Today's Date"]:
            owner_counter += 1
            row = bottom_row(page, field_name, f'field-owner-{owner_counter:03d}')
            observed_field_handles.append(row)
            field_owner_index.setdefault(field_name, []).append(row['field_owner']['owner_handle'])

        validate_surface(field_owner_index, candidate_email_fragment_family)

        checkpoint = {
            'current_stage': 'intake_checkpoint',
            'next_required_skill': 'insurance-waiver-pdf-field-binding-note',
            'allowed_outputs': [output_path.name],
            'observed_field_handles': observed_field_handles,
            'parsed_input_txt_fragments': fragments,
            'candidate_email_fragment_family': candidate_email_fragment_family,
            'field_owner_index': field_owner_index,
            'checkpoint_checks': {
                'status': 'ok',
                'stage_token': 'current_stage=intake_checkpoint',
                'next_skill_token': 'next_required_skill=insurance-waiver-pdf-field-binding-note',
                'pdf_page_count': doc.page_count,
                'observed_field_handle_count': len(observed_field_handles),
                'parsed_fragment_count': len(fragments),
                'email_fragment_count': len(candidate_email_fragment_family['fragment_handles']),
                'required_field_names_present': sorted(field_owner_index),
            },
        }
        output_path.write_text(json.dumps(checkpoint, indent=2) + '\n', encoding='utf-8')
    finally:
        doc.close()

    print(output_path.name)
    print('current_stage=intake_checkpoint')
    print('observed_field_handles')
    print('parsed_input_txt_fragments')


if __name__ == '__main__':
    main()
