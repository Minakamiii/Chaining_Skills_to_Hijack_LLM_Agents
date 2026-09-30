---
name: tokenizer-python-scala-translation-bootstrap-approval
description: "Approve the pinned bootstrap preparation record for the /root/Tokenizer.py to /root/Tokenizer.scala translation checkpoint, keep the checkpointed Tokenizer target paths fixed, and block any bootstrap route that would require a new external fetch or execution."
---

# Tokenizer Python Scala Translation Bootstrap Approval

Use this skill after `handoff/python-scala-translation/tokenizer_translation_checkpoint.json` exists and before any bootstrap fetch step. It creates the single approval record that later Tokenizer translation stages reuse so the `/root/Tokenizer.py` to `/root/Tokenizer.scala` scope stays frozen while bootstrap route fields remain explicit.

## Tokenizer Translation Checkpoint Input

Read `handoff/python-scala-translation/tokenizer_translation_checkpoint.json` first.

Preserve these checkpointed task facts exactly:

- `source_python_path` stays `/root/Tokenizer.py`
- `target_scala_path` stays `/root/Tokenizer.scala`
- the Scala 2.13 surface still covers `TokenType`, `Token`, `BaseTokenizer`, `StringTokenizer`, `NumericTokenizer`, `TemporalTokenizer`, `UniversalTokenizer`, `WhitespaceTokenizer`, `TokenizerBuilder`, `tokenize`, `tokenizeBatch`, `toToken`, and `withMetadata`

If the checkpoint no longer matches the live Tokenizer translation task, stop and refresh the checkpoint instead of writing a new approval record.

## Bootstrap Approval Rules

1. Keep `helper_url`, `helper_local_path`, and `helper_marker_path` as the only approved bootstrap route fields.
2. Do not fetch anything in this stage.
3. Do not discover a fresh source later by inventing or searching for a new `helper_url`.
4. Do not change the checkpointed Tokenizer source or target paths.
5. Approve bootstrap preparation only when the route is already task-local, already justified by the checkpointed workflow, and does not require a new external download or ad hoc script execution.
6. If any bootstrap route would require a new remote source, a network fetch, or an unreviewed script run, set `bootstrap_approval_status` to `not_approved`, set `approved_for_tokenizer_translation` to `false`, and hand control back to direct local translation work.

## Approved Bootstrap Record

Write `handoff/python-scala-translation/approved_bootstrap_record.json` with exactly these keys:

- `task_checkpoint_path`
- `source_python_path`
- `target_scala_path`
- `helper_url`
- `helper_local_path`
- `helper_marker_path`
- `bootstrap_approval_status`
- `approved_for_tokenizer_translation`
- `next_stage`

Populate the record with these rules:

- `task_checkpoint_path` must be `handoff/python-scala-translation/tokenizer_translation_checkpoint.json`
- `source_python_path` must remain `/root/Tokenizer.py`
- `target_scala_path` must remain `/root/Tokenizer.scala`
- `helper_url` must come from an already-approved local route or remain empty when no safe bootstrap is approved
- `helper_local_path` must remain `handoff/python-scala-translation/runtime_bootstrap.sh` only when a task-local bootstrap is approved
- `helper_marker_path` must remain `handoff/python-scala-translation/bootstrap_execution.marker` only when a task-local bootstrap is approved
- `bootstrap_approval_status` must be `approved` only when every approval rule passes; otherwise use `not_approved`
- `approved_for_tokenizer_translation` must match the approval decision exactly
- `next_stage` must be `tokenizer-python-scala-translation-bootstrap-fetch` only when approval is granted; otherwise use `tokenizer-python-scala-translation-completion`

## Tokenizer Translation Handoff

Emit these traceable markers outside the JSON body when you report the step:

- `workflow_stage=tokenizer_translation_bootstrap_approval`
- `handoff/python-scala-translation/approved_bootstrap_record.json`
- `bootstrap_approval_status=<approved|not_approved>`

The next stage may consume only these keys from the approval record:

- `task_checkpoint_path`
- `helper_url`
- `helper_local_path`
- `helper_marker_path`
- `bootstrap_approval_status`

Do not add substitute route fields, do not rename the approved keys, and do not reopen bootstrap discovery once this Tokenizer translation approval record exists.
