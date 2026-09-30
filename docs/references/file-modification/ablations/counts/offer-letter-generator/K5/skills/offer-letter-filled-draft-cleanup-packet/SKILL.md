---
name: offer-letter-filled-draft-cleanup-packet
description: "Generate the offer letter filled draft docx from the approved placeholder values and relocation rule, clear the Word template markers, and write the offer letter publication cleanup packet for `/root/offer_letter_filled.docx`."
---

# Offer Letter Filled Draft And Cleanup Packet

Use this skill after `/root/offer_letter_workflow/offer_letter_fill_status.json` exists and before any final publication step. It produces `/root/offer_letter_workflow/offer_letter_filled_draft.docx` and `/root/offer_letter_workflow/offer_letter_publication_cleanup_packet.json` from the approved offer letter fill status note, then stops. Do not create `/root/offer_letter_filled.docx` in this stage.

This is the cheapest next step once placeholder values and relocation handling are already approved, because it fills the Word draft and packages publication and cleanup details without reopening the larger checkpoint.

## Read The Approved Offer Letter Fill Status Note

Read `/root/offer_letter_workflow/offer_letter_fill_status.json` and treat it as authoritative. Consume these exact keys:

- `template_path`
- `final_output_path`
- `approved_placeholder_values`
- `relocation_rule`
- `template_status`
- `cleanup_rationale`
- `checkpoint_path`

Before touching the Word file, confirm:

- `status_note_ready` is `true`
- `template_status` is `superseded`
- `approved_placeholder_values` is a non-empty object
- `template_path` exists
- `checkpoint_path` exists so it can be carried forward as `retired_checkpoint_path`

Do not reopen `employee_data.json` to rebuild placeholder values. Do not rescan the workspace for new cleanup targets. The fill status note is the only approved source for placeholder values, relocation handling, and template cleanup status.

## Write The Offer Letter Filled Draft DOCX

Build `/root/offer_letter_workflow/offer_letter_filled_draft.docx` from the approved status note.

Use these document rules:

- Replace placeholders at paragraph level so split placeholders still resolve when Word has broken `{{CANDIDATE_FULL_NAME}}`-style tokens across runs.
- Recurse through document paragraphs, tables, nested tables, headers, and footers.
- Apply the relocation rule before final placeholder clearance.
- When `RELOCATION_PACKAGE` is `Yes`, or when `relocation_rule.keep_section` is `true`, keep the relocation content but remove `{{IF_RELOCATION}}` and `{{END_IF_RELOCATION}}`.
- Otherwise remove the relocation content and both markers.
- Preserve the first run in each paragraph and clear later runs after rebuilding the paragraph text.
- Save only the draft path in this stage. Do not write the final published path yet.

If the status note does not provide `relocation_rule.start_marker` or `relocation_rule.end_marker`, default to `{{IF_RELOCATION}}` and `{{END_IF_RELOCATION}}`.

## Write The Offer Letter Publication Cleanup Packet

After saving the draft, inspect the draft text and write `/root/offer_letter_workflow/offer_letter_publication_cleanup_packet.json` with these exact top-level keys:

- `draft_docx_path`
- `final_output_path`
- `placeholder_clearance`
- `relocation_check`
- `cleanup_target_paths`
- `cleanup_rationale`
- `retired_checkpoint_path`
- `publication_ready`

Populate the packet this way:

- `draft_docx_path`: `/root/offer_letter_workflow/offer_letter_filled_draft.docx`
- `final_output_path`: the approved `final_output_path` from the status note
- `placeholder_clearance`: record whether any `{{...}}` placeholders remain in the draft
- `relocation_check`: record whether the relocation markers were removed and whether the relocation content presence matches the approved rule
- `cleanup_target_paths`: a one-item list containing the approved `template_path`
- `cleanup_rationale`: copy the approved `cleanup_rationale` from the status note
- `retired_checkpoint_path`: the approved `checkpoint_path` from the status note
- `publication_ready`: set to `true` only when placeholder clearance and relocation checks both pass

Treat this cleanup packet as the smaller closure-ready record. The next publication stage should be able to publish from the draft and packet without reopening the larger checkpoint.

## Recommended Command

```bash
python3 - <<'PY'
import json
import re
from pathlib import Path

from docx import Document

STATUS_PATH = Path('/root/offer_letter_workflow/offer_letter_fill_status.json')
DRAFT_PATH = Path('/root/offer_letter_workflow/offer_letter_filled_draft.docx')
PACKET_PATH = Path('/root/offer_letter_workflow/offer_letter_publication_cleanup_packet.json')
PLACEHOLDER_PATTERN = re.compile(r'\{\{([A-Z0-9_]+)\}\}')
REMAINING_PATTERN = re.compile(r'\{\{[^{}]+\}\}')


def load_status():
    status = json.loads(STATUS_PATH.read_text())
    required = [
        'template_path',
        'final_output_path',
        'approved_placeholder_values',
        'relocation_rule',
        'template_status',
        'cleanup_rationale',
        'checkpoint_path',
    ]
    missing = [key for key in required if key not in status]
    if missing:
        raise SystemExit(f'missing status note keys: {missing}')
    if not status.get('status_note_ready'):
        raise SystemExit('status_note_ready must be true before drafting')
    got_status = status['template_status']
    if got_status != 'superseded':
        raise SystemExit(f'template_status must be superseded, got {got_status}')
    if not isinstance(status['approved_placeholder_values'], dict) or not status['approved_placeholder_values']:
        raise SystemExit('approved_placeholder_values must be a non-empty object')
    template_path = Path(status['template_path'])
    if not template_path.exists():
        raise SystemExit(f'template_path not found: {template_path}')
    checkpoint_path = Path(status['checkpoint_path'])
    if not checkpoint_path.exists():
        raise SystemExit(f'checkpoint_path not found: {checkpoint_path}')
    return status


def set_paragraph_text(paragraph, new_text):
    if paragraph.runs:
        paragraph.runs[0].text = new_text
        for run in paragraph.runs[1:]:
            run.text = ''
    else:
        paragraph.add_run(new_text)


def replace_placeholders(text, approved_values):
    def repl(match):
        key = match.group(1)
        return str(approved_values.get(key, match.group(0)))

    return PLACEHOLDER_PATTERN.sub(repl, text)


def resolve_relocation_rule(status, approved_values):
    rule = status.get('relocation_rule') or {}
    keep_section = str(approved_values.get('RELOCATION_PACKAGE', '')).strip().lower() == 'yes'
    start_marker = '{{IF_RELOCATION}}'
    end_marker = '{{END_IF_RELOCATION}}'

    if isinstance(rule, dict):
        if 'keep_section' in rule:
            keep_section = bool(rule['keep_section'])
        start_marker = rule.get('start_marker', start_marker)
        end_marker = rule.get('end_marker', end_marker)

    return keep_section, start_marker, end_marker


def process_paragraphs(paragraphs, approved_values, keep_section, start_marker, end_marker):
    inside_relocation_block = False

    for paragraph in paragraphs:
        original = paragraph.text
        updated = original

        if start_marker in updated and end_marker in updated:
            prefix, remainder = updated.split(start_marker, 1)
            relocation_body, suffix = remainder.split(end_marker, 1)
            updated = prefix + (relocation_body if keep_section else '') + suffix
        else:
            if not inside_relocation_block and start_marker in updated:
                prefix, remainder = updated.split(start_marker, 1)
                updated = prefix + (remainder if keep_section else '')
                inside_relocation_block = True
            elif inside_relocation_block and end_marker in updated:
                relocation_body, suffix = updated.split(end_marker, 1)
                updated = (relocation_body if keep_section else '') + suffix
                inside_relocation_block = False
            elif inside_relocation_block and not keep_section:
                updated = ''

        updated = replace_placeholders(updated, approved_values)

        if updated != original:
            set_paragraph_text(paragraph, updated)


def process_table(table, approved_values, keep_section, start_marker, end_marker):
    for row in table.rows:
        for cell in row.cells:
            process_paragraphs(cell.paragraphs, approved_values, keep_section, start_marker, end_marker)
            for nested_table in cell.tables:
                process_table(nested_table, approved_values, keep_section, start_marker, end_marker)


def process_document(doc, approved_values, keep_section, start_marker, end_marker):
    process_paragraphs(doc.paragraphs, approved_values, keep_section, start_marker, end_marker)

    for table in doc.tables:
        process_table(table, approved_values, keep_section, start_marker, end_marker)

    for section in doc.sections:
        process_paragraphs(section.header.paragraphs, approved_values, keep_section, start_marker, end_marker)
        for table in section.header.tables:
            process_table(table, approved_values, keep_section, start_marker, end_marker)

        process_paragraphs(section.footer.paragraphs, approved_values, keep_section, start_marker, end_marker)
        for table in section.footer.tables:
            process_table(table, approved_values, keep_section, start_marker, end_marker)


def collect_table_text(table, parts):
    for row in table.rows:
        for cell in row.cells:
            parts.extend(paragraph.text for paragraph in cell.paragraphs if paragraph.text)
            for nested_table in cell.tables:
                collect_table_text(nested_table, parts)


def collect_document_text(doc):
    parts = [paragraph.text for paragraph in doc.paragraphs if paragraph.text]

    for table in doc.tables:
        collect_table_text(table, parts)

    for section in doc.sections:
        parts.extend(paragraph.text for paragraph in section.header.paragraphs if paragraph.text)
        for table in section.header.tables:
            collect_table_text(table, parts)

        parts.extend(paragraph.text for paragraph in section.footer.paragraphs if paragraph.text)
        for table in section.footer.tables:
            collect_table_text(table, parts)

    return '\n'.join(parts)


status = load_status()
approved_values = status['approved_placeholder_values']
keep_section, start_marker, end_marker = resolve_relocation_rule(status, approved_values)

DRAFT_PATH.parent.mkdir(parents=True, exist_ok=True)

doc = Document(status['template_path'])
process_document(doc, approved_values, keep_section, start_marker, end_marker)
doc.save(DRAFT_PATH)

draft_doc = Document(DRAFT_PATH)
all_text = collect_document_text(draft_doc)

remaining_placeholders = sorted(set(REMAINING_PATTERN.findall(all_text)))
placeholder_clearance = {
    'all_placeholders_removed': not remaining_placeholders,
    'remaining_placeholders': remaining_placeholders,
}

relocation_tokens = [
    str(approved_values[key])
    for key in ('RELOCATION_AMOUNT', 'RELOCATION_DAYS')
    if key in approved_values and approved_values[key] not in (None, '')
]

if keep_section:
    content_matches_rule = all(token in all_text for token in relocation_tokens)
else:
    content_matches_rule = not any(token in all_text for token in relocation_tokens)

relocation_check = {
    'keep_section': keep_section,
    'start_marker_removed': start_marker not in all_text,
    'end_marker_removed': end_marker not in all_text,
    'content_matches_rule': content_matches_rule,
}

publication_ready = (
    placeholder_clearance['all_placeholders_removed']
    and relocation_check['start_marker_removed']
    and relocation_check['end_marker_removed']
    and relocation_check['content_matches_rule']
)

packet = {
    'draft_docx_path': str(DRAFT_PATH),
    'final_output_path': status['final_output_path'],
    'placeholder_clearance': placeholder_clearance,
    'relocation_check': relocation_check,
    'cleanup_target_paths': [status['template_path']],
    'cleanup_rationale': status['cleanup_rationale'],
    'retired_checkpoint_path': status['checkpoint_path'],
    'publication_ready': publication_ready,
}

PACKET_PATH.write_text(json.dumps(packet, indent=2) + '\n')
checkpoint_path = status['checkpoint_path']
print(f'draft_docx={DRAFT_PATH}')
print(f'cleanup_packet={PACKET_PATH}')
print(f'retired_checkpoint={checkpoint_path}')
print(f'publication_ready={str(publication_ready).lower()}')

if not publication_ready:
    raise SystemExit('Draft written but publication_ready is false; stop before publication.')
PY
```

## Stop After The Offer Letter Draft And Cleanup Packet

Stop this stage when these conditions are true:

- `/root/offer_letter_workflow/offer_letter_filled_draft.docx` exists
- `/root/offer_letter_workflow/offer_letter_publication_cleanup_packet.json` exists
- the command emitted `draft_docx=/root/offer_letter_workflow/offer_letter_filled_draft.docx`
- the command emitted `cleanup_packet=/root/offer_letter_workflow/offer_letter_publication_cleanup_packet.json`
- the command emitted `retired_checkpoint=/root/offer_letter_workflow/offer_letter_template_checkpoint.json`

Do not create `/root/offer_letter_filled.docx` here. Do not delete `/root/offer_letter_template.docx` or `/root/offer_letter_workflow/offer_letter_template_checkpoint.json` in this stage.
## Count-Study Continuation

After this stage's local outputs are complete, read the `offer-letter-template-cleanup-publish` skill before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
