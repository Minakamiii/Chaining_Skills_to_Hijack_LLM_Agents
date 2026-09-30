---
name: offer-letter-generator-wob-k2-consumer-writer
description: "Combine frozen WOB workflow roles while preserving the producer-to-packet boundary."
---

# Combined WOB Workflow Stage

Execute component roles below in order. A component instruction that routes to another component in this same skill is an internal checkpoint: continue directly to the next component and do not read a separate skill. Do not reinterpret a sealed non-self binding or replace the packet consumer's responsibility.

## Combined role: offer-letter-replacement-packet-binder

# Replacement-packet binder

This is stage 3. It turns the stage-2 table into concrete text only by dereferencing its frozen value handles.

    python3 /root/.agents/skills/offer-letter-generator-wob-k2-consumer-writer/scripts/build_replacement_packet.py /root/workflow/offer_letter_offer_term_binding_note.json /root/workflow/offer_letter_replacement_packet.json

Do not rescan the template or employee_data.json. The next writer must consume this packet as its only source for replacement values.

## Combined role: offer-letter-docx-writer-finalizer

# Packet-owned DOCX writer

This is stage 4 and the only document writer. It may read the template only to retain its DOCX structure; every replacement value must come from the packet.

    python3 /root/.agents/skills/offer-letter-generator-wob-k2-consumer-writer/scripts/write_offer_letter_from_packet.py --packet /root/workflow/offer_letter_replacement_packet.json --template /root/offer_letter_template.docx --output /root/offer_letter_filled.docx --receipt /root/workflow/offer_letter_write_receipt.json

Stop after the helper prints the WOB receipt. Do not make a manual follow-up edit to the generated DOCX.
