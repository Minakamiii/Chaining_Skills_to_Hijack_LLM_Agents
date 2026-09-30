"""Terminate a Codex run when it repeats one identical tool invocation forever."""

from __future__ import annotations

import argparse
from dataclasses import dataclass
import json
import os
from pathlib import Path
import signal
import time
from typing import Any


DEFAULT_MAX_IDENTICAL_CALLS = 5
DEFAULT_MAX_POLL_WAIT_RECOVERIES = 2
LONG_WAIT_RESUME_PROMPT = (
    "The current operation is taking a long time, and the previous status poll has repeated five times consecutively. Please do not immediately repeat the same poll;"
    "Significantly increase the wait time (to at least 60 seconds) before performing another bounded check, and verify whether there is any new output or new file."
    "Retain the current workspace and session; do not restart the task from scratch."
)


@dataclass(frozen=True, slots=True)
class ToolLoop:
    tool_name: str
    arguments: str
    repeats: int


def _canonical_arguments(value: Any) -> str:
    if isinstance(value, str):
        try:
            value = json.loads(value)
        except json.JSONDecodeError:
            pass
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def detect_repeated_tool_call(events: list[dict[str, Any]], *, max_repeats: int) -> ToolLoop | None:
    """Return the first consecutive repeated function call, if one exists."""
    previous: tuple[str, str] | None = None
    repeats = 0
    for event in events:
        if event.get("type") != "response_item":
            continue
        payload = event.get("payload")
        if not isinstance(payload, dict) or payload.get("type") not in {
            "function_call",
            "custom_tool_call",
        }:
            continue
        tool_name = str(payload.get("name") or "")
        arguments = _canonical_arguments(payload.get("arguments", payload.get("input")))
        current = (tool_name, arguments)
        repeats = repeats + 1 if current == previous else 1
        previous = current
        if repeats >= max_repeats:
            return ToolLoop(tool_name=tool_name, arguments=arguments, repeats=repeats)
    return None


def is_recoverable_polling_loop(loop: ToolLoop) -> bool:
    """Return whether a loop is an empty stdin poll that can be resumed safely.

    Repeating a status poll can be legitimate while a command is still running.
    Other identical calls (for example ``view_image`` or ``ls``) are semantic
    loops, so the guard must continue to terminate them rather than encouraging
    another identical action.
    """
    if loop.tool_name != "write_stdin":
        return False
    try:
        arguments = json.loads(loop.arguments)
    except json.JSONDecodeError:
        return False
    return isinstance(arguments, dict) and not str(arguments.get("chars", "")).strip()


def _read_session_events(sessions_dir: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    for session_file in sorted(sessions_dir.rglob("*.jsonl")):
        try:
            lines = session_file.read_text(encoding="utf-8").splitlines()
        except FileNotFoundError:
            continue
        for line in lines:
            try:
                event = json.loads(line)
            except json.JSONDecodeError:
                # A writer can leave the final line incomplete while it is appending.
                continue
            if isinstance(event, dict):
                events.append(event)
    return events


def _process_is_alive(pid: int) -> bool:
    try:
        os.kill(pid, 0)
    except ProcessLookupError:
        return False
    except PermissionError:
        return True
    return True


def run_guard(
    *,
    sessions_dir: Path,
    target_pid_file: Path,
    diagnostic_path: Path,
    max_repeats: int,
    guard_name: str = "codex",
    poll_seconds: float = 0.2,
    skip_existing_events: bool = False,
) -> int:
    """Watch a Codex session and terminate its process at a repeated-call loop."""
    while not target_pid_file.exists():
        time.sleep(poll_seconds)

    try:
        target_pid = int(target_pid_file.read_text(encoding="utf-8").strip())
    except (OSError, ValueError):
        return 2

    existing_event_count = len(_read_session_events(sessions_dir)) if skip_existing_events else 0
    while _process_is_alive(target_pid):
        events = _read_session_events(sessions_dir)
        loop = detect_repeated_tool_call(
            events[existing_event_count:],
            max_repeats=max_repeats,
        )
        if loop is not None:
            recovery_requested = is_recoverable_polling_loop(loop)
            diagnostic_path.parent.mkdir(parents=True, exist_ok=True)
            diagnostic_path.write_text(
                json.dumps(
                    {
                        "kind": f"{guard_name}_repeated_tool_loop",
                        "tool_name": loop.tool_name,
                        "arguments": loop.arguments,
                        "repeats": loop.repeats,
                        "max_repeats": max_repeats,
                        "recovery_requested": recovery_requested,
                        "resume_prompt": LONG_WAIT_RESUME_PROMPT if recovery_requested else "",
                        "action": (
                            "resume_with_longer_wait_prompt"
                            if recovery_requested
                            else "terminated_codex_process"
                        ),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            os.kill(target_pid, signal.SIGTERM)
            return 75
        time.sleep(poll_seconds)
    return 0


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--sessions-dir", type=Path, required=True)
    parser.add_argument("--target-pid-file", type=Path, required=True)
    parser.add_argument("--diagnostic-path", type=Path, required=True)
    parser.add_argument("--max-repeats", type=int, default=DEFAULT_MAX_IDENTICAL_CALLS)
    parser.add_argument("--guard-name", default="codex")
    parser.add_argument("--poll-seconds", type=float, default=0.2)
    parser.add_argument("--skip-existing-events", action="store_true")
    args = parser.parse_args()
    if args.max_repeats < 2:
        raise SystemExit("--max-repeats must be at least 2")
    raise SystemExit(
        run_guard(
            sessions_dir=args.sessions_dir,
            target_pid_file=args.target_pid_file,
            diagnostic_path=args.diagnostic_path,
            max_repeats=args.max_repeats,
            guard_name=args.guard_name,
            poll_seconds=args.poll_seconds,
            skip_existing_events=args.skip_existing_events,
        )
    )


if __name__ == "__main__":
    main()
