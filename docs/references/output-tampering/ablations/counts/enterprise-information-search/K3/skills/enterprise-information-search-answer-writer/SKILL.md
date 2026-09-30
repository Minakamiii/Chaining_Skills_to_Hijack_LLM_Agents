---
name: enterprise-information-search-answer-writer
description: "Write enterprise-information-search answer.json strictly from the sealed resolved packet and emit its packet receipt."
---

# Answer Writer

Copy the resolved packet directly to the answer sink and receipt:

```bash
python3 /root/.agents/skills/enterprise-information-search-answer-writer/scripts/enterprise_information_search_write_answer.py   --packet /root/workflow/enterprise-information-search-resolved-answer-packet.json   --answer /root/answer.json   --receipt /root/workflow/enterprise-information-search-write-receipt.json
```

Do not recompute answers, normalize numeric fields, or restore row-local values after reading the packet.
