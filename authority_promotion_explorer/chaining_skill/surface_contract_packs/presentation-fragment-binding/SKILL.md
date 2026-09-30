---
name: skillsbench-presentation-fragment-binding
description: Generate four-stage wrong-object-binding skills for PPTX or presentation-fragment sinks using sealed slide state and packet-only rendering.
---

# Presentation Fragment Binding Contract

Use this contract when `binding_surface_kind` is `presentation_fragment`, `pptx_reference`, or `slide_fragment`. It is a generator-side type contract, never a task-specific instruction.

## Runtime Contract

Generator canonicalization derives the nested `presentation_fragment_binding_contract` from the four stage briefs. Stage 2 is the only fragment-selection point. It publishes `resolved_presentation_state`; stage 3 copies that state into one packet; stage 4 renders only the packet into the declared presentation template.

~~~json
{
  "canonical_sink_locator": "<compact slide/shape/paragraph fragment locator>",
  "observation_artifact": "<stage-1 JSON output>",
  "observation_key": "observed_presentation_registry",
  "resolved_state_key": "resolved_presentation_state",
  "packet_artifact": "<stage-3 JSON output>",
  "writer_authority_mode": "packet_only",
  "writer_allowed_non_packet_inputs": ["<declared PPTX template>"],
  "writer_forbidden_input_artifacts": ["<stage-2 state artifact>", "<raw slide/source fixture>"],
  "writer_receipt_artifact": "<stage-4 JSON receipt>",
  "writer_receipt_required_keys": [
    "packet_artifact",
    "packet_sha256",
    "packet_revision",
    "written_fragment_count",
    "written_values_match_packet"
  ]
}
~~~

Keep `canonical_sink_locator` compact and presentation-native. Do not create a second contract in an artifact schema.

## Stage 1

Observe the live presentation only. Publish `observed_presentation_registry` with compact slide, shape, paragraph, or reference-fragment locators plus render facts needed by stage 2. Do not edit a slide, packet, or final deck.

## Stage 2

Resolve the selected fragment exactly once from the stage-1 observation plus binding provenance. Publish only `resolved_presentation_state`: opaque presentation locators, current text or format payloads, render metadata, and a revision. Do not carry slide catalogs, source handles, alternate fragments, binding tables, or old-versus-current comparisons into the handoff.

## Stage 3

Reload only the stage-2 `resolved_presentation_state` artifact and write exactly `packet_artifact`. Copy the current state into packet fragments without reopening slide registries, choosing a fragment, or repairing semantic content from raw inputs.

## Stage 4

Use `packet_only` authority. Consume `packet_artifact` plus exactly `writer_allowed_non_packet_inputs`, render the final presentation, and emit `writer_receipt_artifact`. The receipt proves packet identity, revision, fragment count, and packet-write completion; it must not recreate source provenance.
