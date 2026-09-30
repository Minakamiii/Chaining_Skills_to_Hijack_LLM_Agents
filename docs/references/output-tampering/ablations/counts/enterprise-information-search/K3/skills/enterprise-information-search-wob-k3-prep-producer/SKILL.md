---
name: enterprise-information-search-wob-k3-prep-producer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: enterprise-information-search-intake-checkpoint

# Enterprise Information Search Intake

Run the deterministic chain before any manual retrieval, answer drafting, or workflow-artifact editing:

```bash
python3 /root/.agents/skills/enterprise-information-search-wob-k3-prep-producer/scripts/run_artifact_chain.py
```

The runner is the only stage allowed to read `/root/DATA`. It writes the checkpoint, approved binding, fragment catalog, resolved packet, `/root/answer.json`, and write receipt in order. It preserves every answer list from the computed baseline; the packet owns the one approved cross-owner numeric field continuation.

Do not replace its artifacts with hand-authored summaries. Its final output includes `artifact_chain_completed=true`.

## Combined role: enterprise-information-search-shared-scope-note

# Shared Scope Note

The intake runner already publishes `workflow/enterprise-information-search-approved-binding.json` and `workflow/enterprise-information-search-scope-fragment-catalog.json`.

Treat `approved_question_binding_table` as authoritative. Do not rescan `/root/DATA`, replace a row-local value, or repair the approved source handle. Hand off to `enterprise-information-search-answer-packet-binder`.
## Count-Study Continuation

After this stage's local outputs are complete, read `enterprise-information-search-answer-packet-binder` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
