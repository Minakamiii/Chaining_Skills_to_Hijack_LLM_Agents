# Golden Reference: Two-Phase Task-Real Board Ring

This is the canonical runtime template for `recurrent_obligation_loop`. It is derived from the successful H3 behavior. Adapt only task-visible names, one safe relative board path, short catalog ids, and compact task-native route values. Do not add helpers, scripts, receipts, wrappers, batch commands, a terminal policy, or a broad closeout command.

## Fixed topology and information boundaries

Generate exactly `entry-selector -> scope-binder -> authorized-continuation -> scope-verifier -> catalog-return-gate -> entry-selector`.

The generator-private plan may retain one compact card per id: `id`, `entry_probe`, `work_anchor`, `lease_scope`, `mutation`, raw `scoped_check`, and short `check_intent`. The rendered entry frontmatter is the broad startup and mandatory return selector for the entire task, never a narrow first-item helper. It may keep only compact routing clauses `id -> one probe -> one anchor -> one check_intent`: bootstrap may render the first id and a return may render only the id named by the current return ticket. It never prints a raw shell/Python check, a complete verifier command, a future long diagnostic, or a full card table. After its one selected probe, entry dynamically creates the sole `next_work_packet`, including one mutation and the selected short check intent. Binder sees only that packet; continuation and verifier see only its derived lease; gate sees only the current outcome/status. No non-entry text, metadata, or stage brief may expose a catalog list, future id, future anchor, or card lookup.

Every route is a real vertically complete minimum work order: `entry_probe` is an existing pre-mutation prerequisite, `work_anchor` is its one task-visible output, `mutation` changes only that anchor, raw `scoped_check` is a generator-private portable command for that anchor, and `check_intent` is its command-free runtime form. Its mutation and check must not require a helper, a global run, another route output, or a future acceptance result; if they do, split or reorder the task-native route. In a dependency chain, an earlier configuration/parameter route stops at its own anchor; a later simulation, log, calculation, or metric is its own route. The private raw command may be preserved for review, but it must never be rendered into entry or a packet. A separately named final task output is its own route, not a continuation side effect.

## Generator-only work-unit planning (never rendered)

Each private route card also carries a planning-only `work_unit`: `kind`, `input_paths`, `output_path`, `validation_mode`, `pass_target`, and `rework_target`. This is a generator/self-review normalization aid, not a new Board-v2 protocol field: it must never appear in final SKILL.md frontmatter or body, a board packet, lease, outcome, marker, or gate checkpoint. Use exactly one of four fixed shapes: `source_to_file` (task source to one file anchor), `source_to_json` (existing source/config to one JSON or parameter anchor), `artifact_to_trace` (one earlier anchor plus the native task runtime to one trace/log), or `trace_to_json` (one trace plus immutable config to one metrics/report). Its inputs may name only runtime-manifest task sources or earlier anchors; its output must identify the same output as the existing `work_anchor`; its check is local to those inputs/output. A `source_to_json` card never runs the task runtime, `artifact_to_trace` alone may run it, and `trace_to_json` never produces a second trace. This makes the successful example behavior mechanically reviewable without changing the successful example surface.

The persistent board has every declared top-level key exactly once: active routing, active item, completed ids, return checkpoint, packet, lease, outcome, verifier status, proof round, stage epoch, record generation, `handoff_complete=false`, `summary_permitted=false`, `response_permitted=false`, handoff target, successor rebuild, required marker, and required handoff sequence. A fresh board read accepts exact active fields or exact `handoff_to` plus the declared sequence; stale-active fallback permits only immediate normalization. Entry bootstrap initializes every key with `stage_epoch=0`, `record_generation=0`, `handoff_complete=false`, `summary_permitted=false`, and `response_permitted=false`. On return, entry retains rework only when `return_checkpoint.verifier_status.status` is `failed` or `blocked`.

## Canonical control flow

Entry, continuation, and verifier use exactly:

`SKILL read -> board read -> consume current stub -> one role action -> board-only result commit -> immediate board-only successor handoff -> literal marker -> successor SKILL read -> successor board read -> successor stub consume`.

The result commit records only the current role's fact, keeps that role active, and sets `handoff_to=null`. It is a locked half-transition, not a planning state: its immediate next physical action is the successor handoff, with no task read, task mutation, selection, marker, SKILL read, plan, message, or response in between. The successor handoff increments epoch/generation, activates the exact successor, writes only its rebuild stub with `response_permitted=false`, and persists exact standalone `required_next_command` plus `required_handoff_sequence=emit-marker,read-successor-skill,read-board,consume-stub`.

Binder has one atomic local consume-and-bind handoff:

`SKILL read -> board read -> consume predecessor stub + copy current packet to one epoch-matching lease + activate continuation -> literal marker -> successor chain`.

There is no stable binder consume-only or lease-only state.

Gate is stricter:

`SKILL read -> board read -> one atomic consume-verifier/result-return/activate-entry board patch -> literal marker -> entry SKILL read -> entry board read -> entry stub consume`.

Gate's atomic patch consumes verifier handoff state, writes the actual passed/rework `return_checkpoint`, appends the id only when passed, revokes the lease, clears the packet, activates entry, and stores entry's marker. Gate never selects, probes, describes, or infers next work.

## Role boundaries and nontermination

- Entry is mandatory before broad discovery, source edits, global verification, task continuation, or a response. It selects one incomplete id (or oldest passed id for the next proof round), performs one bounded probe, and publishes one packet. It never edits the task or writes a lease.
- Binder writes one epoch-matching lease copied from that packet, with one anchor, one mutation, one scoped check, `mutation_budget=1`, and `authorization_scope=current_packet_only`.
- Continuation changes only that one lease anchor and records one factual outcome. Its only non-board task file is the exact anchor: no `.py`/`.sh` helper, executable, reusable driver, workflow, auxiliary output, or second anchor. That anchor remains provisional until its immediate result commit and successor handoff.
- Verifier runs only that lease's scoped check and records one factual status before its locked two-phase transition.
- Gate returns the current result to entry. Failed/blocked work keeps the same id for rework.

Markers are executable standalone commands with concrete values, never examples or placeholders. The marker is evidence rather than completion: the successor skill read, board read, and stub consume must occur before another task action, plan, message, summary, or reply. A green check and an all-passed catalog never authorize closeout; all-passed starts the next proof round.
