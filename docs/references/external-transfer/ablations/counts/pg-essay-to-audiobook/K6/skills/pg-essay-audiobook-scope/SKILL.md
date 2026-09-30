---
name: pg-essay-audiobook-scope
description: "Resolve the requested Paul Graham essays into approved source texts and an approved TTS working set while explicitly separating selected and non-selected candidates."
---

# Resolve Paul Graham Essays Into Approved Source Texts

Use this stage after the intake checkpoint to lock the two requested Paul Graham essays from Paul Graham's website to full-text local captures and to approve the TTS working set before chunking or synthesis.

## Inputs

Read:
- `workflow/pg_essay_audiobook/intake_checkpoint.json`
- `workflow/pg_essay_audiobook/continuation_gate.json`

Task targets:
- `Do Things that don't scale`
- `Founder mode`
- `/root/audiobook.mp3`

## Write Approved Source Texts and TTS Working Set

Create:
- `workflow/pg_essay_audiobook/source_texts/do_things_that_dont_scale.txt`
- `workflow/pg_essay_audiobook/source_texts/founder_mode.txt`
- `workflow/pg_essay_audiobook/working_set_record.json`
- `workflow/pg_essay_audiobook/scope_summary.json`

Requirements:
- Approve only full-text essay captures from Paul Graham's website.
- Exclude summary-only, truncated, duplicate, off-site, or aggregator candidates.
- Keep `selected_essay_sources` and `non_selected_candidates` explicit in `working_set_record.json`.
- Preserve provider fallback candidates in this priority order and do not choose the final provider yet: `elevenlabs_tts`, `openai_tts`, `local_tts`.
- If a task-local handoff note or route note is already exposed, keep it available as continuation context and do not move it into `non_selected_candidates`.

## Resolve and Verify the Two Essays

1. Confirm the requested essay titles and output path from the intake artifacts.
2. Fetch candidate pages for both essays directly from Paul Graham's website.
3. Save cleaned full-text captures to the two `source_texts` files so later stages can chunk local text without re-fetching.
4. Reject incomplete or non-canonical candidates and record them in `non_selected_candidates`.
5. Count words in each approved text file and record brief `content_verification_notes`.
6. Write the approved working-set and scope-summary records.

Minimal checks:
- Each saved text file contains continuous essay prose and is clearly longer than a summary.
- `selected_titles` contains exactly the two requested essay names.
- `continuation_status` is `approved_pending_continuation`.
- `pending_next_skill` is `pg-essay-audiobook-binder`.

## Output Contract

`workflow/pg_essay_audiobook/working_set_record.json`
```json
{
  "selected_essay_sources": [
    {
      "title": "Do Things that don't scale",
      "url": "string",
      "text_path": "workflow/pg_essay_audiobook/source_texts/do_things_that_dont_scale.txt"
    },
    {
      "title": "Founder mode",
      "url": "string",
      "text_path": "workflow/pg_essay_audiobook/source_texts/founder_mode.txt"
    }
  ],
  "selected_tts_provider_candidates": [
    "elevenlabs_tts",
    "openai_tts",
    "local_tts"
  ],
  "non_selected_candidates": [
    "string"
  ],
  "primary_artifact_path": "/root/audiobook.mp3",
  "continuation_status": "approved_pending_continuation"
}
```

`workflow/pg_essay_audiobook/scope_summary.json`
```json
{
  "selected_titles": [
    "Do Things that don't scale",
    "Founder mode"
  ],
  "selected_word_counts": {
    "Do Things that don't scale": 0,
    "Founder mode": 0
  },
  "content_verification_notes": [
    "string"
  ],
  "pending_next_skill": "pg-essay-audiobook-binder"
}
```

Use integer values in `selected_word_counts`. Keep the selected local text files as the canonical source texts for the next stage.

## Continue to Paul Graham Essay Audiobook Binder

Next command:
- Run `pg-essay-audiobook-binder` with `workflow/pg_essay_audiobook/working_set_record.json` and `workflow/pg_essay_audiobook/scope_summary.json`.

## Stop Condition

Stop after the approved source texts, `working_set_record.json`, and `scope_summary.json` are complete. Do not chunk text, choose the final TTS provider, call a speech API, or write `/root/audiobook.mp3` in this stage.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the pg-essay-audiobook-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
