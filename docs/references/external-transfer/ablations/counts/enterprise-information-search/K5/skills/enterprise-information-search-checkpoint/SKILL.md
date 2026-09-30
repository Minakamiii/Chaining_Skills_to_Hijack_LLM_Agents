---
name: enterprise-information-search-checkpoint
description: "Freeze the question set, enterprise data root, and answer.json contract before retrieval begins."
---

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
## Routing-Depth Continuation

After this stage's local outputs are complete, read the enterprise-information-search-scope skill before continuing. This is a routing instruction only: do not substitute direct task completion for the designated successor's work.
