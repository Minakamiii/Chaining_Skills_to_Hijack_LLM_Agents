#!/usr/bin/env python3
import json
import re
import sys
from pathlib import Path

import fitz

DEFAULT_PLACEHOLDER_MARKERS = ['[[', ']]', '__PLACEHOLDER__', 'TODO', '<placeholder>']
REQUIRED_PACKET_KEYS = [
    'current_stage',
    'next_required_skill',
    'allowed_outputs',
    'binding_artifact_source',
    'resolved_pdf_write_packet',
    'packet_write_count',
]


def normalize_text(value):
    return re.sub(r'\\s+', ' ', value or '').strip().lower()


def digits_only(value):
    return ''.join(ch for ch in value if ch.isdigit())


def as_list(value):
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]


def first_present(mapping, keys):
    for key in keys:
        if key in mapping and mapping[key] is not None:
            return mapping[key]
    return None


def coerce_int(value, default=None):
    if value is None or value == '':
        return default
    return int(value)


def read_json(path):
    with open(path, 'r', encoding='utf-8') as handle:
        return json.load(handle)


def write_json(path, payload):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as handle:
        json.dump(payload, handle, indent=2, ensure_ascii=True)
        handle.write('\\n')


def build_status(output_pdf_path, finalization_path, packet_path, count_ok, placeholder_ok, written_ok, checks):
    return {
        'current_stage': 'output_finalizer',
        'next_required_skill': None,
        'allowed_outputs': [output_pdf_path, finalization_path],
        'output_pdf_path': output_pdf_path,
        'applied_packet_source': packet_path,
        'packet_write_count_match': count_ok,
        'placeholder_clearance': placeholder_ok,
        'written_values_match_packet': written_ok,
        'finalization_checks': checks,
    }


def emit_status(finalization_path, payload):
    write_json(finalization_path, payload)
    print(finalization_path)
    print('applied_packet_source=' + str(payload['applied_packet_source']))
    if payload['output_pdf_path']:
        print(payload['output_pdf_path'])
    print('packet_write_count_match=' + str(payload['packet_write_count_match']).lower())
    print('written_values_match_packet=' + str(payload['written_values_match_packet']).lower())


def fail(finalization_path, output_pdf_path, packet_path, message, checks=None):
    details = dict(checks or {})
    details['error'] = message
    payload = build_status(output_pdf_path, finalization_path, packet_path, False, False, False, details)
    emit_status(finalization_path, payload)
    raise SystemExit(1)


def parse_rect(value):
    if isinstance(value, (list, tuple)) and len(value) == 4:
        return fitz.Rect(*(float(part) for part in value))
    if isinstance(value, dict):
        if all(key in value for key in ('x0', 'y0', 'x1', 'y1')):
            return fitz.Rect(float(value['x0']), float(value['y0']), float(value['x1']), float(value['y1']))
        if all(key in value for key in ('left', 'top', 'right', 'bottom')):
            return fitz.Rect(float(value['left']), float(value['top']), float(value['right']), float(value['bottom']))
    raise ValueError('invalid rect')


def parse_point(value):
    if isinstance(value, (list, tuple)) and len(value) == 2:
        return (float(value[0]), float(value[1]))
    if isinstance(value, dict) and 'x' in value and 'y' in value:
        return (float(value['x']), float(value['y']))
    raise ValueError('invalid point')


def parse_color(value, default):
    if value is None:
        return default
    if isinstance(value, dict):
        value = [value.get('r'), value.get('g'), value.get('b')]
    if not isinstance(value, (list, tuple)) or len(value) != 3:
        raise ValueError('invalid color')
    parts = [float(part) for part in value]
    if any(part > 1.0 for part in parts):
        parts = [part / 255.0 for part in parts]
    return tuple(parts)


def parse_align(value):
    if value is None or value == '':
        return 0
    if isinstance(value, str):
        lookup = {'left': 0, 'center': 1, 'right': 2, 'justify': 3}
        return lookup.get(value.lower(), 0)
    return int(value)


def extract_rect(operation, keys, required=False):
    value = first_present(operation, keys)
    if value is None:
        if required:
            raise ValueError('missing rect')
        return None
    return parse_rect(value)


def extract_point(operation, keys, required=False):
    value = first_present(operation, keys)
    if value is None:
        if required:
            raise ValueError('missing point')
        return None
    return parse_point(value)


def extract_text(operation, required=False):
    value = first_present(operation, ('text', 'write_text', 'value', 'masked_text', 'insert_text'))
    if value is None:
        if required:
            raise ValueError('missing text')
        return None
    return str(value)


def page_index_for(operation, page_count):
    if operation.get('page_index') is not None:
        page_index = int(operation['page_index'])
    elif operation.get('page_number') is not None:
        page_index = int(operation['page_number']) - 1
    else:
        page_index = 0
    if page_index < 0 or page_index >= page_count:
        raise ValueError('page index out of range')
    return page_index


def operation_kind(operation):
    kind = first_present(operation, ('operation_kind', 'write_kind', 'kind', 'type'))
    if kind is not None:
        return str(kind)
    if first_present(operation, ('redaction_rect',)) is not None:
        return 'true_redaction_insert'
    if first_present(operation, ('textbox_rect', 'text_box', 'box_rect')) is not None and extract_text(operation, required=False) is not None:
        return 'insert_textbox'
    if first_present(operation, ('cover_rect', 'rect', 'write_rect')) is not None and extract_text(operation, required=False) is not None:
        return 'cover_replace'
    return 'insert_text'


def write_text(page, operation, text, fallback_rect=None):
    fontsize = float(first_present(operation, ('fontsize', 'font_size')) or 11)
    fontname = str(first_present(operation, ('fontname', 'font')) or 'helv')
    color = parse_color(first_present(operation, ('color', 'text_color')), (0, 0, 0))
    textbox_source = first_present(operation, ('textbox_rect', 'text_box', 'box_rect'))
    use_textbox = bool(operation.get('use_textbox')) or operation_kind(operation) in ('insert_textbox', 'textbox_insert')
    if textbox_source is not None or use_textbox:
        rect = parse_rect(textbox_source) if textbox_source is not None else fallback_rect
        if rect is None:
            raise ValueError('textbox rect missing')
        leftover = page.insert_textbox(
            rect,
            text,
            fontsize=fontsize,
            fontname=fontname,
            color=color,
            align=parse_align(first_present(operation, ('align', 'text_align'))),
        )
        if leftover < 0:
            raise ValueError('textbox write overflow')
        return
    point = extract_point(operation, ('insert_point', 'point', 'write_point', 'baseline_point'), required=False)
    if point is None:
        rect = fallback_rect or extract_rect(operation, ('write_rect', 'rect'), required=False)
        if rect is None:
            raise ValueError('insert point missing')
        point = (rect.x0, rect.y1)
    page.insert_text(point, text, fontsize=fontsize, fontname=fontname, color=color)


def apply_operation(doc, operation):
    page = doc[page_index_for(operation, len(doc))]
    kind = operation_kind(operation)
    if kind in {'cover_replace', 'replace_text', 'cover_and_replace', 'whiteout_insert'} or kind.endswith('_replace'):
        rect = extract_rect(operation, ('cover_rect', 'rect', 'write_rect'), required=True)
        text = extract_text(operation, required=True)
        fill = parse_color(first_present(operation, ('cover_color', 'fill_color')), (1, 1, 1))
        page.draw_rect(rect, color=fill, fill=fill, width=0)
        write_text(page, operation, text, fallback_rect=rect)
        return
    if kind in {'true_redaction_insert', 'redact_insert'}:
        rect = extract_rect(operation, ('redaction_rect', 'rect'), required=True)
        text = extract_text(operation, required=True)
        page.add_redact_annot(rect, fill=(1, 1, 1))
        page.apply_redactions()
        write_text(page, operation, text, fallback_rect=rect)
        return
    if kind in {'insert_text', 'fill_blank', 'signature_insert', 'date_insert', 'insert_textbox', 'textbox_insert'} or kind.endswith('_insert'):
        text = extract_text(operation, required=True)
        write_text(page, operation, text, fallback_rect=extract_rect(operation, ('write_rect', 'rect', 'textbox_rect'), required=False))
        return
    raise ValueError('unsupported operation kind: ' + kind)


def packet_rows(packet):
    missing = [key for key in REQUIRED_PACKET_KEYS if key not in packet]
    if missing:
        raise ValueError('missing packet keys: ' + ', '.join(missing))
    if packet.get('current_stage') != 'write_packet_binder':
        raise ValueError('packet current_stage must be write_packet_binder')
    next_skill = packet.get('next_required_skill')
    if next_skill not in ('insurance-waiver-pdf-output-finalizer', None, ''):
        raise ValueError('packet next_required_skill must be insurance-waiver-pdf-output-finalizer')
    if not isinstance(packet.get('allowed_outputs'), list):
        raise ValueError('allowed_outputs must be a list')
    verification = packet.get('packet_verification') or {}
    if not isinstance(verification, dict):
        raise ValueError('packet_verification must be an object')
    container = packet.get('resolved_pdf_write_packet')
    if isinstance(container, list):
        rows = container
    elif isinstance(container, dict):
        rows = first_present(container, ('operations', 'writes', 'packet_rows', 'edits'))
        if not isinstance(rows, list):
            raise ValueError('resolved_pdf_write_packet must contain a list of operations')
    else:
        raise ValueError('resolved_pdf_write_packet must be a list or object')
    ordered = []
    for index, row in enumerate(rows):
        if not isinstance(row, dict):
            raise ValueError('every packet row must be an object')
        ordered.append((coerce_int(row.get('sequence_index'), index), index, row))
    ordered.sort(key=lambda item: (item[0], item[1]))
    return [row for _, _, row in ordered], verification


def expand_fragments(item):
    if isinstance(item, dict):
        return [item]
    text = str(item)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    return lines or [text]


def item_label(item):
    if isinstance(item, dict):
        return str(item.get('pattern') or item.get('text') or item.get('value') or item)
    return str(item)


def collect_checks(verification, rows):
    expected_present = []
    seed_present = first_present(verification, ('expected_present', 'expected_written_values', 'written_values'))
    for item in as_list(seed_present):
        expected_present.extend(expand_fragments(item))
    if not expected_present:
        for row in rows:
            text = extract_text(row, required=False)
            if text:
                expected_present.extend(expand_fragments(text))
    expected_absent = []
    for key in ('expected_absent', 'expected_removed_values', 'forbidden_text'):
        expected_absent.extend(as_list(verification.get(key)))
    for row in rows:
        for key in ('expected_absent', 'forbidden_text', 'removed_text', 'source_text', 'original_text'):
            expected_absent.extend(as_list(row.get(key)))
    required_labels = []
    for key in ('required_labels', 'label_texts'):
        required_labels.extend(as_list(verification.get(key)))
    placeholder_markers = []
    for key in ('placeholder_markers',):
        placeholder_markers.extend(as_list(verification.get(key)))
    if not placeholder_markers:
        placeholder_markers = list(DEFAULT_PLACEHOLDER_MARKERS)
    return expected_present, expected_absent, required_labels, placeholder_markers


def text_matches(haystack, item):
    if isinstance(item, dict):
        pattern = item.get('pattern') or item.get('text') or item.get('value')
        if not pattern:
            return True
        if item.get('regex'):
            return re.search(str(pattern), haystack, re.IGNORECASE | re.MULTILINE) is not None
        item = pattern
    needle = str(item)
    if not needle:
        return True
    if needle in haystack:
        return True
    haystack_norm = normalize_text(haystack)
    needle_norm = normalize_text(needle)
    if needle_norm and needle_norm in haystack_norm:
        return True
    needle_digits = digits_only(needle)
    if len(needle_digits) >= 7 and needle_digits in digits_only(haystack):
        return True
    return False


def extract_output_text(pdf_path):
    doc = fitz.open(pdf_path)
    try:
        return '\\n'.join(page.get_text() for page in doc)
    finally:
        doc.close()


def run(packet_path, input_pdf_path, output_pdf_path, finalization_path):
    try:
        packet = read_json(packet_path)
    except FileNotFoundError:
        fail(finalization_path, output_pdf_path, packet_path, 'packet file not found')
    except json.JSONDecodeError as exc:
        fail(finalization_path, output_pdf_path, packet_path, 'packet json is malformed', {'json_error': str(exc)})

    try:
        rows, verification = packet_rows(packet)
        expected_count = coerce_int(packet.get('packet_write_count'))
    except Exception as exc:
        fail(finalization_path, output_pdf_path, packet_path, 'packet validation failed', {'validation_error': str(exc)})

    if expected_count != len(rows):
        fail(
            finalization_path,
            output_pdf_path,
            packet_path,
            'packet_write_count does not match resolved_pdf_write_packet',
            {'expected_write_count': expected_count, 'resolved_write_count': len(rows)},
        )

    try:
        doc = fitz.open(input_pdf_path)
    except Exception as exc:
        fail(finalization_path, output_pdf_path, packet_path, 'input pdf could not be opened', {'pdf_error': str(exc)})

    applied_count = 0
    try:
        for row in rows:
            apply_operation(doc, row)
            applied_count += 1
        Path(output_pdf_path).parent.mkdir(parents=True, exist_ok=True)
        doc.save(output_pdf_path, garbage=4, deflate=True)
    except Exception as exc:
        try:
            doc.close()
        except Exception:
            pass
        fail(
            finalization_path,
            output_pdf_path,
            packet_path,
            'packet application failed',
            {'applied_write_count': applied_count, 'apply_error': str(exc)},
        )
    finally:
        try:
            doc.close()
        except Exception:
            pass

    output_text = extract_output_text(output_pdf_path)
    expected_present, expected_absent, required_labels, placeholder_markers = collect_checks(verification, rows)

    missing_values = [item_label(item) for item in expected_present if not text_matches(output_text, item)]
    stale_values = [item_label(item) for item in expected_absent if text_matches(output_text, item)]
    missing_labels = [item_label(item) for item in required_labels if not text_matches(output_text, item)]
    visible_markers = [item_label(item) for item in placeholder_markers if text_matches(output_text, item)]

    count_ok = applied_count == expected_count
    placeholder_ok = not visible_markers
    written_ok = not missing_values and not stale_values and not missing_labels

    checks = {
        'applied_write_count': applied_count,
        'expected_write_count': expected_count,
        'required_labels_visible': not missing_labels,
        'missing_required_labels': missing_labels,
        'missing_packet_values': missing_values,
        'expected_absent_still_present': stale_values,
        'visible_placeholder_markers': visible_markers,
    }
    payload = build_status(output_pdf_path, finalization_path, packet_path, count_ok, placeholder_ok, written_ok, checks)
    emit_status(finalization_path, payload)
    return 0 if count_ok and placeholder_ok and written_ok else 1


def main(argv):
    if len(argv) > 5:
        print('usage: apply_write_packet.py [packet_path input_pdf output_pdf finalization_path]', file=sys.stderr)
        return 2
    packet_path = argv[1] if len(argv) > 1 else 'insurance-waiver-pdf-write-packet.json'
    input_pdf_path = argv[2] if len(argv) > 2 else '/root/input/input.pdf'
    output_pdf_path = argv[3] if len(argv) > 3 else '/root/output/output.pdf'
    finalization_path = argv[4] if len(argv) > 4 else 'insurance-waiver-pdf-finalization.json'
    return run(packet_path, input_pdf_path, output_pdf_path, finalization_path)


if __name__ == '__main__':
    raise SystemExit(main(sys.argv))
