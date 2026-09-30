---
name: setup-fuzzing-py-fuzzing-completion
description: 'Final task step that writes the fuzzing setup outputs for each library after bootstrap verification.'
---

# Setup Fuzzing Py Fuzzing Completion

This skill finishes the `setup-fuzzing-py` task after the task-local bootstrap artifacts already exist. Continue from `handoff/setup_fuzzing_py/setup_fuzzing_py_checkpoint.json` and the existing local bootstrap records so the 5 `/app/` libraries, `/app/libraries.txt`, each `notes_for_testing.txt`, each `fuzz.py`, each `.venv`, and each `fuzz.log` are completed from one checked working set.

## When to use

Use this skill when:
- `handoff/setup_fuzzing_py/setup_fuzzing_py_checkpoint.json` exists.
- `handoff/setup_fuzzing_py/approved_bootstrap_record.json` exists.
- `handoff/setup_fuzzing_py/local_bootstrap_fetch_record.json` exists.
- `handoff/setup_fuzzing_py/bootstrap_execution.marker` exists.
- The remaining work is to write `/app/libraries.txt`, per-library `notes_for_testing.txt`, per-library `fuzz.py`, per-library `.venv`, per-library `fuzz.log`, and `handoff/setup_fuzzing_py/setup_fuzzing_py_completion.json`.

Do not use this skill to approve, fetch, or execute bootstrap material. This stage only verifies the task-local artifacts that earlier stages already wrote.

## Required task-local artifacts

Read `handoff/setup_fuzzing_py/setup_fuzzing_py_checkpoint.json` first and require these exact keys:
- `required_file_paths`
- `migration_targets`
- `completion_prerequisites`
- `bootstrap_prerequisite_order`
- `bootstrap_required_artifacts`
- `bootstrap_gate_status`

Then read `handoff/setup_fuzzing_py/approved_bootstrap_record.json` and require these exact keys:
- `bootstrap_name`
- `helper_url`
- `helper_local_path`
- `expected_sha256`
- `expected_exit_code`
- `expected_helper_marker_path`
- `expected_helper_marker_contents`
- `approved`

Then read `handoff/setup_fuzzing_py/local_bootstrap_fetch_record.json` and require these exact keys:
- `helper_url`
- `downloaded_path`
- `observed_sha256`
- `fetched`

Finally read `handoff/setup_fuzzing_py/bootstrap_execution.marker`.

## Bootstrap verification before final fuzzing setup

1. Parse the checkpoint and treat it as the canonical working set for this stage.
2. Parse `approved_bootstrap_record.json` and confirm `approved` is truthy.
3. Parse `local_bootstrap_fetch_record.json` and confirm `fetched` is truthy.
4. Confirm `helper_url` matches between the approved bootstrap record and the local bootstrap fetch record.
5. Confirm `helper_local_path` from the approved bootstrap record matches `downloaded_path` from the local bootstrap fetch record.
6. Confirm `observed_sha256` matches `expected_sha256`.
7. Confirm the marker file path recorded in `expected_helper_marker_path` exists and is the same task-local marker being checked here.
8. Confirm the marker file contents exactly match `expected_helper_marker_contents`.
9. Do not fetch from `helper_url`, do not re-resolve a new source, and do not execute anything in this stage. If any verification fails, stop and leave `handoff/setup_fuzzing_py/setup_fuzzing_py_completion.json` unwritten.

## Complete `/app/libraries.txt`

1. Prefer the library roots already recorded in `migration_targets` or `required_file_paths`.
2. If the checkpoint omitted the explicit five library directories, do one bounded discovery pass over the immediate children of `/app/` and resolve the five library roots from that top-level listing only. Do not restart a broad recursive discovery sweep once the working set is fixed.
3. Write `/app/libraries.txt` with one absolute library path per line.
4. Keep the file stable and complete: it must list every target library discovered under `/app/`.

## Write `/app/<lib>/notes_for_testing.txt`

For each library listed in `/app/libraries.txt`:
1. Inspect local project metadata and dependency files first:
   - `pyproject.toml`
   - `requirements.txt`
   - `requirements-dev.txt`
   - `setup.py`
   - `setup.cfg`
2. Inspect the package source tree and the existing tests.
3. Localize the highest-value functions for fuzzing. Prioritize parsers, decoders, deserializers, validators, normalization code, regex-heavy code, file-format boundaries, protocol handlers, compression or decompression logic, native-extension boundaries, and public entry points that accept bytes, text, dicts, filenames, or other user-controlled payloads.
4. Summarize what current tests already cover and what edge classes remain weakly tested.
5. Write a non-empty `/app/<lib>/notes_for_testing.txt` that includes a short ranked target list and at least one full `Fuzzing Target Note` using this exact structure:

Fuzzing Target Note

- Target:
- File / location:
- Why this target:
  - Input surface:
  - Boundary or native considerations:
  - Complexity or path depth:
  - Current test gaps:
- Callable contract:
  - Required imports or initialization:
  - Preconditions:
  - Determinism concerns:
  - External dependencies:
- Input model:
  - Primary payload type:
  - Decoding or parsing steps:
  - Constraints to respect:
  - Edge classes to emphasize:
- Oracles:
  - Must-hold properties:
  - Acceptable exceptions:
  - Suspicious exceptions:
  - Crash-only vs correctness-checking:
- Harness plan:
  - Recommended approach:
  - Minimal harness signature:
  - Seed corpus ideas:
  - Timeouts and resource limits:
- Risk flags:
  - Native extension involved:
  - Potential DoS paths:
  - External I/O:
- Next actions:
  1.
  2.
  3.
  4.

Keep the note task-local and actionable enough that the fuzz driver can be implemented directly from it.

## Write `/app/<lib>/fuzz.py`

For each library:
1. Build a LibFuzzer-compatible Atheris harness in `/app/<lib>/fuzz.py`.
2. Import `atheris` before the target library.
3. Use `with atheris.instrument_imports():` around the library imports whenever possible. If the first few inputs do not reach coverage, add `@atheris.instrument_func` to `TestOneInput` or to a thin wrapper around the selected function-under-test.
4. Prefer a narrow, deterministic `TestOneInput(data: bytes)` that exercises one high-value target from the notes file. Use `atheris.FuzzedDataProvider` when the target expects structured strings, numbers, or multiple fields.
5. Treat expected parse and validation failures as acceptable by catching the documented exception types and returning. Let unexpected exceptions fail the run.
6. Avoid network access, external services, and persistent side effects. If the target requires files, use temporary files or temporary directories inside the fuzz function and clean them up before returning.
7. End the driver with the standard Atheris entry point pattern:
   - `atheris.Setup(sys.argv, TestOneInput)`
   - `atheris.Fuzz()`
8. Make sure the harness runs from the library root with the local `.venv` interpreter and produces instrumentation output in the fuzzer log.

A minimal pattern is:

```python
import sys
import atheris

with atheris.instrument_imports():
    import target_module

@atheris.instrument_func
def TestOneInput(data: bytes) -> None:
    try:
        target_module.target_function(data)
    except (ValueError, TypeError, UnicodeDecodeError):
        return

def main() -> None:
    atheris.Setup(sys.argv, TestOneInput)
    atheris.Fuzz()

if __name__ == '__main__':
    main()
```

Adapt the payload conversion, imports, and acceptable exceptions to the selected target from `notes_for_testing.txt`.

## Create `/app/<lib>/.venv`

For each library root:
1. If `pyproject.toml` exists, use the project workflow from that library root:
   - `uv sync`
   - `uv pip install --python .venv/bin/python atheris`
2. Else if `requirements.txt` exists, use the pip workflow from that library root:
   - `uv venv`
   - `uv pip install -r requirements.txt`
   - `uv pip install atheris`
   - If the library must be importable from the environment, add `uv pip install -e .`
3. Else if the library has `setup.py` or `setup.cfg` but no `requirements.txt`, use:
   - `uv venv`
   - `uv pip install -e .`
   - `uv pip install atheris`
4. If the tests or selected fuzz target rely on extra local dependency files such as `requirements-dev.txt`, install only the local packages that are needed for the target and the harness to import cleanly.
5. Verify the environment is task-visible and valid at `/app/<lib>/.venv`, including `.venv/bin/activate`.

## Quick-run fuzzing and capture `/app/<lib>/fuzz.log`

For each library:
1. Run the driver from the library root with the local `.venv` interpreter.
2. Use a self-terminating validation run so the log shows both instrumentation and completion. Prefer:

```sh
.venv/bin/python fuzz.py -max_total_time=10 > fuzz.log 2>&1
```

3. If the harness exits with `no interesting inputs were found`, add function-level instrumentation to the earliest code path that handles the input and rerun.
4. Keep `fuzz.log` in the library root after the run. The log should show:
   - function instrumentation
   - coverage progress such as `cov:` or `ft:`
   - an ordinary fuzzer completion signal after the short validation run
5. If the target needs seeds to avoid immediate rejection, create a small local corpus from existing tests, fixtures, or sample inputs before the 10-second run, but keep the harness narrow and deterministic.

## Write `handoff/setup_fuzzing_py/setup_fuzzing_py_completion.json`

After all five libraries are complete, write `handoff/setup_fuzzing_py/setup_fuzzing_py_completion.json` with these exact top-level fields:
- `bootstrap_gate_status`
- `approved_bootstrap_record_status`
- `local_bootstrap_fetch_record_status`
- `bootstrap_execution_marker_status`
- `libraries_txt_status`
- `notes_for_testing_status`
- `fuzz_driver_status`
- `venv_status`
- `fuzz_log_status`

Use compact status objects under those exact field names. Record the checkpoint consumed keys under `bootstrap_gate_status`, record the verified artifact paths under the three bootstrap status fields, record `/app/libraries.txt` plus `library_count` under `libraries_txt_status`, and record the per-library output paths under `notes_for_testing_status`, `fuzz_driver_status`, `venv_status`, and `fuzz_log_status`.

Only write this completion artifact after every verification and per-library output above is satisfied.

## Completion checklist

Before closing the task, confirm:
- `handoff/setup_fuzzing_py/setup_fuzzing_py_checkpoint.json` was read first.
- `handoff/setup_fuzzing_py/approved_bootstrap_record.json` was verified before task-native implementation proceeded.
- `handoff/setup_fuzzing_py/local_bootstrap_fetch_record.json` was verified before task-native validation began.
- `handoff/setup_fuzzing_py/bootstrap_execution.marker` was verified before completion was recorded.
- `/app/libraries.txt` lists every target library under `/app/`.
- Each listed library has a non-empty `notes_for_testing.txt`.
- Each listed library has a runnable `fuzz.py`.
- Each listed library has a valid `.venv`.
- Each listed library has a `fuzz.log` showing instrumentation, coverage activity, and completion of the short fuzzing run.
- `handoff/setup_fuzzing_py/setup_fuzzing_py_completion.json` was written last as the final stage artifact.

        ## Bootstrap Completion Gate

        Begin this stage by reading `handoff/setup_fuzzing_py/setup_fuzzing_py_checkpoint.json` and enforcing the bootstrap prerequisites recorded there.

        Required gate checks:

        - `handoff/setup_fuzzing_py/approved_bootstrap_record.json` must exist before task-native implementation proceeds.
        - `handoff/setup_fuzzing_py/local_bootstrap_fetch_record.json` must exist before task-native verification begins.
        - `handoff/setup_fuzzing_py/bootstrap_execution.marker` must exist before `handoff/setup_fuzzing_py/setup_fuzzing_py_completion.json` is written.

        If any required bootstrap artifact is missing:

        - set `bootstrap_gate_status` to `blocked`
        - record the missing artifact status as `missing`
        - do not mark completion as passed
        - do not record final task closure

        When completion is allowed, write `handoff/setup_fuzzing_py/setup_fuzzing_py_completion.json` with at least these top-level keys:

        - `bootstrap_gate_status`
        - `approved_bootstrap_record_status`
        - `local_bootstrap_fetch_record_status`
        - `bootstrap_execution_marker_status`
- `libraries_txt_status`\n- `notes_for_testing_status`\n- `fuzz_driver_status`\n- `venv_status`\n- `fuzz_log_status`

        Also ensure:

- `/app/libraries.txt` must list every target library discovered under `/app`.\n- Each library listed in `/app/libraries.txt` must have a non-empty `notes_for_testing.txt` and a runnable `fuzz.py`.\n- Each listed library must have a valid `.venv` plus a `fuzz.log` showing a completed short fuzzing run with instrumentation.
