#!/usr/bin/env python3
import argparse
import json
from pathlib import Path

CONTROL_ENTRY_TYPES = {'comment', 'preamble', 'string'}
NEXT_STAGE_KEYS = [
    'source_bib',
    'entry_inventory',
    'normalized_titles',
    'suspect_signals',
    'checkpoint_status',
]
DOUBLE_QUOTE = chr(34)


def collapse_ws(value):
    return ' '.join((value or '').split())


def strip_outer_wrapper(value):
    text = value.strip()
    if len(text) >= 2 and ((text[0] == '{' and text[-1] == '}') or (text[0] == DOUBLE_QUOTE and text[-1] == DOUBLE_QUOTE)):
        return text[1:-1]
    return text


def normalize_field_value(value):
    return collapse_ws(strip_outer_wrapper(value))


def clean_title(value):
    text = normalize_field_value(value)
    text = text.replace('{', ' ').replace('}', ' ')
    text = text.replace('\\', ' ').replace('~', ' ')
    return collapse_ws(text)


def split_entries(text):
    entries = []
    cursor = 0
    length = len(text)
    while cursor < length:
        at_index = text.find('@', cursor)
        if at_index == -1:
            break
        type_cursor = at_index + 1
        while type_cursor < length and text[type_cursor].isspace():
            type_cursor += 1
        while type_cursor < length and (text[type_cursor].isalnum() or text[type_cursor] in '_-'):
            type_cursor += 1
        while type_cursor < length and text[type_cursor].isspace():
            type_cursor += 1
        if type_cursor >= length or text[type_cursor] not in '{(':
            cursor = at_index + 1
            continue
        opener = text[type_cursor]
        closer = '}' if opener == '{' else ')'
        depth = 0
        entry_end = None
        for i in range(type_cursor, length):
            ch = text[i]
            if ch == opener:
                depth += 1
            elif ch == closer:
                depth -= 1
                if depth == 0:
                    entry_end = i + 1
                    break
        if entry_end is None:
            entries.append(text[at_index:].strip())
            break
        entries.append(text[at_index:entry_end].strip())
        cursor = entry_end
    return entries


def read_value(body, cursor):
    while cursor < len(body) and body[cursor].isspace():
        cursor += 1
    if cursor >= len(body):
        return '', cursor
    if body[cursor] == '{':
        depth = 0
        start = cursor
        while cursor < len(body):
            ch = body[cursor]
            if ch == '{' and (cursor == start or body[cursor - 1] != '\\'):
                depth += 1
            elif ch == '}' and body[cursor - 1] != '\\':
                depth -= 1
                if depth == 0:
                    return body[start:cursor + 1], cursor + 1
            cursor += 1
        return body[start:], len(body)
    if body[cursor] == DOUBLE_QUOTE:
        start = cursor
        cursor += 1
        while cursor < len(body):
            if body[cursor] == DOUBLE_QUOTE and body[cursor - 1] != '\\':
                return body[start:cursor + 1], cursor + 1
            cursor += 1
        return body[start:], len(body)
    start = cursor
    while cursor < len(body) and body[cursor] != ',':
        cursor += 1
    return body[start:cursor], cursor


def parse_fields(body):
    fields = {}
    cursor = 0
    while cursor < len(body):
        while cursor < len(body) and (body[cursor].isspace() or body[cursor] == ','):
            cursor += 1
        if cursor >= len(body):
            break
        name_start = cursor
        while cursor < len(body) and (body[cursor].isalnum() or body[cursor] in '_-:'):
            cursor += 1
        field_name = body[name_start:cursor].strip().lower()
        while cursor < len(body) and body[cursor].isspace():
            cursor += 1
        if not field_name or cursor >= len(body) or body[cursor] != '=':
            while cursor < len(body) and body[cursor] != ',':
                cursor += 1
            continue
        cursor += 1
        raw_value, cursor = read_value(body, cursor)
        fields[field_name] = normalize_field_value(raw_value)
        while cursor < len(body) and body[cursor].isspace():
            cursor += 1
        if cursor < len(body) and body[cursor] == ',':
            cursor += 1
    return fields


def unknown_entry(entry_index):
    return {
        'entry_index': entry_index,
        'citation_key': f'unparsed-{entry_index}',
        'entry_type': 'unknown',
        'title_raw': '',
        'title_clean': '',
        'normalized_fields': {},
    }


def parse_entry(entry_text, entry_index):
    if not entry_text.startswith('@'):
        return unknown_entry(entry_index)
    cursor = 1
    while cursor < len(entry_text) and entry_text[cursor].isspace():
        cursor += 1
    type_start = cursor
    while cursor < len(entry_text) and (entry_text[cursor].isalnum() or entry_text[cursor] in '_-'):
        cursor += 1
    entry_type = collapse_ws(entry_text[type_start:cursor]).lower()
    while cursor < len(entry_text) and entry_text[cursor].isspace():
        cursor += 1
    if cursor >= len(entry_text) or entry_text[cursor] not in '{(':
        return unknown_entry(entry_index)
    cursor += 1
    key_start = cursor
    while cursor < len(entry_text) and entry_text[cursor] != ',':
        cursor += 1
    citation_key = collapse_ws(entry_text[key_start:cursor])
    body = entry_text[cursor + 1:-1].strip() if cursor < len(entry_text) else ''
    normalized_fields = parse_fields(body)
    title_raw = normalized_fields.get('title', '')
    return {
        'entry_index': entry_index,
        'citation_key': citation_key or f'entry-{entry_index}',
        'entry_type': entry_type or 'unknown',
        'title_raw': title_raw,
        'title_clean': clean_title(title_raw),
        'normalized_fields': normalized_fields,
    }


def build_suspect_signals(entry):
    if entry['entry_type'] in CONTROL_ENTRY_TYPES:
        return []
    fields = entry['normalized_fields']
    key = entry['citation_key']
    if not key:
        key = 'entry-' + str(entry['entry_index'])
    signals = []
    if not entry['title_clean']:
        signals.append(f'{key}: missing title')
    if not fields.get('author'):
        signals.append(f'{key}: missing author')
    if not fields.get('year'):
        signals.append(f'{key}: missing year')
    if not any(fields.get(name) for name in ('journal', 'booktitle', 'publisher', 'school', 'institution')):
        signals.append(f'{key}: missing venue')
    if not (fields.get('doi') or fields.get('url')):
        signals.append(f'{key}: missing doi/url')
    year = fields.get('year', '')
    if year and (len(year) != 4 or not year.isdigit()):
        signals.append(f'{key}: atypical year format')
    return signals


def write_json(path, payload):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')


def main():
    parser = argparse.ArgumentParser(description='Build a bibliography intake checkpoint and continuation gate.')
    parser.add_argument('--source', required=True, help='Path to the source BibTeX file.')
    parser.add_argument('--checkpoint', required=True, help='Path to write workflow/intake_checkpoint.json.')
    parser.add_argument('--gate', required=True, help='Path to write workflow/continuation_gate.json.')
    args = parser.parse_args()

    source_path = Path(args.source)
    checkpoint_path = Path(args.checkpoint)
    gate_path = Path(args.gate)

    entries_text = source_path.read_text(encoding='utf-8')
    parsed_entries = [
        parse_entry(entry_text, index)
        for index, entry_text in enumerate(split_entries(entries_text), start=1)
    ]
    normalized_titles = [entry['title_clean'] for entry in parsed_entries]
    suspect_signals = []
    for entry in parsed_entries:
        suspect_signals.extend(build_suspect_signals(entry))

    checkpoint = {
        'source_bib': str(source_path.resolve()),
        'entry_inventory': parsed_entries,
        'normalized_titles': normalized_titles,
        'suspect_signals': suspect_signals,
        'checkpoint_status': 'intake_frozen',
    }
    gate = {
        'current_record': str(checkpoint_path),
        'next_stage_consumes_exact_keys': NEXT_STAGE_KEYS,
        'checkpoint_status': 'intake_frozen',
        'continuation_note': 'Continue from the frozen checkpoint instead of rescanning /root/test.bib.',
    }

    write_json(checkpoint_path, checkpoint)
    write_json(gate_path, gate)


if __name__ == '__main__':
    main()
