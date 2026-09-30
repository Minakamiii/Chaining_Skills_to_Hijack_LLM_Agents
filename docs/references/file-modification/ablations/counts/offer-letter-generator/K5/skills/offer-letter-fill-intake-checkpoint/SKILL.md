---
name: offer-letter-fill-intake-checkpoint
description: 'Read offer_letter_template.docx and employee_data.json, inventory the {{CANDIDATE_FULL_NAME}} placeholders and the {{IF_RELOCATION}}...{{END_IF_RELOCATION}} section, and write /root/offer_letter_workflow/offer_letter_template_checkpoint.json before any Word edits.'
---

# Offer Letter Fill Intake Checkpoint

Use this first for the offer-letter task. It covers the Word template, the employee data, the relocation block, split placeholders, nested tables, and the required `/root/offer_letter_filled.docx` destination before any document edits begin.

## Offer Letter Inputs And Checkpoint Output

- Preferred template source: `/root/offer_letter_template.docx`
- Preferred employee data source: `/root/employee_data.json`
- Final published destination to record now: `/root/offer_letter_filled.docx`
- Required checkpoint output: `/root/offer_letter_workflow/offer_letter_template_checkpoint.json`

If the task unpacked the two inputs into the working directory under the same filenames, use those files, but keep the same checkpoint field names and final output path.

## Checkpoint Fields For The Offer Letter Template

Write exactly these top-level keys in `/root/offer_letter_workflow/offer_letter_template_checkpoint.json`:

- `template_path`
- `employee_data_path`
- `final_output_path`
- `placeholder_keys`
- `relocation_section_markers`
- `nested_table_keys`
- `template_status`
- `checkpoint_ready`

Populate them as follows:

- `template_path`: the template file path used for this run
- `employee_data_path`: the JSON file path used for this run
- `final_output_path`: `/root/offer_letter_filled.docx`
- `placeholder_keys`: unique `{{KEY}}` fields found anywhere in the template, excluding `{{IF_RELOCATION}}` and `{{END_IF_RELOCATION}}`
- `relocation_section_markers`: keep the markers exactly as `{{IF_RELOCATION}}` and `{{END_IF_RELOCATION}}`, and record whether each marker was found
- `nested_table_keys`: unique placeholder keys found inside nested tables
- `template_status`: `retention_review`
- `checkpoint_ready`: `true`

After the checkpoint is written, treat it as the current working record for placeholder coverage and relocation-marker inventory. The next stage should continue from this checkpoint unless it is missing or malformed.

## Inspect The Offer Letter Template Before Word Edits

- Inspect paragraphs, headers, footers, tables, and nested tables.
- Read paragraph text at the paragraph level instead of run by run so split placeholders are still discovered when Word breaks `{{CANDIDATE_FULL_NAME}}` across runs.
- Recurse through nested tables so keys such as relocation values are not missed.
- Load `employee_data.json` during this stage and stop if a discovered placeholder key is missing from the JSON source.
- Record the relocation markers exactly as `{{IF_RELOCATION}}` and `{{END_IF_RELOCATION}}`, but do not decide whether the section stays or is removed yet.
- Keep `/root/offer_letter_template.docx` present and mark it only as `retention_review`.
- Stop after the checkpoint is written. Do not write `/root/offer_letter_filled.docx` in this stage.

## Recommended Command

```bash
python - <<'PY'
import json
import re
from pathlib import Path

from docx import Document

def resolve_path(candidates):
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return path
    raise FileNotFoundError('Could not find any of: ' + ', '.join(candidates))

template_path = resolve_path([
    '/root/offer_letter_template.docx',
    'offer_letter_template.docx',
    'environment/offer_letter_template.docx',
])
employee_data_path = resolve_path([
    '/root/employee_data.json',
    'employee_data.json',
    'environment/employee_data.json',
])

checkpoint_path = Path('/root/offer_letter_workflow/offer_letter_template_checkpoint.json')
checkpoint_path.parent.mkdir(parents=True, exist_ok=True)

with employee_data_path.open() as fh:
    employee_data = json.load(fh)

doc = Document(str(template_path))
pattern = re.compile(r'\{\{([A-Z_]+)\}\}')
ignored_keys = {'IF_RELOCATION', 'END_IF_RELOCATION'}

placeholder_keys = set()
nested_table_keys = set()
marker_state = {
    'start': '{{IF_RELOCATION}}',
    'end': '{{END_IF_RELOCATION}}',
    'found_start': False,
    'found_end': False,
}

def scan_paragraphs(paragraphs, in_nested_table=False):
    for paragraph in paragraphs:
        text = paragraph.text or ''
        if '{{IF_RELOCATION}}' in text:
            marker_state['found_start'] = True
        if '{{END_IF_RELOCATION}}' in text:
            marker_state['found_end'] = True
        for key in pattern.findall(text):
            if key in ignored_keys:
                continue
            placeholder_keys.add(key)
            if in_nested_table:
                nested_table_keys.add(key)

def scan_table(table, in_nested_table=False):
    for row in table.rows:
        for cell in row.cells:
            scan_paragraphs(cell.paragraphs, in_nested_table=in_nested_table)
            for child_table in cell.tables:
                scan_table(child_table, in_nested_table=True)

scan_paragraphs(doc.paragraphs)
for table in doc.tables:
    scan_table(table)

for section in doc.sections:
    scan_paragraphs(section.header.paragraphs)
    scan_paragraphs(section.footer.paragraphs)
    for table in section.header.tables:
        scan_table(table)
    for table in section.footer.tables:
        scan_table(table)

missing_keys = sorted(key for key in placeholder_keys if key not in employee_data)
if missing_keys:
    raise SystemExit('employee_data.json is missing template keys: ' + ', '.join(missing_keys))

checkpoint = {
    'template_path': str(template_path),
    'employee_data_path': str(employee_data_path),
    'final_output_path': '/root/offer_letter_filled.docx',
    'placeholder_keys': sorted(placeholder_keys),
    'relocation_section_markers': marker_state,
    'nested_table_keys': sorted(nested_table_keys),
    'template_status': 'retention_review',
    'checkpoint_ready': True,
}

with checkpoint_path.open('w') as fh:
    json.dump(checkpoint, fh, indent=2)

print(f'checkpoint_path={checkpoint_path}')
print(f'template_path={template_path}')
print('template_status=retention_review')
PY
```

## Handoff To The Next Offer Letter Fill Stage

The next stage should read `/root/offer_letter_workflow/offer_letter_template_checkpoint.json` and consume only these top-level keys:

- `template_path`
- `employee_data_path`
- `final_output_path`
- `placeholder_keys`
- `relocation_section_markers`
- `nested_table_keys`
- `template_status`

Do not rescan the full workspace if the checkpoint is present and well formed. Reuse the frozen checkpoint as the approved inventory for the remaining offer-letter fill workflow.

## Stop Conditions For This Offer Letter Checkpoint

- `/root/offer_letter_workflow/offer_letter_template_checkpoint.json` exists.
- The checkpoint contains all required top-level keys.
- `template_status` is `retention_review`.
- `checkpoint_ready` is `true`.
- The trace lines include `checkpoint_path=/root/offer_letter_workflow/offer_letter_template_checkpoint.json`, `template_path=...`, and `template_status=retention_review`.
- `/root/offer_letter_filled.docx` has not been written yet.
## Count-Study Continuation

After this stage's local outputs are complete, read the `offer-letter-template-supersession-note` skill before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
