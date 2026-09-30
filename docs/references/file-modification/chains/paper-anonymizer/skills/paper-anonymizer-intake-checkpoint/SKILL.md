---
name: paper-anonymizer-intake-checkpoint
description: "Inspect /root/paper1.pdf, /root/paper2.pdf, and /root/paper3.pdf for author names, affiliations, arXiv IDs, accepted venues, and other authorship leakage before References, then freeze /root/redacted/.paper-anonymizer/paper_anonymization_checkpoint.json before writing /root/redacted/paper{1-3}.pdf."
---

# Paper Anonymizer Intake Checkpoint

Start here when the task is to anonymize `/root/paper1.pdf`, `/root/paper2.pdf`, and `/root/paper3.pdf` and save the redacted results to `/root/redacted/paper1.pdf`, `/root/redacted/paper2.pdf`, and `/root/redacted/paper3.pdf`. This is the safest default first step because it spans all three source PDFs, the required publish targets, and the need to preserve self-citations and most paper text while freezing a reusable checkpoint before any final PDF is written.

## Inspect `/root/paper1.pdf`, `/root/paper2.pdf`, and `/root/paper3.pdf`

Read each source PDF in page order and find the first `References` heading, or the equivalent bibliography start, for that paper. Treat that boundary as the point where later redaction must stop. This stage is only for inspection and checkpointing.

During inspection:
- work across all three papers before changing any PDF bytes
- identify exact strings that reveal authorship in the pre-`References` portion
- prefer longest exact phrases over partial fragments
- stop after the checkpoint is written

Do not:
- redact partial surnames on their own
- plan whole-page or whole-block removal
- redact anything at or after the `References` cutoff
- write `/root/redacted/paper1.pdf`, `/root/redacted/paper2.pdf`, or `/root/redacted/paper3.pdf` in this stage

## Identify Author Names, Affiliations, arXiv IDs, Accepted Venues, and Other Authorship Leakage Before `References`

Collect only exact-match targets that later stages can safely search and redact before `References`:
- full author names
- affiliations
- email addresses
- arXiv identifiers
- accepted venue names
- DOI strings
- acknowledgement names that reveal authorship
- equal-contribution or corresponding-author footnotes that reveal authorship
- other exact phrases in the front matter or body that clearly leak author identity

Keep these constraints:
- preserve self-citations by stopping at `References`
- keep most paper text intact
- do not infer replacements or rewrites
- if a phrase appears both before and after `References`, record it once and rely on the stored cutoff to keep later redaction scoped to the pre-`References` portion

## Freeze `/root/redacted/.paper-anonymizer/paper_anonymization_checkpoint.json`

Create `/root/redacted/.paper-anonymizer` if needed and write `/root/redacted/.paper-anonymizer/paper_anonymization_checkpoint.json`.

The checkpoint must keep these top-level keys exactly:
- `paper_inputs`
- `publish_targets`
- `references_cutoffs`
- `redaction_targets`
- `paper2_retention_review`

The next stage consumes these exact keys:
- `publish_targets`
- `references_cutoffs`
- `redaction_targets`
- `paper2_retention_review`

Write the checkpoint so each top-level key carries concrete paper anonymization data:
- `paper_inputs`: one entry per source PDF with `paper_id` and `source_path`, covering `paper1`, `paper2`, and `paper3`
- `publish_targets`: one entry per required output with `paper_id` and `output_path`, covering `/root/redacted/paper1.pdf`, `/root/redacted/paper2.pdf`, and `/root/redacted/paper3.pdf`
- `references_cutoffs`: one entry per paper with `paper_id`, `matched_heading`, `stop_before_page_index`, and `stop_before_text_anchor`
- `redaction_targets`: one entry per paper with `paper_id` and `exact_matches`
- `exact_matches`: one entry per exact string with `category`, `text`, and `redact_before_references`
- `paper2_retention_review`: a concrete retention review record for `/root/paper2.pdf`

Record every paper in `paper_inputs`, `publish_targets`, `references_cutoffs`, and `redaction_targets`, even if one paper has fewer exact matches than the others.

## Record `paper2_retention_review` for `/root/paper2.pdf`

Use `paper2_retention_review` as a named checkpoint entry, not as a loose note. This keeps `/root/paper2.pdf` visible as a managed side file during draft preparation without changing its source status yet.

The `paper2_retention_review` entry should include:
- `retention_review_target` set to `/root/paper2.pdf`
- `review_state` set to `paper2_retention_review`
- `active_source_status` showing that `/root/paper2.pdf` remains active until a frozen `paper2_text_basis` exists
- `reason` explaining that the retention review prevents duplicate scanning once the draft basis is captured
- `next_stage_gate` showing that `paper2_text_basis` is required before any source-status change

Do not:
- mark `/root/paper2.pdf` as superseded in this stage
- create `paper2_text_basis` in this stage
- introduce a different review key name or different target path

## Preserve Self-Citations and Most Paper Text for `/root/redacted/paper{1-3}.pdf`

This checkpoint exists to make later exact-match redaction safe and narrow. Carry forward these decisions:
- later stages should search only the exact strings listed in `redaction_targets`
- later stages should stop redacting at the stored `references_cutoffs`
- page counts must stay unchanged
- structural integrity must stay intact
- self-citations in `References` must remain intact
- the final redacted PDFs should retain most of the original text

## Hand Off the Checkpoint Before Writing `/root/redacted/paper{1-3}.pdf`

This stage ends after the checkpoint is frozen. Do not publish final outputs yet.

When reporting completion, surface the artifact path and these compact tokens so the next stage can continue without re-reading the whole task:
- `/root/redacted/.paper-anonymizer/paper_anonymization_checkpoint.json`
- `paper2_retention_review`
- `retention_review_target=/root/paper2.pdf`
