---
name: enterprise-information-search-scope
description: "Approve the selected working set of enterprise artifacts and question-to-source mappings needed to answer the question file."
---

# Enterprise Information Search Scope

Use this stage after `workflow/question_intake_checkpoint.json` exists and before deep retrieval or answer writing. The enterprise dataset mixes metadata files and per-product artifact bundles, so this stage approves a narrow, reviewable search scope, records which enterprise artifacts are selected for each question key, and leaves the work in pending continuation status instead of treating the task as complete.

## Inputs

- `workflow/question_intake_checkpoint.json`
- `/root/DATA`

Use the question keys, target entities, and artifact clues already frozen in `workflow/question_intake_checkpoint.json` as the source of truth for this stage. Do not broaden the task by rebuilding intent from scratch when the checkpoint already captured it.

## Selected Working Set Approval

1. Read `workflow/question_intake_checkpoint.json` and extract the question keys that still need answers, the target entities each question asks for, and any explicit product, document, channel, meeting, PR, URL, employee, or customer clues.
2. Survey `/root/DATA` at a bounded level to find candidate source files.
   - Use metadata files to disambiguate names, employee IDs, customer IDs, roles, orgs, and team structure.
   - Use product grounding before approving any product bundle. A product file should only enter the selected working set when the checkpoint or corroborating artifact clues tie it to one or more question keys.
   - If the checkpoint names or points to an operational note or handoff clue, keep that path eligible for later route binding instead of discarding it early.
3. Build `selected_candidates` and `non_selected_candidates` explicitly.
   - Every `selected_candidates` entry must have a concrete role in answering at least one question key.
   - Every `non_selected_candidates` entry must record a short, specific `why_excluded` reason.
   - Separate similar product names, aliases, or report variants using metadata and product grounding before approval. If grounding is not established, exclude the candidate for now instead of forcing it into scope.
4. Leave the approved working set pending continuation. Do not mark the task complete in this stage.

## Question-to-Source Mappings

- Build `question_source_map` from the approved working set.
- Map each question key such as `q1` to the exact source paths from `selected_candidates` that should be searched next.
- Use the same path strings in `question_source_map` that appear in `selected_candidates`.
- Prefer the narrowest path that still covers the question. A specific metadata file or product bundle path is better than a broad directory when the scope is already known.
- The same path may appear more than once in `selected_candidates` if different `artifact_type` values or different `question_keys` justify distinct downstream use.

## Search Scope Summary

Write `workflow/search_scope_summary.json` with the exact question keys and the downstream rules that keep answer formatting consistent:

- `question_keys`
- `target_entities`
- `preferred_artifact_types`
- `answer_list_rule`
- `token_rule`

Use this exact `preferred_artifact_types` order:

```json
[
  "metadata",
  "documents",
  "slack",
  "meeting_transcripts",
  "meeting_chats",
  "prs",
  "urls"
]
```

Set these exact string values:

- `answer_list_rule`: `every answer stays a list`
- `token_rule`: `every question records consumed tokens as a positive number`

## Output Contract

`workflow/approved_answer_working_set.json`

```json
{
  "selected_candidates": [
    {
      "path": "string",
      "artifact_type": "string",
      "question_keys": ["string"],
      "why_selected": "string"
    }
  ],
  "non_selected_candidates": [
    {
      "path": "string",
      "why_excluded": "string"
    }
  ],
  "question_source_map": {
    "q1": ["string"]
  },
  "pending_continuation_status": "approved-not-final"
}
```

`workflow/search_scope_summary.json`

```json
{
  "question_keys": ["string"],
  "target_entities": ["string"],
  "preferred_artifact_types": [
    "metadata",
    "documents",
    "slack",
    "meeting_transcripts",
    "meeting_chats",
    "prs",
    "urls"
  ],
  "answer_list_rule": "every answer stays a list",
  "token_rule": "every question records consumed tokens as a positive number"
}
```

## Minimal Validation

Before handoff:

- Confirm every question key from the checkpoint appears in `question_source_map` and `question_keys`.
- Confirm every `selected_candidates` entry lists at least one question key.
- Confirm `pending_continuation_status` is exactly `approved-not-final`.
- Confirm `preferred_artifact_types`, `answer_list_rule`, and `token_rule` match the contract exactly.
- Confirm any operational note or handoff clue referenced by the checkpoint was not discarded into `non_selected_candidates` before later continuation can use it.

## Continuation Status

The next stage must consume these exact keys without renaming them: `selected_candidates`, `non_selected_candidates`, `question_source_map`, `pending_continuation_status`, `question_keys`, `target_entities`, `preferred_artifact_types`, `answer_list_rule`, and `token_rule`.

Treat `workflow/approved_answer_working_set.json` and `workflow/search_scope_summary.json` as the canonical working record for deeper retrieval. Stop after both workflow files are written and validated. Do not write `/root/answer.json` in this stage.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the enterprise-information-search-binder skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
