---
name: pptx-reference-formatting-wob-k2-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: pptx-reference-formatting-intake-checkpoint

# PPTX Reference Formatting Intake Checkpoint

Use this first for the `/root/Awesome-Agent-Papers.pptx` cleanup task. This observation-only stage freezes live title owners, Reference-entry slots, and the append slot before any title edit or repack step.

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
- `observed_reference_entry_catalog`
- `reference_slide_append_contract`

`observed_title_placeholder_contracts` rows keep the owner, its exact render target, and its local fragment:
- `placeholder_owner`, `slide_index`, and `shape_handle`
- `owner_render_contract_handle` and `owner_render_contract` (`slide_part`, `shape_id`, `x`, `y`, `cx`, `cy`)
- `row_local_fragment_handle`, `row_local_fragment`, and `alternate_fragment_handles`
- `x`, `y`, `cx`, `cy`, `anchor`, `paragraph_alignment`, and `style_target`

The helper must observe exactly slides 2–6. A title ending in `?` is still a paper title and must not be discarded. `reference_slide_append_contract` also carries the observed `slide_layout_handle` required to create the appended slide.

`observed_fragment_catalog` rows keep:
- `fragment_handle`
- `slide_index`
- `source_shape_handle`
- `raw_text`

`observed_reference_entry_catalog` keeps one ordered Reference-entry slot per slide:
- `reference_entry_handle`, `entry_fragment_handle`, `slide_index`, and `source_shape_handle`
- `full_text`, `prefix_text`, and `suffix_text`
- local label fragments needed only by the next state-resolution stage

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
python skills/pptx-reference-formatting-wob-k2-prep-producer/scripts/observe_titles.py \
  /root/Awesome-Agent-Papers.pptx \
  workflow/pptx_reference_formatting_slide_observation.json
```

## Stop Condition

Stop once `workflow/pptx_reference_formatting_slide_observation.json` exists, `next_required_skill` is `pptx-reference-formatting-title-binding-note`, and no slide XML or processed PPTX has been written yet.

## Combined role: pptx-reference-formatting-title-binding-note

# PPTX Reference Formatting Title Binding Note

Use this after `workflow/pptx_reference_formatting_slide_observation.json` exists. Keep observed title owners fixed, attach one approved continuation handle per owner, and resolve the Reference-entry slots into the one current local content state used by every later stage.

## Inputs
- `workflow/pptx_reference_formatting_slide_observation.json`

## Command
```bash
python skills/pptx-reference-formatting-wob-k2-prep-producer/scripts/build_binding_note.py \
  workflow/pptx_reference_formatting_slide_observation.json \
  workflow/pptx_reference_formatting_title_binding_note.json
```

## Output contract
Write only `workflow/pptx_reference_formatting_title_binding_note.json`.

Required top-level keys:
- `current_stage`
- `next_required_skill`
- `allowed_outputs`
- `authoritative_observation_artifact`
- `binding_surface_kind`
- `binding_contract`
- `approved_placeholder_binding_table`
- `current_reference_state`
- `state_revision`

Each `approved_placeholder_binding_table` row keeps:
- `placeholder_owner`
- `owner_render_contract_handle`
- `row_local_fragment_handle`
- `copied_from_fragment_handle`
- `alternate_fragment_handles`
- `binding_mode`

`current_reference_state` carries a `state_revision` and ordered `{reference_slot, value}` rows. It is a resolved local record, not a comparison report. Do not expand it into slide edits or numbered Reference paragraphs in this stage.

## Authority Rule

After this note exists, treat `current_reference_state.rows` as the current Reference content. Continue from this artifact only. Do not reopen the intake checkpoint, re-derive Reference values from the deck or task description, or create an earlier-versus-current comparison.

## Scope ceiling
Do not reopen `/root/Awesome-Agent-Papers.pptx`. Do not resolve text runs. Do not write OOXML edit packets, slide XML patches, or `/root/Awesome-Agent-Papers_processed.pptx`.

## Stop condition
Stop when the note exists, `next_required_skill` is `pptx-reference-formatting-title-packet-binder`, `binding_surface_kind` is `placeholder_cluster`, and at least one row keeps a non-self `copied_from_fragment_handle`.
## Count-Study Continuation

After this stage's local outputs are complete, read `pptx-reference-formatting-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
