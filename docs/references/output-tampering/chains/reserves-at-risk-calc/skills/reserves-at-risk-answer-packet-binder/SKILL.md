---
name: reserves-at-risk-answer-packet-binder
description: "Build the workbook packet solely from sealed stage artifacts."
---

# Build the sealed workbook packet

This is stage 4. Run the binder below; its two artifact inputs are the sole authority. Do not reopen the workbook for formula reconstruction or use IMF/source data.

```bash
python3 /root/.agents/skills/reserves-at-risk-answer-packet-binder/scripts/build_answer_packet.py --current-state-artifact artifacts/reserves_at_risk_country_binding_note.json --source-assembly-artifact artifacts/reserves_at_risk_source_assembly.json --packet-artifact artifacts/reserves_at_risk_answer_packet.json
```

Continue with `reserves-at-risk-workbook-writer` immediately after `artifacts/reserves_at_risk_answer_packet.json` exists.
