---
name: enterprise-information-search-answer-packet-binder
description: "Materialize the enterprise-information-search resolved answer packet only from its approved binding and fragment catalog."
---

# Answer Packet Binder

Consume only:

- `workflow/enterprise-information-search-approved-binding.json`
- `workflow/enterprise-information-search-scope-fragment-catalog.json`

Use the bundled helper when this stage is invoked separately:

```bash
python3 /root/.agents/skills/enterprise-information-search-answer-packet-binder/scripts/enterprise_information_search_bind_packet.py   /root/workflow/enterprise-information-search-approved-binding.json   /root/workflow/enterprise-information-search-scope-fragment-catalog.json   /root/workflow/enterprise-information-search-resolved-answer-packet.json
```

Do not reopen raw enterprise data or substitute source handles. Hand off the resulting packet to `enterprise-information-search-answer-writer`.
