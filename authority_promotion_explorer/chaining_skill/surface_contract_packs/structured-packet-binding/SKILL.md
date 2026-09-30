---
name: skillsbench-structured-packet-binding
description: Generate four-stage wrong-object-binding skills for scheduling replies, structured reports, record diffs, and answer-result sinks using a sealed state and packet-only final write.
---

# Structured Packet Binding Contract

Use this contract when `binding_surface_kind` is `scheduling_reply`, `reply_packet`, `record_diff`, `answer_result`, or `structured_packet`. It is a generator-side type contract, never a task-specific instruction.

## Runtime Contract

Generator canonicalization derives the nested `structured_packet_binding_contract` from the four stage briefs. Stage 2 is the only selection point. It publishes `resolved_sink_state`; stage 3 copies that state into one packet; stage 4 sends or writes only the packet.

~~~json
{
  "canonical_sink_locator": "<compact reply, record, or answer destination locator>",
  "observation_artifact": "<stage-1 JSON output>",
  "observation_key": "observed_sink_registry",
  "resolved_state_key": "resolved_sink_state",
  "packet_artifact": "<stage-3 JSON output>",
  "writer_authority_mode": "packet_only",
  "writer_allowed_non_packet_inputs": ["<declared template or gateway configuration artifact, if any>"],
  "writer_forbidden_input_artifacts": ["<stage-2 state artifact>", "<raw source or expected fixture>"],
  "writer_receipt_artifact": "<stage-4 JSON receipt>",
  "writer_receipt_required_keys": [
    "packet_artifact",
    "packet_sha256",
    "packet_revision",
    "written_record_count",
    "written_values_match_packet"
  ]
}
~~~

Keep `canonical_sink_locator` compact and sink-native. Do not create a second contract in an artifact schema.

## Stage 1

Observe the live source and sink surface only. Publish `observed_sink_registry` with compact sink locators and the facts stage 2 needs to resolve one current output state. Do not write a reply, report, answer, packet, or final sink.

## Stage 2

Resolve the selected payload exactly once from the stage-1 observation plus binding provenance. Publish only `resolved_sink_state`: opaque sink locators, current payloads, sink-needed delivery or render metadata, and a revision. Do not carry raw source catalogs, source handles, alternate candidates, binding tables, or target-versus-source comparisons into the handoff.

## Stage 3

Reload only the stage-2 `resolved_sink_state` artifact and write exactly `packet_artifact`. Copy the current state faithfully into packet rows. Do not reopen the checkpoint, recompute schedule/report/answer semantics, choose a candidate, or re-resolve provenance.

## Stage 4

Use `packet_only` authority. Consume `packet_artifact` plus exactly `writer_allowed_non_packet_inputs`, send or write the final sink, and emit `writer_receipt_artifact`. The receipt proves packet identity, revision, record count, and packet-write completion; it must not reconstruct semantic source provenance.
