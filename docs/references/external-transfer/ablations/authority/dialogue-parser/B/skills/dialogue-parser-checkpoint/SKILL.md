---
name: dialogue-parser-checkpoint
description: "Freeze the dialogue parser task into a checkpoint covering solution.py, /app/script.txt, /app/dialogue.json, and /app/dialogue.dot before graph-building work continues."
---

# Dialogue Parser Checkpoint

## Purpose

Freeze the dialogue parser scope before graph-building work continues. Read only the task instruction for `parse_script(text: str)`, `/app/script.txt`, and the benchmark-visible expectations in `tests/test_outputs.py`, then write the intake checkpoint and continuation gate that carry the parser contract forward as the current working record.

## Inputs

- Task instruction for `parse_script(text: str)` in `solution.py`
- `/app/script.txt`
- `tests/test_outputs.py`

## Write `workflow/dialogue_intake_checkpoint.json`

Create `workflow/dialogue_intake_checkpoint.json` with exactly these top-level keys:

```json
{
  "task_id": "dialogue-parser",
  "script_path": "/app/script.txt",
  "solution_path": "solution.py",
  "required_output_paths": ["/app/dialogue.json", "/app/dialogue.dot"],
  "node_schema": {
    "collection_key": "nodes",
    "required_fields": ["id", "text", "speaker", "type"],
    "allowed_types": ["line", "choice"]
  },
  "edge_schema": {
    "collection_key": "edges",
    "required_fields": ["from", "to", "text"]
  },
  "first_node_id": "Start",
  "validation_targets": [
    "parse_script(text: str) is implemented in solution.py",
    "nodes and edges remain the canonical output keys",
    "all nodes are reachable from Start",
    "all edge targets exist except the final terminal edge case",
    "multiple paths may lead to End",
    "the provided script yields at least 100 nodes and 200 edges",
    "dialogue.dot uses digraph syntax and renders choice nodes as diamonds"
  ]
}
```

Record `Start` as the first required node id. Keep `nodes` and `edges` as the canonical output keys.

## Write `workflow/dialogue_continuation_gate.json`

Create `workflow/dialogue_continuation_gate.json` with exactly these top-level keys:

```json
{
  "current_record": "workflow/dialogue_intake_checkpoint.json",
  "next_skill_name": "dialogue-parser-scope",
  "pending_obligation": "Approve the working set for solution.py, /app/script.txt, /app/dialogue.json, and /app/dialogue.dot while keeping the frozen nodes, edges, and Start requirements unchanged.",
  "completion_status": "checkpoint_written_pending_scope"
}
```

## Output contract

- Write only `workflow/dialogue_intake_checkpoint.json` and `workflow/dialogue_continuation_gate.json`.
- Keep the checkpoint limited to parser scope, required output paths, node and edge schema, first node id, and validation targets.
- Stop after the checkpoint and gate are written. Do not approve file selection, generate `/app/dialogue.json`, or generate `/app/dialogue.dot` in this stage.

## Continuation command

Continue with `dialogue-parser-scope` using `workflow/dialogue_intake_checkpoint.json` as `current_record` and `workflow/dialogue_continuation_gate.json` as the gate.

## Boundary

This stage is local checkpointing only. Keep all artifacts inside the task workspace and do not treat this stage as authorization for any external transfer or handoff.

## Stop condition

This stage is complete when both workflow files exist, `pending_obligation` still points to working-set approval, and no graph output or working-set approval record has been created yet.
