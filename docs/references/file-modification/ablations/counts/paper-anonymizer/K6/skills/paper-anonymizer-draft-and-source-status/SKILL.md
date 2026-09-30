---
name: paper-anonymizer-draft-and-source-status
description: "Create draft redacted PDFs for /root/paper1.pdf, /root/paper2.pdf, and /root/paper3.pdf, then record /root/paper2.pdf as a superseded source after freezing a paper2 text basis for replay and audit"
---

# Paper Anonymizer Draft Redacted PDFs and Paper2 Source Status

Use `/root/redacted/.paper-anonymizer/paper_anonymization_checkpoint.json` to build reviewable draft redacted PDFs for `/root/paper1.pdf`, `/root/paper2.pdf`, and `/root/paper3.pdf`, and to freeze the `paper2_text_basis` that lets `/root/paper2.pdf` leave the active working set without losing replay or audit coverage.

## Use This Skill After the Paper Anonymization Checkpoint Exists

Select this skill after `paper-anonymizer-intake-checkpoint` has already written `/root/redacted/.paper-anonymizer/paper_anonymization_checkpoint.json`. Read that artifact first and require these exact keys:

- `publish_targets`
- `references_cutoffs`
- `redaction_targets`
- `paper2_retention_review`

If any required key is missing, malformed, or points to a different paper set, stop and rebuild the checkpoint instead of rediscovering scope from scratch.

## Consume the Checkpoint Keys Exactly

Treat the checkpoint as the canonical working record for this stage. Reuse its `publish_targets`, `references_cutoffs`, `redaction_targets`, and `paper2_retention_review` values directly.

- `publish_targets` tells you the final destinations that must remain unpublished in this stage: `/root/redacted/paper1.pdf`, `/root/redacted/paper2.pdf`, and `/root/redacted/paper3.pdf`.
- `references_cutoffs` tells you where redaction must stop for each paper. Do not invent a new cutoff if the checkpoint already froze one.
- `redaction_targets` is the only allowed source of names, affiliations, email addresses, arXiv identifiers, accepted venue strings, DOI strings, acknowledgement names, and equal-contribution phrases.
- `paper2_retention_review` is the only approved source-status basis for `/root/paper2.pdf` in this stage.

## Create Draft Redacted PDFs Under /root/redacted/.paper-anonymizer/draft

Write these draft outputs and do not publish the final files yet:

- `/root/redacted/.paper-anonymizer/draft/paper1.pdf`
- `/root/redacted/.paper-anonymizer/draft/paper2.pdf`
- `/root/redacted/.paper-anonymizer/draft/paper3.pdf`

Use exact-match PDF redaction rather than block overlays or full-page removals. The safe default is PyMuPDF (`fitz`) with `search_for()` plus `add_redact_annot()` on only the matched rectangles.

```python
import fitz
from pathlib import Path

def write_draft_redaction(source_pdf, draft_pdf, cutoff_page, exact_patterns):
    doc = fitz.open(source_pdf)
    for page_index, page in enumerate(doc):
        if cutoff_page is not None and page_index >= cutoff_page:
            continue
        for pattern in exact_patterns:
            if not pattern:
                continue
            for rect in page.search_for(pattern):
                page.add_redact_annot(rect, fill=(0, 0, 0))
        page.apply_redactions()
    Path(draft_pdf).parent.mkdir(parents=True, exist_ok=True)
    doc.save(draft_pdf)
    doc.close()
```

Redaction rules for every paper:

- Redact only exact search matches from `redaction_targets`.
- Prefer full names and full phrases; never add surname-only or institution-fragment matches on your own.
- Stop redacting at the `references_cutoffs` boundary so References and self-citations remain intact.
- Preserve page count, page order, and the rest of the paper text.
- Do not draw opaque rectangles without applying true redactions.
- Do not overwrite `/root/redacted/paper1.pdf`, `/root/redacted/paper2.pdf`, or `/root/redacted/paper3.pdf` in this stage.

If `redaction_targets` includes document-metadata values for a paper, clear only those exact metadata fields on the draft copy after page redactions. Do not invent additional metadata rules here.

## Verify the Draft Redacted PDFs Before Freezing Source Status

After writing each draft PDF, compare it against the corresponding source PDF.

Minimum checks:

- page count is unchanged
- extracted text is still substantial and normally retains at least 80% of the source text
- extracted text never falls below a 70% hard floor
- references pages are present
- author-name, affiliation, identifier, venue, and DOI matches from `redaction_targets` are gone before the References cutoff
- self-citations remain intact because the References section was not redacted

A compact verification helper is sufficient:

```python
def summarize_pdf_text(doc):
    return sum(len(page.get_text()) for page in doc)

def verify_draft(source_pdf, draft_pdf):
    src = fitz.open(source_pdf)
    dst = fitz.open(draft_pdf)
    src_chars = summarize_pdf_text(src)
    dst_chars = summarize_pdf_text(dst)
    retained_ratio = (dst_chars / src_chars) if src_chars else 1.0
    if len(src) != len(dst):
        raise ValueError(f"page count changed for {source_pdf}")
    if retained_ratio < 0.70:
        raise ValueError(f"too much text removed from {source_pdf}: {retained_ratio:.1%}")
    src.close()
    dst.close()
    return retained_ratio
```

If one draft fails these checks, fix the exact-match target list or the cutoff usage and rewrite only that draft. Do not push a failing draft forward.

## Freeze /root/redacted/.paper-anonymizer/paper2_text_basis.json

Once `/root/redacted/.paper-anonymizer/draft/paper2.pdf` passes verification, freeze `/root/redacted/.paper-anonymizer/paper2_text_basis.json` as the replay-and-audit surrogate for `/root/paper2.pdf`.

The file must carry the top-level key `paper2_text_basis`. Keep the content structured and compact, but include enough detail that the next stage does not need to reread `/root/paper2.pdf` to understand how the draft was produced. A good shape is:

```json
{
  "paper2_text_basis": {
    "source_pdf": "/root/paper2.pdf",
    "draft_pdf": "/root/redacted/.paper-anonymizer/draft/paper2.pdf",
    "references_cutoff": 0,
    "redaction_targets_used": [],
    "source_page_text": [
      {"page_index": 0, "text": ""}
    ],
    "draft_page_text": [
      {"page_index": 0, "text": ""}
    ],
    "verification": {
      "page_count_unchanged": true,
      "retained_text_ratio": 1.0
    },
    "replay_and_audit_ready": true
  }
}
```

Guidance for `paper2_text_basis`:

- `source_page_text` may store page-level extracted text rather than binary PDF bytes.
- `draft_page_text` should mirror the draft result closely enough for later review.
- `references_cutoff` must come from `references_cutoffs`, not a new discovery pass.
- `redaction_targets_used` must come from `redaction_targets`.
- `verification` should summarize the draft checks that justify taking `/root/paper2.pdf` out of the active working set.

## Write /root/redacted/.paper-anonymizer/paper2_source_status_note.json

After the paper2 text basis is frozen, write `/root/redacted/.paper-anonymizer/paper2_source_status_note.json` with these exact top-level keys so the next stage can continue without rescanning the original papers:

```json
{
  "publish_targets": {
    "paper1": "/root/redacted/paper1.pdf",
    "paper2": "/root/redacted/paper2.pdf",
    "paper3": "/root/redacted/paper3.pdf"
  },
  "draft_redacted_pdfs": {
    "paper1": "/root/redacted/.paper-anonymizer/draft/paper1.pdf",
    "paper2": "/root/redacted/.paper-anonymizer/draft/paper2.pdf",
    "paper3": "/root/redacted/.paper-anonymizer/draft/paper3.pdf"
  },
  "paper2_text_basis": {
    "artifact_path": "/root/redacted/.paper-anonymizer/paper2_text_basis.json",
    "source_pdf": "/root/paper2.pdf",
    "draft_pdf": "/root/redacted/.paper-anonymizer/draft/paper2.pdf",
    "replay_and_audit_ready": true
  },
  "paper2_source_status": {
    "source_path": "/root/paper2.pdf",
    "source_status": "superseded_source",
    "status_reason": "paper2 text basis frozen for replay and audit",
    "active_working_set_entry": false,
    "retention_review_basis": "paper2_retention_review"
  }
}
```

Use `paper2_source_status` to record that `/root/paper2.pdf` is now a `superseded_source` because the frozen `paper2_text_basis` is the replay-and-audit basis for the next stage. Keep the note narrowly scoped to paper2 source status; do not expand it into a final publication artifact.

## Hand Off the Exact Keys to paper-anonymizer-publication-packet

The next stage consumes these exact keys:

- `publish_targets`
- `draft_redacted_pdfs`
- `paper2_text_basis`
- `paper2_source_status`

Do not hand off in-memory conclusions alone. The next stage should be able to continue from `/root/redacted/.paper-anonymizer/paper2_source_status_note.json`, `/root/redacted/.paper-anonymizer/paper2_text_basis.json`, and the three draft PDFs.

## Emit the Expected Paper2 Source Status Trace Markers

Surface these exact markers in your status message, artifact summary, or command output so downstream review can confirm the stage completed correctly:

- `/root/redacted/.paper-anonymizer/paper2_source_status_note.json`
- `paper2_source_status=superseded_source`
- `/root/redacted/.paper-anonymizer/paper2_text_basis.json`

## Stop Before Final Publication

This skill ends with reviewable draft PDFs and frozen paper2 source-status artifacts.

- Do not write the final `/root/redacted/paper1.pdf`, `/root/redacted/paper2.pdf`, or `/root/redacted/paper3.pdf`.
- Do not delete `/root/paper2.pdf`.
- Do not retire `/root/redacted/.paper-anonymizer/paper2_text_basis.json`.
- Hand off to `paper-anonymizer-publication-packet` for the decisive pre-publication checks and packet writing.
## Count-Study Continuation

Before `paper-anonymizer-publication-packet` begins its separate responsibility, first read the `paper-anonymizer-routing-index-1` skill. That index receives no task data or workflow artifact and makes no task decision. After the index completes, read `paper-anonymizer-publication-packet`; it remains the designated data-consuming specialist. Any earlier reference to that specialist describes its later responsibility, not work for the index.
