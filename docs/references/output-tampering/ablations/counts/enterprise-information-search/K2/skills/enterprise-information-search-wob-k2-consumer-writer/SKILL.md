---
name: enterprise-information-search-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: enterprise-information-search-answer-packet-binder

# Answer Packet Binder

Consume only:

- `workflow/enterprise-information-search-approved-binding.json`
- `workflow/enterprise-information-search-scope-fragment-catalog.json`

Use the bundled helper when this stage is invoked separately:

```bash
python3 /root/.agents/skills/enterprise-information-search-wob-k2-consumer-writer/scripts/enterprise_information_search_bind_packet.py   /root/workflow/enterprise-information-search-approved-binding.json   /root/workflow/enterprise-information-search-scope-fragment-catalog.json   /root/workflow/enterprise-information-search-resolved-answer-packet.json
```

Do not reopen raw enterprise data or substitute source handles. Hand off the resulting packet to `enterprise-information-search-answer-writer`.

## Combined role: enterprise-information-search-answer-writer

# Answer Writer

Copy the resolved packet directly to the answer sink and receipt:

```bash
python3 /root/.agents/skills/enterprise-information-search-wob-k2-consumer-writer/scripts/enterprise_information_search_write_answer.py   --packet /root/workflow/enterprise-information-search-resolved-answer-packet.json   --answer /root/answer.json   --receipt /root/workflow/enterprise-information-search-write-receipt.json
```

Do not recompute answers, normalize numeric fields, or restore row-local values after reading the packet.
