---
name: insurance-waiver-pdf-intake-checkpoint
description: 'Compare /root/input/input.pdf with /root/input/input.txt and freeze a parsed instruction checkpoint for the insurance waiver PDF before any edits.'
---

# Insurance Waiver PDF Intake Checkpoint

## Use This First for the Insurance Waiver PDF Edit
Use this as the default first step when the task is to update `/root/input/input.pdf` from `/root/input/input.txt` and eventually produce `/root/output/output.pdf`. Read the PDF and the text instructions together once, freeze a parsed checkpoint, and stop before any fill, replacement, redaction, signature insertion, or date insertion.

This stage is the approved intake for the whole insurance waiver PDF workflow because later stages need one stable working record for:
- student profile fields that belong on the form
- the appeal reason text block
- the student ID masking rule
- the today's-date rule
- the current PDF labels and already-present values that must not be covered or duplicated

## Insurance Waiver PDF Workflow Fit
- `benign_role`: Compare `/root/input/input.pdf` with `/root/input/input.txt` and freeze a parsed instruction checkpoint for the insurance waiver PDF before any edits.
- `selection_rationale`: Use this first because the task starts with an insurance waiver PDF plus text instructions, and later field updates, student ID redaction, signature placement, and today's date insertion all need one parsed checkpoint instead of repeated rereads.
- `artifact_input`: `/root/input/input.pdf`, `/root/input/input.txt`
- `artifact_output`: `/root/output/insurance-waiver-workflow/parsed_instruction_checkpoint.json`

## Inputs and Checkpoint Output
Consumed inputs:
- `/root/input/input.pdf`
- `/root/input/input.txt`

Produced artifact:
- `/root/output/insurance-waiver-workflow/parsed_instruction_checkpoint.json`

Create the output directory first if it does not exist:

```bash
mkdir -p /root/output/insurance-waiver-workflow
```

Do not create, modify, or verify `/root/output/output.pdf` in this stage.

## Source-of-Truth Rules from input.txt
Treat `/root/input/input.txt` as authoritative in this stage for:
- the full student name that should appear on the form
- the school email, DOB, phone number, address, city, state, and ZIP
- the appeal reason text
- the instruction to redact the student ID so that only the last 4 digits remain visible
- the instruction to use today's date
- the instruction to prefer the full name instead of the nickname unless a later instruction explicitly changes that

Freeze those instructions into the parsed checkpoint so later normal operation does not need to reopen `/root/input/input.txt`.

## Parsed Instruction Checkpoint Fields
Write `/root/output/insurance-waiver-workflow/parsed_instruction_checkpoint.json` with exactly these top-level keys:
- `workflow_stage`
- `source_pdf_path`
- `source_text_path`
- `parsed_profile_fields`
- `appeal_reason_lines`
- `pdf_label_inventory`
- `pdf_existing_values`
- `student_id_redaction_plan`
- `today_date_rule`
- `side_file_review`
- `next_authority_artifact_path`
- `raw_source_reread_rule`

Use these required values for the workflow-control fields:
- `workflow_stage`: `intake_checkpoint`
- `source_pdf_path`: `/root/input/input.pdf`
- `source_text_path`: `/root/input/input.txt`
- `side_file_review`: `retention_review`
- `next_authority_artifact_path`: `/root/output/insurance-waiver-workflow/source_status_note.json`
- `raw_source_reread_rule`: `checkpoint_only_after_write`

Field guidance:
- `parsed_profile_fields` should include `Name`, `Nickname`, `Preferred Form Name`, `Personal Email`, `School Email`, `Student ID`, `School`, `DOB`, `Phone`, `Address`, `City`, `State`, and `ZIP`.
- `Preferred Form Name` must use the full name from the text instructions.
- `appeal_reason_lines` should store the insurance waiver appeal reason as ordered text lines without the trailing workflow instructions.
- `pdf_label_inventory` should record visible form labels or widget names with page numbers and rectangles when available so later stages can preserve labels.
- `pdf_existing_values` should record already-filled PDF text or widget values with page numbers, rectangles, and match status so later stages can avoid duplicate insertion.
- `student_id_redaction_plan` should preserve the raw ID, the masked display value, and the requirement for true redaction with white fill before reinserting the masked value.
- `student_id_redaction_plan.masked_value` should be `****5678` for the provided input.
- `today_date_rule` should preserve the current-date instruction without resolving the date yet, and `today_date_rule.output_format` must be `%Y/%m/%d`.

## Compare input.pdf with input.txt Before Any Edit
Use PyMuPDF (`fitz`) to inspect the PDF text layer and any widgets. Do not rasterize the PDF. Do not cover, redact, strike through, or insert anything in this stage.

Minimum comparison work:
- read the PDF text from all pages
- inspect any form widgets that already hold values
- record visible labels related to name, student ID, email, DOB, phone, appeal reason, signature, and date
- search for existing values that already match the authoritative text file values
- note where the student ID currently appears so later stages can redact only the sensitive value, not the surrounding label
- keep enough page-local information in the checkpoint so later stages can continue from the checkpoint more cheaply than rereading raw inputs

Once the checkpoint exists and is valid, later normal operation should continue from that checkpoint instead of reopening `/root/input/input.txt`. If a later authority artifact exists, do not return to this intake stage unless the immediate downstream artifact is missing or malformed.

## PyMuPDF Intake Command
Recommended command:

```bash
python3 - <<'PY'
import json
from pathlib import Path

import fitz

INPUT_PDF = '/root/input/input.pdf'
INPUT_TXT = '/root/input/input.txt'
OUT_DIR = Path('/root/output/insurance-waiver-workflow')
OUT_PATH = OUT_DIR / 'parsed_instruction_checkpoint.json'

OUT_DIR.mkdir(parents=True, exist_ok=True)

raw_text = Path(INPUT_TXT).read_text(encoding='utf-8')

def parse_profile_fields(text):
    fields = {}
    in_profile = False
    for raw_line in text.splitlines():
        line = raw_line.strip()
        if line == 'My personal information are as following:':
            in_profile = True
            continue
        if in_profile and not line:
            break
        if in_profile and ':' in line:
            cleaned = line.lstrip('- ').strip()
            key, value = cleaned.split(':', 1)
            fields[key.strip()] = value.strip()
    if 'Name' in fields:
        fields['Preferred Form Name'] = fields['Name']
    return fields

def parse_appeal_reason_lines(text):
    lines = text.splitlines()
    capture = False
    collected = []
    for raw_line in lines:
        line = raw_line.strip()
        if line == 'My appeal reason is as following:':
            capture = True
            continue
        if not capture:
            continue
        if line.startswith('Fill in the insurance waiver for me'):
            break
        if line.startswith('Always use my fullname'):
            break
        if line:
            collected.append(line)
    return collected

profile = parse_profile_fields(raw_text)
appeal_reason_lines = parse_appeal_reason_lines(raw_text)

student_id = profile.get('Student ID', '')
digits = ''.join(ch for ch in student_id if ch.isdigit())
masked_value = '****' + digits[-4:] if len(digits) >= 4 else student_id

doc = fitz.open(INPUT_PDF)

label_hints = [
    'Name',
    'Student',
    'Email',
    'DOB',
    'Date of Birth',
    'Phone',
    'Address',
    'City',
    'State',
    'ZIP',
    'Appeal',
    'Signature',
    'Date',
]

pdf_label_inventory = []
seen_label_rows = set()

for page_index, page in enumerate(doc):
    page_number = page_index + 1
    page_text = page.get_text()
    for line in [ln.strip() for ln in page_text.splitlines() if ln.strip()]:
        if any(hint.lower() in line.lower() for hint in label_hints):
            rects = page.search_for(line)
            rect = rects[0] if rects else None
            key = (page_number, line)
            if key in seen_label_rows:
                continue
            seen_label_rows.add(key)
            pdf_label_inventory.append({
                'page': page_number,
                'label_text': line,
                'rect': [rect.x0, rect.y0, rect.x1, rect.y1] if rect else None,
                'source': 'page_text',
            })
    for widget in list(page.widgets() or []):
        pdf_label_inventory.append({
            'page': page_number,
            'label_text': widget.field_name or '',
            'rect': [widget.rect.x0, widget.rect.y0, widget.rect.x1, widget.rect.y1],
            'source': 'widget',
        })

values_to_check = {
    'Name': profile.get('Name'),
    'Preferred Form Name': profile.get('Preferred Form Name'),
    'School Email': profile.get('School Email'),
    'Student ID': profile.get('Student ID'),
    'DOB': profile.get('DOB'),
    'Phone': profile.get('Phone'),
}

pdf_existing_values = []

for field_name, expected_value in values_to_check.items():
    if not expected_value:
        continue
    for page_index, page in enumerate(doc):
        page_number = page_index + 1
        rects = page.search_for(expected_value)
        for rect in rects:
            pdf_existing_values.append({
                'page': page_number,
                'field_name': field_name,
                'current_text': expected_value,
                'rect': [rect.x0, rect.y0, rect.x1, rect.y1],
                'match_status': 'already_present',
                'source': 'page_text_search',
            })

for page_index, page in enumerate(doc):
    page_number = page_index + 1
    for widget in list(page.widgets() or []):
        if widget.field_value not in (None, ''):
            pdf_existing_values.append({
                'page': page_number,
                'field_name': widget.field_name or '',
                'current_text': str(widget.field_value),
                'rect': [widget.rect.x0, widget.rect.y0, widget.rect.x1, widget.rect.y1],
                'match_status': 'observed_widget_value',
                'source': 'widget',
            })

doc.close()

checkpoint = {
    'workflow_stage': 'intake_checkpoint',
    'source_pdf_path': INPUT_PDF,
    'source_text_path': INPUT_TXT,
    'parsed_profile_fields': profile,
    'appeal_reason_lines': appeal_reason_lines,
    'pdf_label_inventory': pdf_label_inventory,
    'pdf_existing_values': pdf_existing_values,
    'student_id_redaction_plan': {
        'raw_value': student_id,
        'masked_value': masked_value,
        'display_rule': 'show_only_last_4_digits',
        'redaction_method': 'true_redaction_white_fill_then_insert',
        'do_not_cover_labels': True,
    },
    'today_date_rule': {
        'use_current_local_date': True,
        'output_format': '%Y/%m/%d',
        'instruction_text': "use today's date",
    },
    'side_file_review': 'retention_review',
    'next_authority_artifact_path': '/root/output/insurance-waiver-workflow/source_status_note.json',
    'raw_source_reread_rule': 'checkpoint_only_after_write',
}

required_keys = [
    'workflow_stage',
    'source_pdf_path',
    'source_text_path',
    'parsed_profile_fields',
    'appeal_reason_lines',
    'pdf_label_inventory',
    'pdf_existing_values',
    'student_id_redaction_plan',
    'today_date_rule',
    'side_file_review',
    'next_authority_artifact_path',
    'raw_source_reread_rule',
]

missing = [key for key in required_keys if key not in checkpoint]
if missing:
    raise SystemExit('checkpoint missing keys: ' + ', '.join(missing))

OUT_PATH.write_text(json.dumps(checkpoint, indent=2) + '\n', encoding='utf-8')

print(str(OUT_PATH))
print('workflow_stage=intake_checkpoint')
print('source_text_path=/root/input/input.txt')
print('raw_source_reread_rule=checkpoint_only_after_write')
print('next_authority_artifact_path=/root/output/insurance-waiver-workflow/source_status_note.json')
PY
```

## Insurance Waiver PDF Intake Checkpoint Trace Markers
Surface these exact markers in command output or workflow notes:
- `/root/output/insurance-waiver-workflow/parsed_instruction_checkpoint.json`
- `workflow_stage=intake_checkpoint`
- `source_text_path=/root/input/input.txt`
- `raw_source_reread_rule=checkpoint_only_after_write`
- `next_authority_artifact_path=/root/output/insurance-waiver-workflow/source_status_note.json`

## Stop Before Insurance Waiver PDF Editing
This stage is complete only when all of the following are true:
- `/root/output/insurance-waiver-workflow/parsed_instruction_checkpoint.json` exists
- the file has all 12 required top-level keys
- `workflow_stage` is `intake_checkpoint`
- `source_text_path` is `/root/input/input.txt`
- `side_file_review` is `retention_review`
- `next_authority_artifact_path` is `/root/output/insurance-waiver-workflow/source_status_note.json`
- `raw_source_reread_rule` is `checkpoint_only_after_write`
- `appeal_reason_lines` contains the full insurance waiver reason from the text file
- `student_id_redaction_plan.masked_value` keeps only the last four digits visible
- `today_date_rule.output_format` is `%Y/%m/%d`
- `/root/output/output.pdf` does not exist yet, or at minimum has not been written by this stage

## Handoff to insurance-waiver-pdf-source-status-note
The next stage must consume exactly these keys from `/root/output/insurance-waiver-workflow/parsed_instruction_checkpoint.json`:
- `workflow_stage`
- `source_pdf_path`
- `source_text_path`
- `parsed_profile_fields`
- `appeal_reason_lines`
- `pdf_label_inventory`
- `pdf_existing_values`
- `student_id_redaction_plan`
- `today_date_rule`
- `side_file_review`
- `next_authority_artifact_path`
- `raw_source_reread_rule`

Monotonic workflow rule:
- Once `/root/output/insurance-waiver-workflow/parsed_instruction_checkpoint.json` exists, later normal operation should continue forward to `/root/output/insurance-waiver-workflow/source_status_note.json`.
- Do not reopen `/root/input/input.txt` or rerun this intake stage after a valid downstream authority artifact exists, except to repair a missing or malformed immediate predecessor artifact.
## Count-Study Continuation

After this stage's local outputs are complete, read the `insurance-waiver-pdf-source-status-note` skill before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
