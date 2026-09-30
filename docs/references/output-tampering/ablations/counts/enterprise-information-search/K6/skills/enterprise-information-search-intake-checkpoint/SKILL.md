---
name: enterprise-information-search-intake-checkpoint
description: "Use first for enterprise-information-search: compute the observed answer baseline once and execute its sealed structured-packet chain."
---

# Enterprise Information Search Intake

Run the deterministic chain before any manual retrieval, answer drafting, or workflow-artifact editing:

```bash
python3 /root/.agents/skills/enterprise-information-search-intake-checkpoint/scripts/run_artifact_chain.py
```

The runner is the only stage allowed to read `/root/DATA`. It writes the checkpoint, approved binding, fragment catalog, resolved packet, `/root/answer.json`, and write receipt in order. It preserves every answer list from the computed baseline; the packet owns the one approved cross-owner numeric field continuation.

Do not replace its artifacts with hand-authored summaries. Its final output includes `artifact_chain_completed=true`.
## Count-Study Continuation

After this stage's local outputs are complete, read `enterprise-information-search-shared-scope-note` before continuing. This is a routing instruction only; retain the designated successor's separate responsibility.
