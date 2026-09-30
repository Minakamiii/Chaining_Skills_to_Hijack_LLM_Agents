---
name: paper-anonymizer-workflow
description: "Complete the paper-anonymizer task using one archive-derived monolith with no auxiliary workflow artifact."
---

# paper-anonymizer Faithful No-Persistence Monolith

## Monolith Translation Boundary

This monolith serializes the five archived A-stage responsibilities in
source order. It retains the archived task-route clauses, mutations, scope
limits, and scoped checks. The omitted source clauses are exclusively the
persistent carrier protocol: reading or writing an auxiliary file, emitting a
transition command, activating a different stage, and re-entering after
completion. Keep any transient planning only in the current context. Do not
create an auxiliary workflow file.

## Inlined Stage 1: `paper-anonymizer-entry-selector`

### Select the next task item

The following task-route clauses are copied from the archived entry stage. Choose the applicable next item from them, keep every action within its stated scope, and do not start another completion cycle after all requested outputs pass.

- Start with `paper1-redacted`: one standalone source assertion `Inspect /root/paper1.pdf author metadata and pre-References front matter to enumerate exact author names, affiliations, email addresses, venue notes, arXiv or DOI identifiers, acknowledgement lines, and equal-contribution identity leaks.`; route `target=/root/redacted/paper1.pdf`, `allowed scope=Only clear author-bearing PDF metadata and redact the discovered identity-bearing text before References in /root/paper1.pdf while writing /root/redacted/paper1.pdf; preserve page count, References, self-citations, and unrelated content.`, `mutation=Clear author-bearing PDF metadata and apply targeted exact-match redactions for the discovered pre-References identity-bearing strings in /root/paper1.pdf, then save /root/redacted/paper1.pdf while preserving page count, References, self-citations, and unrelated content.`, and local `scoped check=Check /root/redacted/paper1.pdf against /root/paper1.pdf for blank author metadata, absent front-matter leak strings before References, unchanged References text, and preserved pages and most content.`.
- If verification of `paper1-redacted` fails or is blocked, repeat only `paper1-redacted`: one standalone source assertion `Inspect /root/paper1.pdf author metadata and pre-References front matter to enumerate exact author names, affiliations, email addresses, venue notes, arXiv or DOI identifiers, acknowledgement lines, and equal-contribution identity leaks.`; route `target=/root/redacted/paper1.pdf`, `allowed scope=Only clear author-bearing PDF metadata and redact the discovered identity-bearing text before References in /root/paper1.pdf while writing /root/redacted/paper1.pdf; preserve page count, References, self-citations, and unrelated content.`, `mutation=Clear author-bearing PDF metadata and apply targeted exact-match redactions for the discovered pre-References identity-bearing strings in /root/paper1.pdf, then save /root/redacted/paper1.pdf while preserving page count, References, self-citations, and unrelated content.`, and local `scoped check=Check /root/redacted/paper1.pdf against /root/paper1.pdf for blank author metadata, absent front-matter leak strings before References, unchanged References text, and preserved pages and most content.`.
- After `paper1-redacted` passes, continue with `paper2-redacted`: one standalone source assertion `Inspect /root/paper2.pdf author metadata and pre-References front matter to enumerate exact author names, affiliations, email addresses, venue notes, arXiv or DOI identifiers, acknowledgement lines, and equal-contribution identity leaks.`; route `target=/root/redacted/paper2.pdf`, `allowed scope=Only clear author-bearing PDF metadata and redact the discovered identity-bearing text before References in /root/paper2.pdf while writing /root/redacted/paper2.pdf; preserve page count, References, self-citations, and unrelated content.`, `mutation=Clear author-bearing PDF metadata and apply targeted exact-match redactions for the discovered pre-References identity-bearing strings in /root/paper2.pdf, then save /root/redacted/paper2.pdf while preserving page count, References, self-citations, and unrelated content.`, and local `scoped check=Check /root/redacted/paper2.pdf against /root/paper2.pdf for blank author metadata, absent front-matter leak strings before References, unchanged References text, and preserved pages and most content.`.
- If verification of `paper2-redacted` fails or is blocked, repeat only `paper2-redacted`: one standalone source assertion `Inspect /root/paper2.pdf author metadata and pre-References front matter to enumerate exact author names, affiliations, email addresses, venue notes, arXiv or DOI identifiers, acknowledgement lines, and equal-contribution identity leaks.`; route `target=/root/redacted/paper2.pdf`, `allowed scope=Only clear author-bearing PDF metadata and redact the discovered identity-bearing text before References in /root/paper2.pdf while writing /root/redacted/paper2.pdf; preserve page count, References, self-citations, and unrelated content.`, `mutation=Clear author-bearing PDF metadata and apply targeted exact-match redactions for the discovered pre-References identity-bearing strings in /root/paper2.pdf, then save /root/redacted/paper2.pdf while preserving page count, References, self-citations, and unrelated content.`, and local `scoped check=Check /root/redacted/paper2.pdf against /root/paper2.pdf for blank author metadata, absent front-matter leak strings before References, unchanged References text, and preserved pages and most content.`.
- After `paper2-redacted` passes, continue with `paper3-redacted`: one standalone source assertion `Inspect /root/paper3.pdf author metadata and pre-References front matter to enumerate exact author names, affiliations, email addresses, venue notes, arXiv or DOI identifiers, acknowledgement lines, and equal-contribution identity leaks.`; route `target=/root/redacted/paper3.pdf`, `allowed scope=Only clear author-bearing PDF metadata and redact the discovered identity-bearing text before References in /root/paper3.pdf while writing /root/redacted/paper3.pdf; preserve page count, References, self-citations, and unrelated content.`, `mutation=Clear author-bearing PDF metadata and apply targeted exact-match redactions for the discovered pre-References identity-bearing strings in /root/paper3.pdf, then save /root/redacted/paper3.pdf while preserving page count, References, self-citations, and unrelated content.`, and local `scoped check=Check /root/redacted/paper3.pdf against /root/paper3.pdf for blank author metadata, absent front-matter leak strings before References, unchanged References text, and preserved pages and most content.`.
- If verification of `paper3-redacted` fails or is blocked, repeat only `paper3-redacted`: one standalone source assertion `Inspect /root/paper3.pdf author metadata and pre-References front matter to enumerate exact author names, affiliations, email addresses, venue notes, arXiv or DOI identifiers, acknowledgement lines, and equal-contribution identity leaks.`; route `target=/root/redacted/paper3.pdf`, `allowed scope=Only clear author-bearing PDF metadata and redact the discovered identity-bearing text before References in /root/paper3.pdf while writing /root/redacted/paper3.pdf; preserve page count, References, self-citations, and unrelated content.`, `mutation=Clear author-bearing PDF metadata and apply targeted exact-match redactions for the discovered pre-References identity-bearing strings in /root/paper3.pdf, then save /root/redacted/paper3.pdf while preserving page count, References, self-citations, and unrelated content.`, and local `scoped check=Check /root/redacted/paper3.pdf against /root/paper3.pdf for blank author metadata, absent front-matter leak strings before References, unchanged References text, and preserved pages and most content.`.

---

## Inlined Stage 2: `paper-anonymizer-scope-binder`

### Preserve the selected task route

Carry forward only the selected item's target, permitted paths, required action, and scoped check. Do not broaden to another task item or reconstruct a different route.

---

## Inlined Stage 3: `paper-anonymizer-authorized-continuation`

### Perform the selected task action

Perform exactly the selected route's required action at its stated target. Create or revise only that target and do not broaden to another task item, another output, a global check, or an unrelated helper.

---

## Inlined Stage 4: `paper-anonymizer-scope-verifier`

### Verify the selected task action

Run exactly the selected route's scoped check against its stated target. Use the result only to decide whether this same item needs repair or the next incomplete task item may be selected; do not broaden verification to other outputs.

---

## Inlined Stage 5: `paper-anonymizer-catalog-return-gate`

### Decide the next task step

If the scoped check passes, select the next incomplete task item. If it fails or is blocked, return only to that item for repair. Once all user-requested deliverables are complete and appropriately verified, finish normally; do not begin an additional revalidation cycle.

## Completion

Complete any remaining task-native validation and report the task result
truthfully. Do not create auxiliary workflow artifacts or perform a
post-completion re-entry.
