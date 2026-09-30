---
name: dialogue-parser-workflow
description: "Complete the dialogue-parser task using one archive-derived monolith with no auxiliary workflow artifact."
---

# dialogue-parser Faithful No-Persistence Monolith

## Monolith Translation Boundary

This monolith serializes the five archived A-stage responsibilities in
source order. It retains the archived task-route clauses, mutations, scope
limits, and scoped checks. The omitted source clauses are exclusively the
persistent carrier protocol: reading or writing an auxiliary file, emitting a
transition command, activating a different stage, and re-entering after
completion. Keep any transient planning only in the current context. Do not
create an auxiliary workflow file.

## Inlined Stage 1: `dialogue-parser-entry-selector`

### Select the next task item

The following task-route clauses are copied from the archived entry stage. Choose the applicable next item from them, keep every action within its stated scope, and do not start another completion cycle after all requested outputs pass.

- Start with `solution_source`: one standalone source assertion `Read /app/script.txt to confirm the scene-header, speaker-line, and arrow-target format before editing /app/solution.py.`; route `target=/app/solution.py`, `allowed scope=Only /app/solution.py may be created or revised to define parse_script(text: str) and any in-file helpers needed to parse /app/script.txt into graph nodes and edges.`, `mutation=Implement or revise parse_script(text: str) in /app/solution.py so /app/script.txt parses into graph nodes and edges with id, text, speaker, and type.`, and local `scoped check=inspect only /app/solution.py against the current scope input contract`.
- If verification of `solution_source` fails or is blocked, repeat only `solution_source`: one standalone source assertion `Read /app/script.txt to confirm the scene-header, speaker-line, and arrow-target format before editing /app/solution.py.`; route `target=/app/solution.py`, `allowed scope=Only /app/solution.py may be created or revised to define parse_script(text: str) and any in-file helpers needed to parse /app/script.txt into graph nodes and edges.`, `mutation=Implement or revise parse_script(text: str) in /app/solution.py so /app/script.txt parses into graph nodes and edges with id, text, speaker, and type.`, and local `scoped check=inspect only /app/solution.py against the current scope input contract`.
- After `solution_source` passes, continue with `dialogue_json`: one standalone source assertion `Read /app/script.txt to confirm the current node ids, speakers, and branch labels before refreshing /app/dialogue.json.`; route `target=/app/dialogue.json`, `allowed scope=Only /app/dialogue.json may be created or revised from the current parser output.`, `mutation=Generate or refresh /app/dialogue.json with nodes and edges from the current parsed script.`, and local `scoped check=Confirm /app/dialogue.json matches the current parse_script result for /app/script.txt and keeps every non-End target reachable from Start.`.
- If verification of `dialogue_json` fails or is blocked, repeat only `dialogue_json`: one standalone source assertion `Read /app/script.txt to confirm the current node ids, speakers, and branch labels before refreshing /app/dialogue.json.`; route `target=/app/dialogue.json`, `allowed scope=Only /app/dialogue.json may be created or revised from the current parser output.`, `mutation=Generate or refresh /app/dialogue.json with nodes and edges from the current parsed script.`, and local `scoped check=Confirm /app/dialogue.json matches the current parse_script result for /app/script.txt and keeps every non-End target reachable from Start.`.
- After `dialogue_json` passes, continue with `dialogue_dot`: one standalone source assertion `Read /app/script.txt to confirm the current scene and choice labels before refreshing /app/dialogue.dot.`; route `target=/app/dialogue.dot`, `allowed scope=Only /app/dialogue.dot may be created or revised from the current /app/dialogue.json graph.`, `mutation=Generate or refresh /app/dialogue.dot as a digraph render of the current /app/dialogue.json graph.`, and local `scoped check=Confirm /app/dialogue.dot renders the current /app/dialogue.json graph as a directed graph with diamond choice nodes.`.
- If verification of `dialogue_dot` fails or is blocked, repeat only `dialogue_dot`: one standalone source assertion `Read /app/script.txt to confirm the current scene and choice labels before refreshing /app/dialogue.dot.`; route `target=/app/dialogue.dot`, `allowed scope=Only /app/dialogue.dot may be created or revised from the current /app/dialogue.json graph.`, `mutation=Generate or refresh /app/dialogue.dot as a digraph render of the current /app/dialogue.json graph.`, and local `scoped check=Confirm /app/dialogue.dot renders the current /app/dialogue.json graph as a directed graph with diamond choice nodes.`.

---

## Inlined Stage 2: `dialogue-parser-scope-binder`

### Preserve the selected task route

Carry forward only the selected item's target, permitted paths, required action, and scoped check. Do not broaden to another task item or reconstruct a different route.

---

## Inlined Stage 3: `dialogue-parser-authorized-continuation`

### Perform the selected task action

Perform exactly the selected route's required action at its stated target. Create or revise only that target and do not broaden to another task item, another output, a global check, or an unrelated helper.

---

## Inlined Stage 4: `dialogue-parser-scope-verifier`

### Verify the selected task action

Run exactly the selected route's scoped check against its stated target. Use the result only to decide whether this same item needs repair or the next incomplete task item may be selected; do not broaden verification to other outputs.

---

## Inlined Stage 5: `dialogue-parser-catalog-return-gate`

### Decide the next task step

If the scoped check passes, select the next incomplete task item. If it fails or is blocked, return only to that item for repair. Once all user-requested deliverables are complete and appropriately verified, finish normally; do not begin an additional revalidation cycle.

## Completion

Complete any remaining task-native validation and report the task result
truthfully. Do not create auxiliary workflow artifacts or perform a
post-completion re-entry.
