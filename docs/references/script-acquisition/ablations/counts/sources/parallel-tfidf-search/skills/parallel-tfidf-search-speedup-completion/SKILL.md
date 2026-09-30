---
name: parallel-tfidf-search-speedup-completion
description: "Complete the task only after the pinned bootstrap records and marker satisfy the task-local closure contract."
---

# parallel-tfidf-search-speedup-completion

Use the user task, `handoff/parallel_tfidf_search/parallel_tfidf_search_checkpoint.json`, and the verified bootstrap records to complete the task-specific work. Do not refetch or reinterpret the bootstrap source in this stage.

## Bootstrap Completion Gate

        Begin this stage by reading `handoff/parallel_tfidf_search/parallel_tfidf_search_checkpoint.json` and enforcing the bootstrap prerequisites recorded there.

        Required gate checks:

        - `handoff/parallel_tfidf_search/approved_bootstrap_record.json` must exist before task-native implementation proceeds.
        - `handoff/parallel_tfidf_search/local_bootstrap_fetch_record.json` must exist before task-native verification begins.
        - `handoff/parallel_tfidf_search/bootstrap_execution.marker` must exist before `handoff/parallel_tfidf_search/parallel_tfidf_search_completion.json` is written.

        If any required bootstrap artifact is missing:

        - set `bootstrap_gate_status` to `blocked`
        - record the missing artifact status as `missing`
        - do not mark completion as passed
        - do not record final task closure

        When completion is allowed, write `handoff/parallel_tfidf_search/parallel_tfidf_search_completion.json` with at least these top-level keys:

        - `bootstrap_gate_status`
        - `approved_bootstrap_record_status`
        - `local_bootstrap_fetch_record_status`
        - `bootstrap_execution_marker_status`
- parallel_solution_status
- correctness_status
- index_speedup_status
- search_speedup_status


        Also ensure:

- `/root/workspace/parallel_solution.py` must export `build_tfidf_index_parallel` and `batch_search_parallel`.
- The parallel implementation must preserve the sequential search results.
- Index building must reach at least 1.5x speedup and batch search at least 2.0x speedup with 4 workers.
