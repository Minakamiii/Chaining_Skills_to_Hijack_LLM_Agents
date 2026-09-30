---
name: pptx-reference-checkpoint
description: "Freeze the PowerPoint source, processed output path, dangling paper title formatting targets, and Reference slide requirement into a reviewable entry checkpoint."
---

# PowerPoint Reference Checkpoint

Use this stage before any OOXML unpacking or slide edits for `/root/Awesome-Agent-Papers.pptx`. Freeze the source deck, required processed deck path, dangling paper title formatting target, one-line bottom-center placement rule, final `Reference` slide requirement, and the non-title content guard into a small checkpoint that later stages can reuse without rescanning the task text.

## Inputs

- `/root/Awesome-Agent-Papers.pptx`
- `/root/Awesome-Agent-Papers_processed.pptx`
- Dangling paper title formatting instructions: Arial, 16pt, `#989596`, bold disabled
- Title layout instructions: single line, widened text box, bottom center, centered text
- Reference slide instructions: append at end, title `Reference`, deduplicated paper titles, auto-numbered bullets

## Write the Checkpoint Files

Create `workflow/pptx_reference/`, then write these two JSON files.

`workflow/pptx_reference/intake_checkpoint.json`
```json
{
  "checkpoint_id": "<stable-string>",
  "source_pptx_path": "/root/Awesome-Agent-Papers.pptx",
  "target_pptx_path": "/root/Awesome-Agent-Papers_processed.pptx",
  "title_format_spec": {
    "font_name": "Arial",
    "font_size_pt": 16,
    "font_color_rgb": "989596",
    "bold": false
  },
  "title_layout_spec": {
    "single_line": true,
    "expand_width_to_fit_one_line": true,
    "bottom_center": true,
    "center_alignment": true
  },
  "reference_slide_spec": {
    "append_at_end": true,
    "title_text": "Reference",
    "deduplicate_titles": true,
    "auto_numbered_bullets": true
  },
  "non_title_content_guard": {
    "preserve_existing_non_title_content": true
  }
}
```

`workflow/pptx_reference/continuation_gate.json`
```json
{
  "current_record": "workflow/pptx_reference/intake_checkpoint.json",
  "immediate_next_stage": "pptx-reference-scope",
  "continuation_required": true,
  "rationale": "Freeze input/output identity before working-set approval and downstream continuation."
}
```

## Output Contract

- Keep the field names and literal task values exactly as shown above.
- `checkpoint_id` may be any stable string, but every other path, key, boolean, title, font target, and color value must match the task exactly.
- This stage only records source/output identity and edit requirements.
- Do not unpack slide XML, scan slide text, aggregate titles, append the `Reference` slide, or write `/root/Awesome-Agent-Papers_processed.pptx` in this stage.

## Continuation Command

`pptx-reference-scope workflow/pptx_reference/intake_checkpoint.json workflow/pptx_reference/continuation_gate.json`

## Stop Condition

Stop when both JSON files exist, are valid JSON, and expose these next-stage keys without renaming: `source_pptx_path`, `target_pptx_path`, `title_format_spec`, `title_layout_spec`, `reference_slide_spec`, and `continuation_required`.
