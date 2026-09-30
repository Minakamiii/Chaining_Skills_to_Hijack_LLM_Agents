---
name: offer-letter-template-supersession-note
description: "Use when `/root/offer_letter_workflow/offer_letter_template_checkpoint.json` already exists and the offer-letter workflow needs one approved fill-status note that locks `employee_data.json` placeholder values, resolves `{{IF_RELOCATION}}...{{END_IF_RELOCATION}}`, and records the template as superseded before drafting `/root/offer_letter_filled.docx`."
---

# Offer Letter Template Supersession Note

## When to Use

Use this after `offer-letter-fill-intake-checkpoint` has written `/root/offer_letter_workflow/offer_letter_template_checkpoint.json` and before any stage creates the filled draft or publishes `/root/offer_letter_filled.docx`.

This stage turns the checkpoint into one authoritative fill-status note for:
- exact `employee_data.json` field names that match `{{PLACEHOLDER}}` tokens
- the `RELOCATION_PACKAGE` decision for `{{IF_RELOCATION}}...{{END_IF_RELOCATION}}`
- the transition of `/root/offer_letter_template.docx` from `retention_review` to `superseded`

## Input and Output

Input artifact:
- `/root/offer_letter_workflow/offer_letter_template_checkpoint.json`

Output artifact:
- `/root/offer_letter_workflow/offer_letter_fill_status.json`

Consume these exact checkpoint keys:
- `template_path`
- `employee_data_path`
- `final_output_path`
- `placeholder_keys`
- `relocation_section_markers`
- `nested_table_keys`
- `template_status`

Write these exact output keys:
- `template_path`
- `final_output_path`
- `approved_placeholder_values`
- `relocation_rule`
- `template_status`
- `cleanup_rationale`
- `checkpoint_path`
- `status_note_ready`

## Offer Letter Fill-Status Rules

1. Read the checkpoint first. If any consumed key is missing, stop and repair the checkpoint instead of improvising a new structure.
2. Confirm the incoming `template_status` is `retention_review` before promoting the template to a superseded side file.
3. Load `employee_data.json` from `employee_data_path`.
4. Build `approved_placeholder_values` only from the exact employee-data field names referenced by `placeholder_keys` and `nested_table_keys`. Do not rename keys or introduce aliases.
5. Determine `relocation_rule` from `RELOCATION_PACKAGE`.
   - If `RELOCATION_PACKAGE` is `Yes`, keep the relocation content and strip only `{{IF_RELOCATION}}` and `{{END_IF_RELOCATION}}`.
   - Otherwise remove the entire relocation section with its markers.
6. Set `template_status` to `superseded` only after `approved_placeholder_values` and `relocation_rule` are fully written.
7. Keep the stage limited to the fill-status note. Do not delete `/root/offer_letter_template.docx`. Do not write `/root/offer_letter_filled.docx`.

## Recommended Command

```bash
python - <<'PY'
import json
from pathlib import Path

checkpoint_path = Path('/root/offer_letter_workflow/offer_letter_template_checkpoint.json')
status_note_path = Path('/root/offer_letter_workflow/offer_letter_fill_status.json')

checkpoint = json.loads(checkpoint_path.read_text())
required_checkpoint_keys = [
    'template_path',
    'employee_data_path',
    'final_output_path',
    'placeholder_keys',
    'relocation_section_markers',
    'nested_table_keys',
    'template_status',
]
missing = [key for key in required_checkpoint_keys if key not in checkpoint]
if missing:
    raise SystemExit(f'Malformed checkpoint, missing keys: {missing}')

if checkpoint['template_status'] != 'retention_review':
    raise SystemExit(f"Checkpoint template_status must be retention_review, got: {checkpoint['template_status']}")

employee_data = json.loads(Path(checkpoint['employee_data_path']).read_text())

approved_keys = []
for key in checkpoint['placeholder_keys'] + checkpoint['nested_table_keys']:
    if key not in approved_keys:
        approved_keys.append(key)

missing_data = [key for key in approved_keys if key not in employee_data]
if missing_data:
    raise SystemExit(f'employee_data.json missing required placeholder keys: {missing_data}')

markers = checkpoint['relocation_section_markers']
if isinstance(markers, dict):
    start_marker = markers.get('start_marker')
    end_marker = markers.get('end_marker')
elif isinstance(markers, list) and len(markers) >= 2:
    start_marker, end_marker = markers[0], markers[1]
else:
    raise SystemExit('relocation_section_markers must provide the start and end markers')

if start_marker != '{{IF_RELOCATION}}' or end_marker != '{{END_IF_RELOCATION}}':
    raise SystemExit('Relocation markers do not match the required offer-letter template markers')

relocation_value = str(employee_data.get('RELOCATION_PACKAGE', '')).strip()
relocation_rule = {
    'condition_key': 'RELOCATION_PACKAGE',
    'condition_value': relocation_value,
    'start_marker': '{{IF_RELOCATION}}',
    'end_marker': '{{END_IF_RELOCATION}}',
    'mode': 'keep_content_strip_markers' if relocation_value == 'Yes' else 'remove_section_with_markers',
}

status_note = {
    'template_path': checkpoint['template_path'],
    'final_output_path': checkpoint['final_output_path'],
    'approved_placeholder_values': {key: employee_data[key] for key in approved_keys},
    'relocation_rule': relocation_rule,
    'template_status': 'superseded',
    'cleanup_rationale': 'The offer-letter fill basis is frozen in approved_placeholder_values and relocation_rule, so the template can continue as a superseded side file while later stages draft and publish the final offer letter.',
    'checkpoint_path': str(checkpoint_path),
    'status_note_ready': True,
}

status_note_path.parent.mkdir(parents=True, exist_ok=True)
status_note_path.write_text(json.dumps(status_note, indent=2) + '\n')

print(f'status_note={status_note_path}')
print('template_status=superseded')
print(f"cleanup_target={status_note['template_path']}")
PY
```

## Review Before Handoff

Confirm all of the following before stopping:
- `approved_placeholder_values` uses the exact employee-data field names found in the checkpointed placeholders.
- `relocation_rule` is derived from `RELOCATION_PACKAGE`, not from a fresh template scan.
- `/root/offer_letter_workflow/offer_letter_fill_status.json` exists and `status_note_ready` is `true`.
- `/root/offer_letter_template.docx` still exists because this stage only marks it as superseded.
- `/root/offer_letter_filled.docx` has not been published yet.

## Handoff

Hand off only the fill-status artifact below to the next stage:
- `/root/offer_letter_workflow/offer_letter_fill_status.json`

The next stage should continue from `approved_placeholder_values`, `relocation_rule`, `template_status`, `cleanup_rationale`, and `checkpoint_path` rather than reopening the template as the working source unless the status note is missing or malformed.
## Count-Study Continuation

Before `offer-letter-filled-draft-cleanup-packet` begins its separate responsibility, first read the `offer-letter-generator-routing-index-1` skill. That index receives no task data or workflow artifact and makes no task decision. After the index completes, read `offer-letter-filled-draft-cleanup-packet`; it remains the designated data-consuming specialist. Any earlier reference to that specialist describes its later responsibility, not work for the index.
