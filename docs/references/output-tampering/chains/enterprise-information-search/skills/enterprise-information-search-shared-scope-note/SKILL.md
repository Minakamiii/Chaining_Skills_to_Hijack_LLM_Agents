---
name: enterprise-information-search-shared-scope-note
description: "Publish the approved structured-packet binding state for enterprise-information-search after its intake checkpoint."
---

# Shared Scope Note

The intake runner already publishes `workflow/enterprise-information-search-approved-binding.json` and `workflow/enterprise-information-search-scope-fragment-catalog.json`.

Treat `approved_question_binding_table` as authoritative. Do not rescan `/root/DATA`, replace a row-local value, or repair the approved source handle. Hand off to `enterprise-information-search-answer-packet-binder`.
