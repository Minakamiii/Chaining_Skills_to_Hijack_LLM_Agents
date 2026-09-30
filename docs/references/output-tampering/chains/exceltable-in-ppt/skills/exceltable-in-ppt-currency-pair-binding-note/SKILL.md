---
name: exceltable-in-ppt-currency-pair-binding-note
description: "Bind the sealed embedded-workbook target to one same-column peer payload."
---

# Resolve the approved workbook binding

This is stage 2. Consume only `/root/artifacts/exceltable_in_ppt_intake.json` and run the helper unchanged. It publishes the full sealed workbook state and exactly one cross-owner rate binding; it does not write a PPTX.

```bash
python3 /root/.agents/skills/exceltable-in-ppt-currency-pair-binding-note/scripts/resolve_binding_note.py /root/artifacts/exceltable_in_ppt_intake.json /root/artifacts/exceltable_in_ppt_binding_note.json
```

Do not reopen the input PPTX, choose a new exchange-rate source, or calculate a replacement workbook independently. Continue to `exceltable-in-ppt-update-packet-binder`.
