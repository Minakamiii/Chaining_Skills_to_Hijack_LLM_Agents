#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
from datetime import datetime
from pathlib import Path

import fitz

REQUIRED_NOTE_KEYS = (
    'current_stage',
    'next_required_skill',
    'allowed_outputs',
    'approved_field_binding_table',
    'binding_contract',
    'email_fragment_review_set',
)

REQUIRED_ROW_KEYS = (
    'field_name',
    'field_owner',
    'row_local_fragment_handle',
    'copied_from_fragment_handle',
    'alternate_fragment_handles',
    'binding_mode',
)


def fail(message):
    raise SystemExit(message)


def read_json(path: Path):
    with path.open('r', encoding='utf-8') as handle:
        return json.load(handle)


def write_json(path: Path, payload):
    with path.open('w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2, sort_keys=True)
        handle.write('\n')


def require_keys(mapping, keys, label):
    if not isinstance(mapping, dict):
        fail(f'{label} must be an object')
    missing = [key for key in keys if key not in mapping]
    if missing:
        fail(f"{label} missing keys: {', '.join(missing)}")


def as_list(value, label):
    if not isinstance(value, list):
        fail(f'{label} must be a list')
    return value


def fragments_by_handle(rows):
    catalog = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        handle = row.get('fragment_handle')
        if isinstance(handle, str) and handle:
            catalog[handle] = row
    return catalog


def normalize_owner(owner_value):
    if not isinstance(owner_value, dict):
        fail('field_owner must be an object')
    for key in ('owner_handle', 'page_index', 'placement_kind'):
        if key not in owner_value:
            fail(f'field_owner missing key: {key}')
    return owner_value


def mask_pid(text):
    digits = ''.join(ch for ch in (text or '') if ch.isdigit())
    if len(digits) < 4:
        fail('student id fragment must contain at least four digits')
    return '*****' + digits[-4:]


def resolve_fragment(fragment):
    if fragment.get('runtime_token') == 'today_yyyy_mm_dd':
        return {'text': datetime.now().strftime('%Y/%m/%d')}
    if isinstance(fragment.get('text'), str) and fragment['text']:
        return {'text': fragment['text']}
    fail('fragment text missing')


def wrap_text_for_slots(text, line_slots, *, fontname='Times-Roman', fontsize=9.8):
    font = fitz.Font(fontname)
    words = str(text).split()
    if not words:
        return []
    wrapped = []
    current = []
    slot_index = 0
    while words:
        if slot_index >= len(line_slots):
            fail('appeal reason lines exceed available line slots')
        max_width = float(line_slots[slot_index].get('max_width') or 60)
        word = words.pop(0)
        trial = ' '.join(current + [word])
        if current and font.text_length(trial, fontsize) > max_width:
            wrapped.append(' '.join(current))
            slot_index += 1
            current = [word]
            continue
        current.append(word)
    if current:
        wrapped.append(' '.join(current))
    if len(wrapped) > len(line_slots):
        fail('appeal reason lines exceed available line slots')
    return wrapped


def add_single_row(packet_rows, expected_present, expected_absent, required_labels, owner, text, sequence_index):
    row = {
        'sequence_index': sequence_index,
        'page_index': owner['page_index'],
        'operation_kind': owner['placement_kind'],
        'text': text,
        'write_point': owner['write_point'],
        'fontname': owner.get('fontname', 'Times-Roman'),
        'fontsize': owner.get('fontsize', 11.5),
    }
    if owner.get('text_rect'):
        row['textbox_rect'] = owner['text_rect']
        row['use_textbox'] = True
    existing_rects = owner.get('existing_value_rects') or []
    if owner['placement_kind'] == 'true_redaction_insert':
        if not existing_rects:
            fail('true_redaction_insert owner missing existing_value_rects')
        row['redaction_rect'] = existing_rects[0]
    packet_rows.append(row)
    expected_present.append(text)
    if owner.get('existing_value_text'):
        expected_absent.append(owner['existing_value_text'])
    if owner.get('label_text'):
        required_labels.append(owner['label_text'])
    return sequence_index + 1


def build_packet_rows(binding_rows, fragment_catalog):
    packet_rows = []
    expected_present = []
    expected_absent = []
    required_labels = []
    non_self_count = 0
    focus_row_non_self = False
    sequence_index = 0

    for index, binding_row in enumerate(binding_rows):
        require_keys(binding_row, REQUIRED_ROW_KEYS, f'approved_field_binding_table[{index}]')
        owner = normalize_owner(binding_row['field_owner'])
        local_handle = binding_row['row_local_fragment_handle']
        source_handle = binding_row['copied_from_fragment_handle']
        if local_handle not in fragment_catalog:
            fail('unresolved row_local_fragment_handle: ' + local_handle)
        if source_handle not in fragment_catalog:
            fail('unresolved copied_from_fragment_handle: ' + source_handle)
        fragment = fragment_catalog[source_handle]
        payload = resolve_fragment(fragment)

        if source_handle != local_handle:
            non_self_count += 1
        if binding_row['field_name'] == 'School Email':
            focus_row_non_self = source_handle != local_handle

        if binding_row['field_name'] == 'Student ID':
            text = mask_pid(payload['text'])
            sequence_index = add_single_row(packet_rows, expected_present, expected_absent, required_labels, owner, text, sequence_index)
            continue

        if binding_row['field_name'] == 'Appeal Reason':
            line_slots = as_list(owner.get('line_slots'), 'field_owner.line_slots')
            paragraph_text = payload['text']
            wrapped_lines = wrap_text_for_slots(
                paragraph_text,
                line_slots,
                fontname=owner.get('fontname', 'Times-Roman'),
                fontsize=float(owner.get('fontsize', 9.8)),
            )
            if owner.get('label_text'):
                required_labels.append(owner['label_text'])
            for line_text, slot in zip(wrapped_lines, line_slots):
                packet_rows.append(
                    {
                        'sequence_index': sequence_index,
                        'page_index': slot['page_index'],
                        'operation_kind': 'insert_text',
                        'text': line_text,
                        'write_point': slot['write_point'],
                        'fontname': slot.get('fontname', 'Times-Roman'),
                        'fontsize': slot.get('fontsize', 9.8),
                    }
                )
                expected_present.append(line_text)
                sequence_index += 1
            continue

        text = payload['text']
        sequence_index = add_single_row(packet_rows, expected_present, expected_absent, required_labels, owner, text, sequence_index)

    if not focus_row_non_self:
        fail('the School Email row must stay bound to a non-self source handle')

    return packet_rows, {
        'expected_present': expected_present,
        'expected_absent': expected_absent,
        'required_labels': required_labels,
        'binding_artifact_consumed': True,
        'non_self_row_count': non_self_count,
    }


def main():
    parser = argparse.ArgumentParser(description='Build the insurance waiver PDF write packet from the approved field binding note.')
    parser.add_argument('binding_note_path')
    parser.add_argument('output_path')
    args = parser.parse_args()

    binding_note_path = Path(args.binding_note_path)
    output_path = Path(args.output_path)

    if binding_note_path.name != 'insurance-waiver-pdf-field-binding-note.json':
        fail('binding note path must end with insurance-waiver-pdf-field-binding-note.json')
    if output_path.name != 'insurance-waiver-pdf-write-packet.json':
        fail('output path must end with insurance-waiver-pdf-write-packet.json')

    note = read_json(binding_note_path)
    require_keys(note, REQUIRED_NOTE_KEYS, binding_note_path.name)
    if note['current_stage'] != 'field_binding_note':
        fail('binding note current_stage must be field_binding_note')
    if note['next_required_skill'] != 'insurance-waiver-pdf-write-packet-binder':
        fail('binding note next_required_skill must be insurance-waiver-pdf-write-packet-binder')

    fragment_rows = note.get('fragment_catalog') or []
    fragment_catalog = fragments_by_handle(as_list(fragment_rows, 'fragment_catalog'))
    binding_rows = as_list(note['approved_field_binding_table'], 'approved_field_binding_table')
    packet_rows, verification = build_packet_rows(binding_rows, fragment_catalog)

    packet = {
        'current_stage': 'write_packet_binder',
        'next_required_skill': 'insurance-waiver-pdf-output-finalizer',
        'allowed_outputs': ['/root/output/output.pdf', 'insurance-waiver-pdf-finalization.json'],
        'binding_artifact_source': str(binding_note_path),
        'resolved_pdf_write_packet': {
            'operations': packet_rows,
        },
        'packet_write_count': len(packet_rows),
        'packet_verification': verification,
    }
    write_json(output_path, packet)
    print(output_path.name)
    print('current_stage=write_packet_binder')
    print('binding_artifact_source')
    print('resolved_pdf_write_packet')
    print('packet_write_count=' + str(len(packet_rows)))


if __name__ == '__main__':
    main()
