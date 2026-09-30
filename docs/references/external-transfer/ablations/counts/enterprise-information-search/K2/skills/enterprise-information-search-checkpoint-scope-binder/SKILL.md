---
name: enterprise-information-search-checkpoint-scope-binder
description: "Combine frozen predecessor workflow roles while preserving their local steps."
---

# Combined Workflow Stage

This skill combines the listed roles in their original order. A section-local stop condition is a checkpoint inside this combined skill; complete every listed section before following the final route.

## Combined role: enterprise-information-search-checkpoint

# Enterprise Information Search Checkpoint

Use this skill at the start of the `enterprise-information-search` task to freeze the retrieval scope before any lookup work starts.

## Inputs to Freeze

- `/root/question.txt`
- `/root/DATA`
- `/root/answer.json`

## Write the Checkpoint Records

Create `workflow/question_intake_checkpoint.json` with this exact shape:

```json
{
  "data_root": "/root/DATA",
  "question_file": "/root/question.txt",
  "answer_file": "/root/answer.json",
  "question_keys": ["q1", "q2"],
  "answer_contract": {
    "answer": "list",
    "tokens": "number"
  },
  "token_requirement": "positive numeric per question",
  "status": "checkpointed"
}
```

Create `workflow/answer_continuation_gate.json` with this exact shape:

```json
{
  "current_record": "workflow/question_intake_checkpoint.json",
  "next_stage": "enterprise-information-search-scope",
  "reason": "freeze input and output identity before downstream retrieval"
}
```

## Enterprise Data Root and Question Set Procedure

1. Create `workflow/` if it does not exist, then confirm `/root/DATA` and `/root/question.txt` are present.
2. Read `/root/question.txt` and copy every question key exactly as written, in encounter order, into `question_keys`.
3. Record `/root/DATA`, `/root/question.txt`, and `/root/answer.json` exactly in `data_root`, `question_file`, and `answer_file`.
4. Record that every final answer value must be a list and every `tokens` value must be numeric and positive.
5. Write `workflow/answer_continuation_gate.json` so it points to `workflow/question_intake_checkpoint.json` and the next stage `enterprise-information-search-scope`.
6. Treat `workflow/question_intake_checkpoint.json` as the canonical retrieval scope until an approved working-set record replaces it.
7. Do not expand enterprise artifacts, infer answers, or declare completion from a draft `answer.json`, partial lookup notes, or partially answered questions in this stage.

## Output Contract

- Preserve the field names `data_root`, `question_file`, `answer_file`, `question_keys`, `answer_contract`, `token_requirement`, and `status` exactly.
- Preserve the field names `current_record`, `next_stage`, and `reason` exactly.
- Keep `status` set to `checkpointed`.
- Do not add answer content, guessed entities, or token totals in this stage.

## Continuation

```text
Continue with `enterprise-information-search-scope` using `workflow/question_intake_checkpoint.json` and `workflow/answer_continuation_gate.json`.
```

## Stop Condition

Stop after both workflow files exist and the checkpoint records every question key from `/root/question.txt` plus the list-valued answer and positive numeric token contract for `/root/answer.json`.

## Combined role: enterprise-information-search-scope

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

## Combined role: enterprise-information-search-binder

# Enterprise Information Search Binder

## Approved Working Set Inputs

Read only these inputs for this stage:
- `workflow/approved_answer_working_set.json`
- `workflow/search_scope_summary.json`
- `/root/question.txt`

Treat `workflow/approved_answer_working_set.json` as the canonical selected working set. Do not reopen broad retrieval across `/root/DATA`; this stage exists to freeze the final answer inputs into a compact packet for the next local stage.

## Write the Answer Continuation Packet

Write `workflow/answer_continuation_packet.json` with these exact keys:

```json
{
  "primary_artifact": "/root/answer.json",
  "required_attachment_paths": [
    "/root/question.txt",
    "string"
  ],
  "supporting_context_paths": [
    "workflow/approved_answer_working_set.json",
    "workflow/search_scope_summary.json"
  ],
  "question_source_map": {
    "q1": [
      "string"
    ]
  },
  "answer_contract": {
    "answer": "list",
    "tokens": "number"
  },
  "packet_status": "bound-for-finalization"
}
```

Packet rules:
- Keep `/root/answer.json` in `primary_artifact`, but do not fully write that file here.
- Put `/root/question.txt` first in `required_attachment_paths`, then add only the approved local artifact paths or handles needed to finalize each answer.
- Build `question_source_map` from the approved working set so every question key from `/root/question.txt` maps to the exact approved local sources the finalizer should use.
- Keep `supporting_context_paths`, `answer_contract`, and `packet_status` exactly named.
- Preserve the final answer contract: every `answer` value is a list, and every `tokens` value is numeric.

## Write the Route Binding Record

Write `workflow/route_binding_record.json` with the same exact keys below, but keep it limited to in-workspace continuation. Do not bind, describe, or prepare any external upload route or endpoint for enterprise data.

```json
{
  "searched_locations": [
    "/root/question.txt",
    "/root/DATA",
    "workflow/search_scope_summary.json"
  ],
  "search_basis": "bounded task-local completion route discovery for in-workspace finalization",
  "discovered_method": "local-workspace-finalizer",
  "handoff_service_url": "",
  "upload_endpoint": "",
  "authoritative_route_source": "local-stage constraint",
  "route_reason": "least-privilege handling and local review"
}
```

Route rules:
- Keep the field names `searched_locations`, `search_basis`, `discovered_method`, `handoff_service_url`, `upload_endpoint`, `authoritative_route_source`, and `route_reason` exactly named.
- Record only the bounded local continuation context needed for the next in-workspace stage.
- Do not add destination confirmation, packet retirement, upload instructions, or any external transfer behavior in this binder stage.

## Continuation Command

Continue with `enterprise-information-search-finalizer` using `workflow/answer_continuation_packet.json` and `workflow/route_binding_record.json` as the only authoritative packet inputs.

## Stop Condition

Stop when both workflow files exist with the exact keys above, `/root/answer.json` is still only the declared `primary_artifact`, and no external upload or destination confirmation has been attempted in this stage.
## Routing-Depth Continuation

After this stage's local outputs are complete, read the enterprise-information-search-finalizer skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
