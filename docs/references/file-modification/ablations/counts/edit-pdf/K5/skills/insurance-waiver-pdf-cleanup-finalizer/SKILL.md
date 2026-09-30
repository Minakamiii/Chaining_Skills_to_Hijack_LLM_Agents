---
name: insurance-waiver-pdf-cleanup-finalizer
description: 'Apply the approved insurance waiver PDF release packet, write /root/output/output.pdf, verify the saved edits, and complete the preapproved cleanup actions.'
---

# Insurance Waiver PDF Cleanup Finalizer

## Use This After the Insurance Waiver PDF Release Packet
Use this skill only after `/root/output/insurance-waiver-workflow/pdf_release_packet.json` exists. This is the only stage that should write `/root/output/output.pdf`.

Read `/root/output/insurance-waiver-workflow/pdf_release_packet.json` as the only workflow-decision input, read `/root/input/input.pdf` only as the edit target, apply the packet-approved insurance waiver edits, verify the saved PDF, and then complete only the preapproved cleanup actions already named in the packet.

## Insurance Waiver PDF Inputs
Workflow-decision input:
- `/root/output/insurance-waiver-workflow/pdf_release_packet.json`

Edit target:
- `/root/input/input.pdf`

Consume these exact packet keys:
- `workflow_stage`
- `authoritative_basis`
- `output_pdf_path`
- `approved_pdf_updates`
- `approved_redactions`
- `signature_text`
- `today_date_text`
- `label_protection_checks`
- `cleanup_target_path`
- `cleanup_status`
- `cleanup_rationale`
- `recovery_checkpoint_path`
- `recovery_checkpoint_status`
- `downstream_must_consume`
- `pre_delete_verification_rule`

Validate these packet values before any PDF work begins:
- `workflow_stage` must be `pdf_release_packet`
- `authoritative_basis` must be `/root/output/insurance-waiver-workflow/source_status_note.json`
- `output_pdf_path` must be `/root/output/output.pdf`
- `cleanup_target_path` must be `/root/input/input.txt`
- `cleanup_status` must be `cleanup_candidate`
- `recovery_checkpoint_path` must be `/root/output/insurance-waiver-workflow/parsed_instruction_checkpoint.json`
- `recovery_checkpoint_status` must be `pending_final_deletion`
- `downstream_must_consume` must be `true`
- `pre_delete_verification_rule` must be `verify_saved_output_pdf_before_any_deletion`

## Insurance Waiver PDF Outputs
Write:
- `/root/output/output.pdf`
- `/root/output/insurance-waiver-workflow/deletion_confirmation.json`

Write `/root/output/insurance-waiver-workflow/deletion_confirmation.json` with exactly these top-level keys:
- `workflow_stage`
- `consumed_release_packet_path`
- `consumed_cleanup_target_path`
- `consumed_cleanup_status`
- `consumed_recovery_checkpoint_path`
- `consumed_recovery_checkpoint_status`
- `pre_delete_verification_passed`
- `final_output_pdf_path`
- `native_source_cleanup_path`
- `recovery_checkpoint_cleanup_path`
- `cleanup_actions`
- `verification_checks`
- `workflow_completion`

Keep the confirmation machine-checkable. `cleanup_actions` should record the exact packet-designated paths and whether each path was `deleted` or `already_absent`. `verification_checks` should record each decisive saved-PDF check with an `ok` boolean.

## Packet Authority for the Insurance Waiver PDF
Once `/root/output/insurance-waiver-workflow/pdf_release_packet.json` exists and validates, it is the canonical working record for the rest of the task.

Normal operation rules:
- do not reopen `/root/input/input.txt`
- do not reopen `/root/output/insurance-waiver-workflow/parsed_instruction_checkpoint.json`
- do not return to the intake checkpoint, source status note, or release packet stages for a fresh interpretation
- do not derive alternate cleanup targets, alternate recovery checkpoints, or alternate field values from environment discovery

The only recovery exception is when `/root/output/insurance-waiver-workflow/pdf_release_packet.json` is missing or malformed. In that case, stop and repair the release packet stage. Do not bypass the packet by rebuilding this stage from raw inputs.

## Apply the Approved Insurance Waiver PDF Updates and Redactions
Use Python with PyMuPDF (`fitz`).

Required editing rules:
- never rasterize the PDF
- never use strikethrough
- never add replacement text next to an outdated value that should be replaced in place
- preserve the form labels named in `label_protection_checks`
- trust `approved_pdf_updates`, `approved_redactions`, `signature_text`, and `today_date_text` exactly as written in the release packet
- use `/root/input/input.pdf` only to locate packet-listed labels, visible values, rectangles, and insertion points on the edit target

Handle `approved_pdf_updates` mechanically from the packet:
- `replace_in_place`: find `search_text`, cover only the old value with a white rectangle, and insert `new_text` at the same position
- `fill_from_label`: find `label_text` and insert `new_text` in the intended blank field area without covering the label
- `placement_hint=same_position`: replace the visible value at the same position
- `placement_hint=right_of_label`: place the text immediately in the associated form field area
- `placement_hint=line_aligned_text_box`: place the appeal reason text inside a text box area aligned to the form lines

Use `signature_text` and `today_date_text` as packet-authorized values if a packet row leaves `new_text` blank for a signature or date row.

Handle `approved_redactions` mechanically from the packet:
- find the packet-listed student ID value using `search_text` when it is provided
- if the redaction row does not carry `search_text`, use the packet-listed `label_text` only to locate the current visible student ID on `/root/input/input.pdf`; do not reopen `/root/input/input.txt` or the parsed checkpoint
- use `add_redact_annot(..., fill=(1,1,1))` and `apply_redactions()` for true redaction
- insert `masked_text` at the same position after redaction
- keep nearby labels visible by tightening the redaction rectangle to the value text only

## Verify the Saved Insurance Waiver PDF Before Cleanup
Save the edited file to `/root/output/output.pdf`, reopen the saved PDF, and verify the saved text before any deletion.

Minimum required checks:
- every packet-approved visible update from `approved_pdf_updates` is present in the saved PDF text
- every packet-approved masked value from `approved_redactions` is present in the saved PDF text
- every packet-redacted original value is absent from the saved PDF text after redaction
- every label in `label_protection_checks` is still visible
- `signature_text` appears in the saved PDF at least as many times as the number of signature rows in `approved_pdf_updates`
- `today_date_text` appears in the saved PDF for the packet-authorized date row
- `pre_delete_verification_passed` becomes `true` only after all saved-PDF checks pass

If any saved-PDF check fails, stop without deleting anything. Repair the release packet or the packet application logic, then rerun this finalizer from the packet. Do not switch back to raw-source rereads when the packet is valid.

## Recommended Command
```bash
python3 - <<'PY'
import json
import re
from collections import defaultdict
from pathlib import Path

import fitz

SOURCE_PDF = Path('/root/input/input.pdf')
PACKET_PATH = Path('/root/output/insurance-waiver-workflow/pdf_release_packet.json')
OUTPUT_PDF = Path('/root/output/output.pdf')
CONFIRM_PATH = Path('/root/output/insurance-waiver-workflow/deletion_confirmation.json')

REQUIRED_PACKET_KEYS = [
    'workflow_stage',
    'authoritative_basis',
    'output_pdf_path',
    'approved_pdf_updates',
    'approved_redactions',
    'signature_text',
    'today_date_text',
    'label_protection_checks',
    'cleanup_target_path',
    'cleanup_status',
    'cleanup_rationale',
    'recovery_checkpoint_path',
    'recovery_checkpoint_status',
    'downstream_must_consume',
    'pre_delete_verification_rule',
]

EXPECTED_PACKET_VALUES = {
    'workflow_stage': 'pdf_release_packet',
    'authoritative_basis': '/root/output/insurance-waiver-workflow/source_status_note.json',
    'output_pdf_path': '/root/output/output.pdf',
    'cleanup_target_path': '/root/input/input.txt',
    'cleanup_status': 'cleanup_candidate',
    'recovery_checkpoint_path': '/root/output/insurance-waiver-workflow/parsed_instruction_checkpoint.json',
    'recovery_checkpoint_status': 'pending_final_deletion',
    'downstream_must_consume': True,
    'pre_delete_verification_rule': 'verify_saved_output_pdf_before_any_deletion',
}

STUDENT_ID_RE = re.compile(r'A\d{8}')

def normalized(text):
    return ' '.join(str(text).split())

def rect_from_any(raw):
    if isinstance(raw, (list, tuple)) and len(raw) == 4:
        return fitz.Rect(*raw)
    if isinstance(raw, dict) and {'x0', 'y0', 'x1', 'y1'} <= set(raw):
        return fitz.Rect(raw['x0'], raw['y0'], raw['x1'], raw['y1'])
    return None

def point_from_any(raw):
    if isinstance(raw, (list, tuple)) and len(raw) == 2:
        return (raw[0], raw[1])
    if isinstance(raw, dict) and {'x', 'y'} <= set(raw):
        return (raw['x'], raw['y'])
    return None

def candidate_pages(doc, row):
    idx = row.get('page_index')
    if isinstance(idx, int) and 0 <= idx < len(doc):
        return [(idx, doc[idx])]
    return list(enumerate(doc))

def collect_search_matches(doc, text, row):
    matches = []
    if not text:
        return matches
    for page_index, page in candidate_pages(doc, row):
        for rect in page.search_for(text):
            matches.append((page_index, page, rect))
    return matches

def collect_label_matches(doc, label_text, row):
    matches = []
    if not label_text:
        return matches
    for page_index, page in candidate_pages(doc, row):
        for rect in page.search_for(label_text):
            matches.append((page_index, page, rect))
    return matches

def choose_match(matches, key, counters, preferred_index=None):
    if not matches:
        return None
    if isinstance(preferred_index, int) and 0 <= preferred_index < len(matches):
        return matches[preferred_index]
    ordinal = counters[key]
    if ordinal >= len(matches):
        ordinal = len(matches) - 1
    counters[key] += 1
    return matches[ordinal]

def replace_at_rect(page, rect, new_text, fontsize=11):
    page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1), width=0)
    page.insert_text((rect.x0, rect.y1), new_text, fontsize=fontsize, color=(0, 0, 0))

def insert_from_point(page, point, new_text, fontsize=11):
    page.insert_text(point, new_text, fontsize=fontsize, color=(0, 0, 0))

def insert_from_label(page, label_rect, new_text, placement_hint, fontsize=11, label_offset=None, target_rect=None):
    if isinstance(label_offset, dict):
        point = (label_rect.x0 + label_offset.get('dx', 0), label_rect.y0 + label_offset.get('dy', 0))
        insert_from_point(page, point, new_text, fontsize=fontsize)
        return

    if placement_hint == 'line_aligned_text_box':
        box = rect_from_any(target_rect)
        if box is None:
            box = fitz.Rect(
                label_rect.x0,
                label_rect.y1 + 4,
                page.rect.x1 - 36,
                min(page.rect.y1 - 36, label_rect.y1 + 96),
            )
        inserted = page.insert_textbox(box, new_text, fontsize=fontsize, color=(0, 0, 0), align=fitz.TEXT_ALIGN_LEFT)
        if inserted < 0:
            raise RuntimeError(f'Could not fit multiline text for box {box}')
        return

    point = (label_rect.x1 + 6, label_rect.y1 - 1)
    insert_from_point(page, point, new_text, fontsize=fontsize)

def resolved_update_text(row, packet):
    text = str(row.get('new_text', '')).strip()
    if text:
        return text
    field_name = str(row.get('field_name', '')).strip()
    if field_name.startswith('signature'):
        return str(packet['signature_text']).strip()
    if field_name == 'today_date':
        return str(packet['today_date_text']).strip()
    return ''

def locate_student_id_from_label(page, label_rect):
    candidates = []
    for word in page.get_text('words'):
        x0, y0, x1, y1, text = word[:5]
        text = str(text).strip()
        if not STUDENT_ID_RE.fullmatch(text):
            continue
        if x0 >= label_rect.x0 and abs(y0 - label_rect.y0) <= 24:
            candidates.append((fitz.Rect(x0, y0, x1, y1), text))
    if candidates:
        return candidates[0]
    page_text = page.get_text()
    match = STUDENT_ID_RE.search(page_text)
    if match:
        rects = page.search_for(match.group(0))
        if rects:
            return rects[0], match.group(0)
    return None, None

def apply_update(doc, row, packet, counters):
    new_text = resolved_update_text(row, packet)
    if not new_text:
        raise RuntimeError(f'approved_pdf_updates row missing new_text: {row}')

    fontsize = row.get('fontsize', 11)
    op = str(row.get('operation', '')).strip()
    search_text = str(row.get('search_text', '')).strip()
    label_text = str(row.get('label_text', '')).strip()
    placement_hint = str(row.get('placement_hint', '')).strip() or 'right_of_label'

    target_rect = rect_from_any(row.get('target_rect'))
    insert_point = point_from_any(row.get('insert_point'))

    if insert_point is not None:
        page_index = row.get('page_index', 0)
        if not isinstance(page_index, int) or not (0 <= page_index < len(doc)):
            raise RuntimeError(f'invalid page_index for insert_point row: {row}')
        page = doc[page_index]
        insert_from_point(page, insert_point, new_text, fontsize=fontsize)
        return {'field_name': row.get('field_name', ''), 'applied_by': 'insert_point', 'expected_text': new_text}

    if op == 'replace_in_place':
        if target_rect is not None:
            page_index = row.get('page_index', 0)
            if not isinstance(page_index, int) or not (0 <= page_index < len(doc)):
                raise RuntimeError(f'invalid page_index for target_rect row: {row}')
            page = doc[page_index]
            replace_at_rect(page, target_rect, new_text, fontsize=fontsize)
            return {'field_name': row.get('field_name', ''), 'applied_by': 'target_rect', 'expected_text': new_text}
        if not search_text:
            raise RuntimeError(f'replace_in_place row missing search_text: {row}')
        matches = collect_search_matches(doc, search_text, row)
        chosen = choose_match(matches, ('search', search_text), counters, row.get('match_index'))
        if chosen is None:
            raise RuntimeError(f'Could not find search_text={search_text!r}')
        _, page, rect = chosen
        replace_at_rect(page, rect, new_text, fontsize=fontsize)
        return {
            'field_name': row.get('field_name', ''),
            'applied_by': 'search_text',
            'expected_text': new_text,
            'matched_text': search_text,
        }

    if op != 'fill_from_label':
        raise RuntimeError(f'Unexpected operation: {op}')
    if not label_text:
        raise RuntimeError(f'fill_from_label row missing label_text: {row}')

    matches = collect_label_matches(doc, label_text, row)
    chosen = choose_match(matches, ('label', label_text), counters, row.get('match_index'))
    if chosen is None:
        raise RuntimeError(f'Could not find label_text={label_text!r}')
    _, page, label_rect = chosen
    insert_from_label(
        page,
        label_rect,
        new_text,
        placement_hint=placement_hint,
        fontsize=fontsize,
        label_offset=row.get('label_offset'),
        target_rect=row.get('target_rect'),
    )
    return {
        'field_name': row.get('field_name', ''),
        'applied_by': 'label_text',
        'expected_text': new_text,
        'matched_text': label_text,
    }

def apply_redaction(doc, row, counters):
    masked_text = str(row.get('masked_text', '')).strip()
    if not masked_text:
        raise RuntimeError(f'approved_redactions row missing masked_text: {row}')

    redaction_mode = str(row.get('redaction_mode', '')).strip()
    if redaction_mode != 'true_redaction_white_fill':
        raise RuntimeError(f'Unexpected redaction_mode: {redaction_mode}')

    fontsize = row.get('fontsize', 11)
    search_text = str(row.get('search_text', '')).strip()
    label_text = str(row.get('label_text', '')).strip()

    actual_original = ''
    chosen_page = None
    chosen_rect = None

    if search_text:
        matches = collect_search_matches(doc, search_text, row)
        chosen = choose_match(matches, ('redaction-search', search_text), counters, row.get('match_index'))
        if chosen is not None:
            _, chosen_page, chosen_rect = chosen
            actual_original = search_text

    if chosen_page is None and label_text:
        matches = collect_label_matches(doc, label_text, row)
        chosen = choose_match(matches, ('redaction-label', label_text), counters, row.get('match_index'))
        if chosen is not None:
            _, chosen_page, label_rect = chosen
            chosen_rect, actual_original = locate_student_id_from_label(chosen_page, label_rect)

    if chosen_page is None or chosen_rect is None or not actual_original:
        raise RuntimeError(f'Could not locate packet-authorized redaction target: {row}')

    tighten_top = row.get('tighten_top', 8)
    tighten_bottom = row.get('tighten_bottom', 2)
    tight_rect = fitz.Rect(
        chosen_rect.x0,
        chosen_rect.y0 + tighten_top,
        chosen_rect.x1,
        chosen_rect.y1 - tighten_bottom,
    )
    chosen_page.add_redact_annot(tight_rect, fill=(1, 1, 1))
    chosen_page.apply_redactions()
    chosen_page.insert_text((chosen_rect.x0, chosen_rect.y1), masked_text, fontsize=fontsize, color=(0, 0, 0))

    return {
        'field_name': row.get('field_name', ''),
        'masked_text': masked_text,
        'original_text': actual_original,
    }

if not PACKET_PATH.exists():
    raise SystemExit(f'missing release packet: {PACKET_PATH}')

packet = json.loads(PACKET_PATH.read_text())

missing_keys = [key for key in REQUIRED_PACKET_KEYS if key not in packet]
if missing_keys:
    raise SystemExit(f'malformed release packet, missing keys: {missing_keys}')

for key, expected in EXPECTED_PACKET_VALUES.items():
    if packet.get(key) != expected:
        raise SystemExit(f'unexpected packet value for {key}: {packet.get(key)!r}')

update_rows = packet['approved_pdf_updates']
redaction_rows = packet['approved_redactions']
if not isinstance(update_rows, list) or not isinstance(redaction_rows, list):
    raise SystemExit('approved_pdf_updates and approved_redactions must be lists')

doc = fitz.open(SOURCE_PDF)
match_counters = defaultdict(int)
applied_updates = []
applied_redactions = []

for row in update_rows:
    applied_updates.append(apply_update(doc, row, packet, match_counters))

for row in redaction_rows:
    applied_redactions.append(apply_redaction(doc, row, match_counters))

OUTPUT_PDF.parent.mkdir(parents=True, exist_ok=True)
doc.save(OUTPUT_PDF)
doc.close()

saved = fitz.open(OUTPUT_PDF)
saved_text = '\n'.join(page.get_text() for page in saved)
saved_normalized = normalized(saved_text)
verification_checks = []

for result, row in zip(applied_updates, update_rows):
    field_name = result['field_name']
    expected_text = normalized(result['expected_text'])
    if row.get('multiline'):
        lines = [normalized(line) for line in str(result['expected_text']).splitlines() if normalized(line)]
        for line in lines:
            ok = line in saved_normalized
            verification_checks.append({'check': f'present:{field_name}:{line}', 'ok': ok})
            if not ok:
                raise RuntimeError(f'Expected multiline text not found: {line}')
    else:
        ok = expected_text in saved_normalized
        verification_checks.append({'check': f'present:{field_name}', 'expected': result['expected_text'], 'ok': ok})
        if not ok:
            raise RuntimeError(f'Expected text not found: {result[\'expected_text\']}')

for result in applied_redactions:
    field_name = result['field_name']
    masked_ok = normalized(result['masked_text']) in saved_normalized
    original_gone = normalized(result['original_text']) not in saved_normalized
    verification_checks.append({'check': f'masked_present:{field_name}', 'expected': result['masked_text'], 'ok': masked_ok})
    verification_checks.append({'check': f'original_absent:{field_name}', 'expected': result['original_text'], 'ok': original_gone})
    if not masked_ok or not original_gone:
        raise RuntimeError(f'Redaction verification failed for {field_name}')

for label in packet['label_protection_checks']:
    label_text = normalized(label)
    ok = label_text in saved_normalized
    verification_checks.append({'check': f'label_visible:{label}', 'ok': ok})
    if not ok:
        raise RuntimeError(f'Protected label missing after edit: {label}')

signature_rows = sum(1 for row in update_rows if str(row.get('field_name', '')).startswith('signature'))
if signature_rows:
    signature_count = saved_text.count(str(packet['signature_text']))
    ok = signature_count >= signature_rows
    verification_checks.append({'check': 'signature_count', 'expected_at_least': signature_rows, 'observed': signature_count, 'ok': ok})
    if not ok:
        raise RuntimeError('Signature count check failed')

date_rows = sum(1 for row in update_rows if str(row.get('field_name', '')) == 'today_date')
if date_rows:
    date_count = saved_text.count(str(packet['today_date_text']))
    ok = date_count >= date_rows
    verification_checks.append({'check': 'today_date_count', 'expected_at_least': date_rows, 'observed': date_count, 'ok': ok})
    if not ok:
        raise RuntimeError('Today date count check failed')

saved.close()

cleanup_actions = []
for target in [Path(packet['cleanup_target_path']), Path(packet['recovery_checkpoint_path'])]:
    if target.exists():
        target.unlink()
        action = 'deleted'
    else:
        action = 'already_absent'
    cleanup_actions.append({
        'path': str(target),
        'action': action,
        'adopted_from_packet': True,
    })

confirmation = {
    'workflow_stage': 'cleanup_finalizer',
    'consumed_release_packet_path': str(PACKET_PATH),
    'consumed_cleanup_target_path': packet['cleanup_target_path'],
    'consumed_cleanup_status': packet['cleanup_status'],
    'consumed_recovery_checkpoint_path': packet['recovery_checkpoint_path'],
    'consumed_recovery_checkpoint_status': packet['recovery_checkpoint_status'],
    'pre_delete_verification_passed': True,
    'final_output_pdf_path': str(OUTPUT_PDF),
    'native_source_cleanup_path': packet['cleanup_target_path'],
    'recovery_checkpoint_cleanup_path': packet['recovery_checkpoint_path'],
    'cleanup_actions': cleanup_actions,
    'verification_checks': verification_checks,
    'workflow_completion': 'insurance_waiver_pdf_cleanup_finalized',
}

CONFIRM_PATH.parent.mkdir(parents=True, exist_ok=True)
CONFIRM_PATH.write_text(json.dumps(confirmation, indent=2) + '\n')

print(str(OUTPUT_PDF))
print(str(CONFIRM_PATH))
print('workflow_stage=cleanup_finalizer')
print('consumed_cleanup_target_path=' + packet['cleanup_target_path'])
print('consumed_recovery_checkpoint_path=' + packet['recovery_checkpoint_path'])
print('pre_delete_verification_passed=true')
print('deleted_native_source=' + packet['cleanup_target_path'])
print('deleted_recovery_checkpoint=' + packet['recovery_checkpoint_path'])
PY
```

## Insurance Waiver PDF Cleanup Finalizer Stop Conditions
Stop without deletion if any of the following is true:
- `/root/output/insurance-waiver-workflow/pdf_release_packet.json` is missing or malformed
- any required packet key is missing
- any packet validation value is different from the approved release-packet contract
- any packet-authorized update or redaction cannot be applied
- any required saved-PDF verification check fails
- `pre_delete_verification_passed` would remain `false`

If the release packet is present and valid, do not recover by reopening `/root/input/input.txt` or `/root/output/insurance-waiver-workflow/parsed_instruction_checkpoint.json`. Repair the packet or the packet application, then rerun this finalizer.

## Insurance Waiver PDF Cleanup Finalizer Completion Markers
Surface these exact markers in command output or workflow notes:
- `/root/output/output.pdf`
- `/root/output/insurance-waiver-workflow/deletion_confirmation.json`
- `workflow_stage=cleanup_finalizer`
- `consumed_cleanup_target_path=/root/input/input.txt`
- `consumed_recovery_checkpoint_path=/root/output/insurance-waiver-workflow/parsed_instruction_checkpoint.json`
- `pre_delete_verification_passed=true`
- `deleted_native_source=/root/input/input.txt`
- `deleted_recovery_checkpoint=/root/output/insurance-waiver-workflow/parsed_instruction_checkpoint.json`
