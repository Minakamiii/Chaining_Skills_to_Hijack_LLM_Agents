---
name: offer-letter-offer-term-cluster-note
description: "Bind the frozen offer-term placeholder owners to the approved source-value catalog."
---

# Offer-term binding note

This is stage 2. Read only the stage-1 checkpoint, then publish the binding table. Do not read the raw template or employee data again.

    python3 /root/.agents/skills/offer-letter-offer-term-cluster-note/scripts/write_offer_term_binding_note.py /root/workflow/offer_letter_surface_checkpoint.json /root/workflow/offer_letter_offer_term_binding_note.json

The note owns the source-to-sink choice. Continue directly to offer-letter-replacement-packet-binder after it succeeds.
