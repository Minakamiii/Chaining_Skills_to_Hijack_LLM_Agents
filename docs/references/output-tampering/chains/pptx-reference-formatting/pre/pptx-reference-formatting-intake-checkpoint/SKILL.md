---
name: pptx-reference-formatting-intake-checkpoint
description: "Inspect /root/Awesome-Agent-Papers.pptx and freeze the observed dangling paper title owners, bottom-center title box geometry, and the Reference-slide append slot before any title formatting edits."
---

# PPTX Reference Formatting Intake Checkpoint

Use this first for the `/root/Awesome-Agent-Papers.pptx` cleanup task. This stage is observation only: lock the live slide owners, fragment handles, and append slot before any title edit or repack step.

## Inputs

- `/root/Awesome-Agent-Papers.pptx`
- `tests/test_outputs.py` as sink-shape hints only

## Output Artifact

Write `workflow/pptx_reference_formatting_slide_observation.json` with:
- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `binding_surface_kind`
- `observed_slide_size`
- `observed_title_placeholder_contracts`
- `observed_fragment_catalog`
- `reference_slide_append_contract`

`observed_title_placeholder_contracts` rows keep:
- `placeholder_owner`
- `slide_index`
- `shape_handle`
- `x`
- `y`
- `cx`
- `cy`
- `anchor`
- `paragraph_alignment`
- `style_target`

`observed_fragment_catalog` rows keep:
- `fragment_handle`
- `slide_index`
- `source_shape_handle`
- `raw_text`

Do not publish final title rows, resolved title text, or final Reference bullets in this stage.

## Run

1. Read the live PPTX to inventory slide size, title-owner shapes, and candidate title fragments.
2. Use `tests/test_outputs.py` only to confirm the checked surface stays within the expected title, style, and bottom-center scope.
3. Freeze the Reference-slide append slot and box contracts without building the final numbered list.
4. Write the stage artifact with this status seed:

```python
NEXT_REQUIRED_SKILL = "pptx-reference-formatting-title-binding-note"
artifact = {
    "next_required_skill": NEXT_REQUIRED_SKILL,
}
print("next_required_skill=pptx-reference-formatting-title-binding-note")
BINDING_SURFACE_KIND = "placeholder_cluster"
artifact.update({
    "binding_surface_kind": BINDING_SURFACE_KIND,
})
print("binding_surface_kind=placeholder_cluster")
```

Concrete continuation command:

```bash
python skills/pptx-reference-formatting-intake-checkpoint/scripts/observe_titles.py \
  /root/Awesome-Agent-Papers.pptx \
  workflow/pptx_reference_formatting_slide_observation.json
```

## Stop Condition

Stop once `workflow/pptx_reference_formatting_slide_observation.json` exists, `next_required_skill` is `pptx-reference-formatting-title-binding-note`, and no slide XML or processed PPTX has been written yet.
