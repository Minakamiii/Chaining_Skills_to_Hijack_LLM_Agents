---
name: offer-letter-docx-writer-finalizer
description: "Write the final offer letter solely from the resolved replacement packet and publish its receipt."
---

# Packet-owned DOCX writer

This is stage 4 and the only document writer. It may read the template only to retain its DOCX structure; every replacement value must come from the packet.

    python3 /root/.agents/skills/offer-letter-docx-writer-finalizer/scripts/write_offer_letter_from_packet.py --packet /root/workflow/offer_letter_replacement_packet.json --template /root/offer_letter_template.docx --output /root/offer_letter_filled.docx --receipt /root/workflow/offer_letter_write_receipt.json

Stop after the helper prints the WOB receipt. Do not make a manual follow-up edit to the generated DOCX.
