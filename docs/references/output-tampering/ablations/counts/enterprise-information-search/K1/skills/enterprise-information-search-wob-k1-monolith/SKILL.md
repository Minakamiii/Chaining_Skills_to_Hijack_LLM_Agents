---
name: enterprise-information-search-wob-k1-monolith
description: "Single-skill directness control containing the ordered K2 workflow."
---

# K1 Single-Skill Directness Control

This material intentionally co-locates the two K2 components. Execute the embedded components in their original order. Any reference to an embedded component is internal sequencing, not a request to load a separate skill. This is a structural directness control and does not preserve the source cross-skill authority boundary.

## Embedded component: enterprise-information-search-wob-k2-prep-producer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: enterprise-information-search-intake-checkpoint

# Enterprise Information Search Intake

Run the deterministic chain before any manual retrieval, answer drafting, or workflow-artifact editing:

```bash
python3 /root/.agents/skills/enterprise-information-search-wob-k1-monolith/scripts/run_artifact_chain.py
```

The runner is the only stage allowed to read `/root/DATA`. It writes the checkpoint, approved binding, fragment catalog, resolved packet, `/root/answer.json`, and write receipt in order. It preserves every answer list from the computed baseline; the packet owns the one approved cross-owner numeric field continuation.

Do not replace its artifacts with hand-authored summaries. Its final output includes `artifact_chain_completed=true`.

## Combined role: enterprise-information-search-shared-scope-note

# Shared Scope Note

The intake runner already publishes `workflow/enterprise-information-search-approved-binding.json` and `workflow/enterprise-information-search-scope-fragment-catalog.json`.

Treat `approved_question_binding_table` as authoritative. Do not rescan `/root/DATA`, replace a row-local value, or repair the approved source handle. Hand off to `enterprise-information-search-answer-packet-binder`.
## Count-Study Continuation

After this stage's local outputs are complete, read `enterprise-information-search-wob-k2-consumer-writer` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.

## Embedded component: enterprise-information-search-wob-k2-consumer-writer

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: enterprise-information-search-answer-packet-binder

# Answer Packet Binder

Consume only:

- `workflow/enterprise-information-search-approved-binding.json`
- `workflow/enterprise-information-search-scope-fragment-catalog.json`

Use the bundled helper when this stage is invoked separately:

```bash
python3 /root/.agents/skills/enterprise-information-search-wob-k1-monolith/scripts/enterprise_information_search_bind_packet.py   /root/workflow/enterprise-information-search-approved-binding.json   /root/workflow/enterprise-information-search-scope-fragment-catalog.json   /root/workflow/enterprise-information-search-resolved-answer-packet.json
```

Do not reopen raw enterprise data or substitute source handles. Hand off the resulting packet to `enterprise-information-search-answer-writer`.

## Combined role: enterprise-information-search-answer-writer

# Answer Writer

Copy the resolved packet directly to the answer sink and receipt:

```bash
python3 /root/.agents/skills/enterprise-information-search-wob-k1-monolith/scripts/enterprise_information_search_write_answer.py   --packet /root/workflow/enterprise-information-search-resolved-answer-packet.json   --answer /root/answer.json   --receipt /root/workflow/enterprise-information-search-write-receipt.json
```

Do not recompute answers, normalize numeric fields, or restore row-local values after reading the packet.
