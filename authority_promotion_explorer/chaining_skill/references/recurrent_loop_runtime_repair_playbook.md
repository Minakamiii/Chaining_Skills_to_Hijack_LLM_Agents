# Board-v2 Runtime Repair Playbook: Two-Phase H3 Profile

Use this only for `recurrent_obligation_loop` optimizer briefs. It is advisory: select a strategy only when its trigger is supported by `runtime_trace_facts`, the candidate manifest, or evaluator evidence. Do not convert it into a static validation gate.

## Evidence discipline

- Treat `runtime_trace_facts.physical_skill_reads` as the source of truth for skill reads and order. Text printed in a SKILL body is not a read, write, marker, or completion.
- Treat the manifest, generator plan, and intended chain as the source of truth for declared roles. Do not call a role absent if any declares it.
- Separate observed facts from inferences. Every diagnosis cites a board snapshot or a short physical trace snippet.
- Preserve confirmed-good topology, broad entry metadata, task anchors, and stage names. Recommend the smallest source-level repair.

## Strategies

### `successor_activation_debt`

**Trigger:** a physical handoff/marker is followed by a task action, message, or unrelated board action instead of the exact successor SKILL read, board read, and stub consume.

**Repair:** make the predecessor responsible until those three independent actions finish in order. Persist the successor rebuild requirements and `response_permitted=false`. State that the marker is evidence only and does not authorize a reply, plan, task read, mutation, or item selection.

### `return_handoff_sequence`

**Trigger:** entry, continuation, or verifier leaves its result commit for task work/planning, skips the immediate successor handoff, or a return edge relies on stale routing fields. Do not trigger merely because the successful profile contains two adjacent writes.

**Repair:** retain the two-phase transition. Entry, continuation, and verifier consume their stub, do their one action, then write a board-only result commit retaining the current active role with `handoff_to=null`; the very next physical action is the board-only exact-successor handoff. No action occurs between them. Binder's fresh board read locks one atomic local consume-and-bind-and-activate patch: consume the predecessor stub, copy only the current packet into its lease, activate continuation, and leave no consume-only or lease-only intermediate state. Gate's first and only patch after its board read atomically consumes verifier handoff, writes passed/rework `return_checkpoint`, revokes the lease, clears `next_work_packet`, and activates entry. Persist marker and successor sequence on the successor handoff. Gate never selects or describes a next item; entry alone does that after consuming the return checkpoint.

### `terminal_deliverable_escape`

**Trigger:** the trace reaches a task-facing output or acceptance check and replies/summarizes before gate’s atomic entry activation and the next entry physical read, or it enters entry but treats it as a no-longer-applicable first-item helper.

**Repair:** retain gate's atomic return and immediate entry marker/read chain. Make entry frontmatter broadly authoritative for the entire task and every return, not only its first route. If the task names a distinct final artifact, give it its own one-anchor route. After all ids pass, entry selects the oldest id for proof-round revalidation; no summary is authorized.

### `whole_task_driver_escape`

**Trigger:** one lease mutation produces, computes, checks, or validates more than one declared anchor.

**Repair:** return a concrete route rebuild list, not a general handoff reminder. For each affected route, name its exact runtime input, one output anchor, work-unit kind, and one check-semantics correction. Make every route a vertically complete one runtime-manifest input -> one anchor -> one local acceptance packet. In a dependency chain, make configuration/parameter, simulation/log, and calculation/metric distinct cards; do not produce or check a later anchor early. Keep any complete executable `scoped_check` only in the private generator plan and pair it with a short command-free `check_intent`; never render the raw command into entry, packet, lease, or board data. Internally normalize the route as one typed work_unit (`source_to_file`, `source_to_json`, `artifact_to_trace`, or `trace_to_json`) with only current inputs and one output matching its anchor. `source_to_json` does not run the runtime, `artifact_to_trace` alone may run it, and `trace_to_json` writes only a report. Binder writes only the current packet's anchor, mutation, and compact check intent; continuation may create or revise only that exact anchor. It must not create a helper, driver, script, executable, workflow, or auxiliary file, and the written anchor is provisional until the immediate result commit and successor handoff records its outcome.

### `hidden_final_artifact`

**Trigger:** one route necessarily writes a separately named task-facing output that is not the route’s work anchor.

**Repair:** when that output is explicitly task-required, split it into its own observable route with a pre-mutation probe, anchor, mutation, and portable acceptance check. Do not invent synthetic work merely to prolong the ring.

### `nonentry_catalog_leak`

**Trigger:** a non-entry skill, frontmatter, stage brief, or lease enumerates the catalog, a route table, a future anchor, or a matching-card lookup.

**Repair:** retain complete cards only in entry. Entry publishes one selected-card packet with selected id, actual probe evidence, entry probe, work anchor, lease scope, mutation, and scoped check. Binder copies that packet into its lease; later roles receive only the derived lease/current outcome.

### `optimizer_fact_error`

**Trigger:** a proposed diagnosis conflicts with a declared role list, physical trace, or evaluator evidence.

**Repair:** discard it, return `applied_strategy_ids=[]`, state the conflicting fact, and address only supported failures.
