from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Iterable, Sequence
import argparse
import hashlib
import json
import os
import re
import shlex
import signal
import socket
import threading
import stat
import subprocess
import sys
import time
import uuid


DEFENSE_NAME = "global_skill_artifact_distrust"
DEFENSE_MODE_SHADOW = "no_defense_shadow_tracking"
DEFENSE_MODE_ENFORCE = DEFENSE_NAME
DEFENSE_AGENT_REGISTRY_PATH = Path(
    "/run/agent-sec-lab/defense/global-skill-artifact-distrust/taint-registry.json"
)
DEFENSE_FAILURE_RETURN_CODE = 86
SKILL_LEASE_COMMAND_NAME = "skillsbench-skill-lease"
SKILL_LEASE_COMMAND_PATH = Path("/usr/local/bin") / SKILL_LEASE_COMMAND_NAME
DEFENSE_SKILL_LEASE_SOCKET_PATH = DEFENSE_AGENT_REGISTRY_PATH.parent / ".skill-lease.sock"

DEFAULT_WORKSPACE_ROOTS = (Path("/root"), Path("/app"))
DEFAULT_EXCLUDE_PREFIXES = (
    Path("/root/.agents"),
    Path("/root/.codex"),
    Path("/root/.cache"),
    Path("/root/.cargo"),
    Path("/root/.config"),
    Path("/root/.local"),
    Path("/root/.npm"),
    Path("/root/.nvm"),
    Path("/root/.rustup"),
    Path("/root/.ssh"),
    Path("/root/.git"),
    Path("/app/.git"),
)

_READ_ONLY_COMMANDS = {
    "cat",
    "file",
    "find",
    "grep",
    "head",
    "less",
    "ls",
    "more",
    "readlink",
    "rg",
    "sed",
    "sha256sum",
    "stat",
    "tail",
    "wc",
}
_EXECUTABLE_SKILL_PATH_RE = re.compile(
    r"(?:^|[\s'\";])(?:/root/\.(?:agents|codex)/skills/|skills/)([^/\s'\";]+)/"
    r"(?:(?:scripts|bin)/[^\s'\";]+|[^\s'\";]+\.(?:py|sh|bash|js|mjs|cjs|ts|rb|pl))"
)


class DefenseInstrumentationError(RuntimeError):
    """Raised when the defense cannot preserve its declared instrumentation contract."""


@dataclass(frozen=True)
class FileFingerprint:
    workspace_root: str
    path: str
    absolute_path: str
    object_type: str
    sha256: str
    size: int
    mode: int

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> tuple[str, int, int]:
    for attempt in range(2):
        before = path.lstat()
        if not stat.S_ISREG(before.st_mode):
            raise DefenseInstrumentationError(f"not a regular file during snapshot: {path}")
        hasher = hashlib.sha256()
        size = 0
        file_flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(os.fspath(path), file_flags)
        with os.fdopen(descriptor, "rb") as handle:
            opened = os.fstat(handle.fileno())
            if (
                not stat.S_ISREG(opened.st_mode)
                or opened.st_dev != before.st_dev
                or opened.st_ino != before.st_ino
            ):
                raise DefenseInstrumentationError(f"file changed identity during snapshot: {path}")
            while True:
                chunk = handle.read(1024 * 1024)
                if not chunk:
                    break
                hasher.update(chunk)
                size += len(chunk)
        after = path.lstat()
        stable = (
            stat.S_ISREG(after.st_mode)
            and before.st_dev == after.st_dev
            and before.st_ino == after.st_ino
            and before.st_size == after.st_size
            and before.st_mtime_ns == after.st_mtime_ns
            and before.st_mode == after.st_mode
        )
        if stable:
            return hasher.hexdigest(), size, stat.S_IMODE(after.st_mode)
        if attempt == 1:
            raise DefenseInstrumentationError(f"file changed repeatedly while hashing: {path}")
    raise AssertionError("unreachable")


def _normalized_absolute(path: Path) -> Path:
    return Path(os.path.abspath(os.fspath(path)))


def _is_at_or_below(path: Path, prefix: Path) -> bool:
    normalized_path = _normalized_absolute(path)
    normalized_prefix = _normalized_absolute(prefix)
    return normalized_path == normalized_prefix or normalized_prefix in normalized_path.parents


def _is_excluded(path: Path, exclude_prefixes: Sequence[Path]) -> bool:
    return any(_is_at_or_below(path, prefix) for prefix in exclude_prefixes)


def _fingerprint_path(path: Path, workspace_root: Path) -> FileFingerprint | None:
    metadata = path.lstat()
    mode = stat.S_IMODE(metadata.st_mode)
    if stat.S_ISLNK(metadata.st_mode):
        link_target = os.readlink(path)
        encoded = os.fsencode(link_target)
        return FileFingerprint(
            workspace_root=str(workspace_root),
            path=path.relative_to(workspace_root).as_posix(),
            absolute_path=str(path),
            object_type="symlink",
            sha256=_sha256_bytes(encoded),
            size=len(encoded),
            mode=mode,
        )
    if not stat.S_ISREG(metadata.st_mode):
        return None
    digest, size, stable_mode = _sha256_file(path)
    return FileFingerprint(
        workspace_root=str(workspace_root),
        path=path.relative_to(workspace_root).as_posix(),
        absolute_path=str(path),
        object_type="file",
        sha256=digest,
        size=size,
        mode=stable_mode,
    )


def snapshot_workspace(
    workspace_roots: Iterable[Path],
    *,
    exclude_prefixes: Iterable[Path] = DEFAULT_EXCLUDE_PREFIXES,
    warnings: list[str] | None = None,
) -> dict[str, FileFingerprint]:
    roots = tuple(_normalized_absolute(root) for root in workspace_roots if root.exists())
    if not roots:
        raise DefenseInstrumentationError("no configured defense workspace root exists")
    exclusions = tuple(_normalized_absolute(path) for path in exclude_prefixes)
    snapshot: dict[str, FileFingerprint] = {}
    for root in roots:
        if not root.is_dir():
            raise DefenseInstrumentationError(f"defense workspace root is not a directory: {root}")
        for current_root, directory_names, file_names in os.walk(root, followlinks=False):
            current = Path(current_root)
            kept_directories: list[str] = []
            for name in directory_names:
                path = current / name
                if _is_excluded(path, exclusions):
                    continue
                try:
                    metadata = path.lstat()
                except FileNotFoundError:
                    raise DefenseInstrumentationError(f"file disappeared during snapshot: {path}") from None
                if stat.S_ISLNK(metadata.st_mode):
                    fingerprint = _fingerprint_path(path, root)
                    if fingerprint is not None:
                        snapshot[fingerprint.absolute_path] = fingerprint
                    continue
                if stat.S_ISDIR(metadata.st_mode):
                    kept_directories.append(name)
                elif warnings is not None:
                    warnings.append(f"unexpected special object during snapshot: {path}")
            directory_names[:] = kept_directories
            for name in file_names:
                path = current / name
                if _is_excluded(path, exclusions):
                    continue
                try:
                    fingerprint = _fingerprint_path(path, root)
                except FileNotFoundError:
                    # A one-shot disappearance is equivalent to an unstable file;
                    # retrying the entire snapshot would hide which boundary failed.
                    raise DefenseInstrumentationError(f"file disappeared during snapshot: {path}") from None
                except PermissionError as exc:
                    raise DefenseInstrumentationError(f"cannot read file during snapshot: {path}: {exc}") from exc
                if fingerprint is not None:
                    snapshot[fingerprint.absolute_path] = fingerprint
                elif warnings is not None:
                    warnings.append(f"unexpected special object during snapshot: {path}")
    return snapshot


def diff_snapshots(
    before: dict[str, FileFingerprint],
    after: dict[str, FileFingerprint],
) -> list[dict[str, Any]]:
    changes: list[dict[str, Any]] = []
    for absolute_path in sorted(set(before) | set(after)):
        old = before.get(absolute_path)
        new = after.get(absolute_path)
        if old is None and new is not None:
            changes.append({"change_kind": "created", "before": None, "after": new.to_dict()})
            continue
        if old is not None and new is None:
            changes.append({"change_kind": "deleted", "before": old.to_dict(), "after": None})
            continue
        if old is None or new is None:
            continue
        if old != new:
            changes.append({"change_kind": "modified", "before": old.to_dict(), "after": new.to_dict()})
    return changes


def _unwrap_shell_command(command: str) -> str:
    try:
        tokens = shlex.split(command)
    except ValueError:
        return command
    if not tokens:
        return command
    executable = Path(tokens[0]).name
    if executable not in {"bash", "dash", "sh", "zsh"}:
        return command
    for index, token in enumerate(tokens[:-1]):
        if token in {"-c", "-lc"}:
            return tokens[index + 1]
    return command


def detect_skill_command(command: str, skill_names: Iterable[str]) -> str | None:
    allowed = {name.strip() for name in skill_names if name.strip()}
    if not allowed:
        return None
    inner = _unwrap_shell_command(command)
    try:
        tokens = shlex.split(inner)
    except ValueError:
        tokens = []
    if tokens and Path(tokens[0]).name in _READ_ONLY_COMMANDS:
        return None
    detected = {match.group(1) for match in _EXECUTABLE_SKILL_PATH_RE.finditer(inner)} & allowed
    if len(detected) > 1:
        names = ", ".join(sorted(detected))
        raise DefenseInstrumentationError(f"one command executes multiple Skill packages: {names}")
    return next(iter(detected), None)


def parse_skill_lease_command(
    command: str,
    skill_names: Iterable[str],
) -> tuple[str, str] | None:
    """Parse a Harness-owned lease command, optionally followed by leased work.

    ``enter <id> && <command>`` is accepted because ``&&`` makes the socket
    sidecar complete its synchronous pre-snapshot before the trailing command
    can run. A strict ``exit <old> && enter <new> && <command>`` transition
    is also accepted: each socket request remains synchronous, so the old
    post-snapshot completes before the new pre-snapshot and trailing work.
    """

    allowed = {name.strip() for name in skill_names if name.strip()}
    inner = _unwrap_shell_command(command)
    try:
        tokens = shlex.split(inner)
    except ValueError:
        # Lease boundaries are owned by the synchronous socket sidecar, not by
        # best-effort parsing of arbitrary Codex shell telemetry.
        return None
    if not tokens or Path(tokens[0]).name != SKILL_LEASE_COMMAND_NAME:
        return None
    if len(tokens) < 2 or tokens[1] not in {"enter", "exit"}:
        return None
    if len(tokens) < 3:
        raise DefenseInstrumentationError(
            f"invalid Skill lease command; expected {SKILL_LEASE_COMMAND_NAME} enter|exit <skill-id>"
        )
    action, skill_id = tokens[1], tokens[2]
    if action == "exit" and len(tokens) > 3:
        is_bare_transition = (
            len(tokens) == 7
            and tokens[3] == "&&"
            and Path(tokens[4]).name == SKILL_LEASE_COMMAND_NAME
            and tokens[5] == "enter"
        )
        is_transition_with_work = (
            len(tokens) >= 9
            and tokens[3] == "&&"
            and Path(tokens[4]).name == SKILL_LEASE_COMMAND_NAME
            and tokens[5] == "enter"
            and tokens[7] == "&&"
            and tokens[8] not in {"&&", "||", ";", "&", "|"}
        )
        if not (is_bare_transition or is_transition_with_work):
            raise DefenseInstrumentationError(
                f"invalid Skill lease command; expected {SKILL_LEASE_COMMAND_NAME} enter|exit <skill-id>"
            )
        if skill_id not in allowed:
            raise DefenseInstrumentationError(f"Skill lease names an uninstalled Skill: {skill_id}")
        next_skill_id = tokens[6]
        if next_skill_id not in allowed:
            raise DefenseInstrumentationError(f"Skill lease names an uninstalled Skill: {next_skill_id}")
        return "transition", f"{skill_id}->{next_skill_id}"
    if action == "enter" and len(tokens) > 3 and (
        len(tokens) < 5
        or tokens[3] != "&&"
        or tokens[4] in {"&&", "||", ";", "&", "|"}
    ):
        raise DefenseInstrumentationError(
            f"invalid Skill lease command; expected {SKILL_LEASE_COMMAND_NAME} enter|exit <skill-id>"
        )
    if skill_id not in allowed:
        raise DefenseInstrumentationError(f"Skill lease names an uninstalled Skill: {skill_id}")
    return action, skill_id

def is_pure_skill_lease_command(command: str) -> bool:
    """Return whether one telemetry command contains no work beyond lease control."""
    inner = _unwrap_shell_command(command)
    try:
        tokens = shlex.split(inner)
    except ValueError:
        return False
    if len(tokens) == 3 and Path(tokens[0]).name == SKILL_LEASE_COMMAND_NAME:
        return True
    return (
        len(tokens) == 7
        and Path(tokens[0]).name == SKILL_LEASE_COMMAND_NAME
        and tokens[1] == "exit"
        and tokens[3] == "&&"
        and Path(tokens[4]).name == SKILL_LEASE_COMMAND_NAME
        and tokens[5] == "enter"
    )

def render_skill_lease_helper(
    socket_path: Path = DEFENSE_SKILL_LEASE_SOCKET_PATH,
) -> str:
    """Render the Harness-owned synchronous Skill-lease client.

    The helper contains only the fixed sidecar socket address. It has no
    authority to assign provenance itself: it succeeds only after the sidecar
    validates the request and completes the corresponding boundary operation.
    """

    rendered_socket_path = json.dumps(str(socket_path))
    return f"""#!/usr/bin/env python3
import json
import socket
import sys

SOCKET_PATH = {rendered_socket_path}
MAX_RESPONSE_BYTES = 1024 * 1024


def fail(message):
    print("skillsbench-skill-lease: " + message, file=sys.stderr)
    raise SystemExit(2)


def main():
    if len(sys.argv) != 3 or sys.argv[1] not in {{"enter", "exit"}}:
        fail("expected: skillsbench-skill-lease enter|exit <installed-skill-id>")
    request = json.dumps(
        {{"action": sys.argv[1], "skill_id": sys.argv[2]}},
        separators=(",", ":"),
    ).encode("utf-8") + b"\\n"
    try:
        with socket.socket(socket.AF_UNIX, socket.SOCK_STREAM) as client:
            client.settimeout(30)
            client.connect(SOCKET_PATH)
            client.sendall(request)
            response = bytearray()
            while b"\\n" not in response:
                chunk = client.recv(4096)
                if not chunk:
                    break
                response.extend(chunk)
                if len(response) > MAX_RESPONSE_BYTES:
                    fail("sidecar response exceeds size limit")
    except OSError as exc:
        fail("cannot reach Harness sidecar: " + str(exc))
    try:
        payload = json.loads(bytes(response).split(b"\\n", 1)[0].decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        fail("invalid Harness sidecar response: " + str(exc))
    if not isinstance(payload, dict) or payload.get("ok") is not True:
        error = payload.get("error", "Harness sidecar rejected the lease request") if isinstance(payload, dict) else "invalid Harness sidecar response"
        fail(str(error))
    print("skill lease " + str(payload.get("action", sys.argv[1])) + " acknowledged")


if __name__ == "__main__":
    main()
"""


def _atomic_write(path: Path, payload: bytes, *, mode: int) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{os.getpid()}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("wb") as handle:
            handle.write(payload)
            handle.flush()
            os.fsync(handle.fileno())
        os.chmod(temporary, mode)
        os.replace(temporary, path)
    finally:
        if temporary.exists():
            temporary.unlink()


class TaintRegistry:
    def __init__(
        self,
        *,
        registry_path: Path,
        projection_path: Path,
        workspace_roots: Sequence[Path],
        exclude_prefixes: Sequence[Path],
        skill_names: Sequence[str],
        original_user_request_sha256: str,
        require_skill_lease: bool = False,
    ) -> None:
        self.registry_path = registry_path
        self.projection_path = projection_path
        self.workspace_roots = tuple(workspace_roots)
        self.exclude_prefixes = tuple(exclude_prefixes)
        self.skill_names = tuple(skill_names)
        self.original_user_request_sha256 = original_user_request_sha256
        self.require_skill_lease = require_skill_lease
        self.active_artifacts: dict[str, dict[str, Any]] = {}
        self.events: list[dict[str, Any]] = []
        self.invocations: list[dict[str, Any]] = []
        self.lease_events: list[dict[str, Any]] = []
        self.unleased_changes: list[dict[str, Any]] = []
        self.instrumentation_errors: list[str] = []
        self.instrumentation_warnings: list[str] = []
        self.snapshot_count = 0
        self.snapshot_seconds = 0.0
        self.diff_seconds = 0.0
        self.status = "active"
        self.child_returncode: int | None = None
        self.started_at = time.time()
        self.completed_at: float | None = None
        self._projection_sha256: str | None = None

    def _exclude_hash(self) -> str:
        serialized = json.dumps(
            sorted(str(_normalized_absolute(path)) for path in self.exclude_prefixes),
            ensure_ascii=False,
            separators=(",", ":"),
        ).encode("utf-8")
        return _sha256_bytes(serialized)

    def _payload(self) -> dict[str, Any]:
        return {
            "schema_version": 1,
            "defense": DEFENSE_NAME,
            "status": self.status,
            "original_user_request_sha256": self.original_user_request_sha256,
            "workspace_roots": [str(path) for path in self.workspace_roots],
            "exclude_prefixes": [str(path) for path in self.exclude_prefixes],
            "exclude_prefixes_sha256": self._exclude_hash(),
            "skill_names": list(self.skill_names),
            "require_skill_lease": self.require_skill_lease,
            "started_at": self.started_at,
            "completed_at": self.completed_at,
            "child_returncode": self.child_returncode,
            "active_artifacts": [self.active_artifacts[path] for path in sorted(self.active_artifacts)],
            "events": list(self.events),
            "invocations": list(self.invocations),
            "lease_events": list(self.lease_events),
            "unleased_changes": list(self.unleased_changes),
            "instrumentation_errors": list(self.instrumentation_errors),
            "instrumentation_warnings": list(self.instrumentation_warnings),
            "overhead": {
                "snapshot_count": self.snapshot_count,
                "snapshot_seconds": self.snapshot_seconds,
                "diff_seconds": self.diff_seconds,
            },
        }

    def record_lease_event(self, *, event_type: str, invocation_id: str, skill_id: str, command_item_id: str) -> None:
        self.lease_events.append(
            {
                "event_type": event_type,
                "invocation_id": invocation_id,
                "skill_id": skill_id,
                "command_item_id": command_item_id,
            }
        )

    def record_unleased_changes(self, *, command_item_id: str, command: str, changes: Sequence[dict[str, Any]]) -> None:
        self.unleased_changes.extend(
            {
                "command_item_id": command_item_id,
                "command_sha256": _sha256_bytes(command.encode("utf-8", errors="surrogateescape")),
                "path": str((change.get("after") or change.get("before") or {}).get("path", "")),
                "change_kind": str(change.get("change_kind", "")),
            }
            for change in changes
        )

    def record_snapshot(self, elapsed_seconds: float, warnings: Sequence[str]) -> None:
        self.snapshot_count += 1
        self.snapshot_seconds += elapsed_seconds
        self.instrumentation_warnings.extend(warnings)

    def _verify_projection(self) -> None:
        if self._projection_sha256 is None:
            return
        try:
            current = self.projection_path.read_bytes()
        except FileNotFoundError as exc:
            raise DefenseInstrumentationError("agent-visible taint registry projection was removed") from exc
        if _sha256_bytes(current) != self._projection_sha256:
            raise DefenseInstrumentationError("agent-visible taint registry projection was modified")

    def persist(self, *, verify_projection: bool = True) -> None:
        if verify_projection:
            self._verify_projection()
        encoded = (json.dumps(self._payload(), indent=2, ensure_ascii=False) + "\n").encode("utf-8")
        # This registry is copied out of the container as trial evidence. Under
        # rootless UID mapping the host runner is not its owner, so it must stay
        # readable after the trial; the separate projection remains read-only.
        _atomic_write(self.registry_path, encoded, mode=0o644)
        _atomic_write(self.projection_path, encoded, mode=0o444)
        self._projection_sha256 = _sha256_bytes(encoded)

    def apply_invocation(
        self,
        *,
        invocation_id: str,
        skill_id: str,
        command_item_id: str,
        command: str,
        exit_command_item_id: str = "",
        exit_command: str = "",
        closure_reason: str = "",
        exit_code: int | None,
        before: dict[str, FileFingerprint],
        after: dict[str, FileFingerprint],
    ) -> None:
        diff_started = time.perf_counter()
        changes = diff_snapshots(before, after)
        self.diff_seconds += time.perf_counter() - diff_started
        invocation_event_ids: list[str] = []
        for change in changes:
            event_id = f"event-{len(self.events) + 1:06d}"
            old = change["before"]
            new = change["after"]
            current = new if new is not None else old
            event = {
                "event_id": event_id,
                "invocation_id": invocation_id,
                "skill_id": skill_id,
                "command_item_id": command_item_id,
                # Registry paths are workspace-relative by contract.
                "path": current["path"],
                "absolute_path": current["absolute_path"],
                "workspace_root": current["workspace_root"],
                "relative_path": current["path"],
                "change_kind": change["change_kind"],
                "before_sha256": old["sha256"] if old is not None else None,
                "after_sha256": new["sha256"] if new is not None else None,
                "before_mode": old["mode"] if old is not None else None,
                "after_mode": new["mode"] if new is not None else None,
            }
            self.events.append(event)
            invocation_event_ids.append(event_id)
            absolute_path = current["absolute_path"]
            if change["change_kind"] == "deleted":
                self.active_artifacts.pop(absolute_path, None)
                continue
            previous = self.active_artifacts.get(absolute_path, {})
            prior_ids = list(previous.get("provenance_event_ids", []))
            self.active_artifacts[absolute_path] = {
                "path": current["path"],
                "absolute_path": absolute_path,
                "workspace_root": current["workspace_root"],
                "relative_path": current["path"],
                "tainted": True,
                "producer_skill": skill_id,
                "producer_invocation_id": invocation_id,
                "provenance_event_ids": prior_ids + [event_id],
                "current_sha256": new["sha256"],
                "current_mode": new["mode"],
                "object_type": new["object_type"],
                "last_change_kind": change["change_kind"],
            }
        self.invocations.append(
            {
                "invocation_id": invocation_id,
                "skill_id": skill_id,
                "command_item_id": command_item_id,
                "command_sha256": _sha256_bytes(command.encode("utf-8", errors="surrogateescape")),
                "exit_command_item_id": exit_command_item_id,
                "exit_command_sha256": _sha256_bytes(exit_command.encode("utf-8", errors="surrogateescape")) if exit_command else "",
                "closure_reason": closure_reason,
                "exit_code": exit_code,
                "provenance_event_ids": invocation_event_ids,
            }
        )
        self.persist()

    def complete(self, child_returncode: int) -> None:
        self.status = "completed"
        self.child_returncode = child_returncode
        self.completed_at = time.time()
        self.persist()

    def fail(self, message: str, *, child_returncode: int | None = None) -> None:
        self.status = "instrumentation_failed"
        self.child_returncode = child_returncode
        self.completed_at = time.time()
        self.instrumentation_errors.append(message)
        # A tampered projection must not prevent the authoritative persisted
        # record from explaining the failure. Overwrite the projection too.
        self.persist(verify_projection=False)


@dataclass
class _ActiveInvocation:
    invocation_id: str
    skill_id: str
    command_item_id: str
    command: str
    before: dict[str, FileFingerprint]
    open_scopes: int


class _SkillLeaseSocketBroker:
    """Own the synchronous enter/exit boundary for one supervised trial.

    Codex collaboration workers share the trial workspace but do not expose a
    Harness-verifiable parent/child lease identity to this socket protocol. A
    repeated ``enter`` for the *already active same Skill* is therefore a
    join of the existing invocation with a nested scope, not a second snapshot
    boundary. Each matching ``exit`` releases one scope; only the final exit
    closes the invocation and captures its post-snapshot. An observed enter of
    a different installed Skill implicitly closes a single-scope predecessor;
    nested scopes remain fail-closed because their owners are ambiguous.
    """

    _MAX_REQUEST_BYTES = 64 * 1024

    def __init__(
        self,
        *,
        registry: TaintRegistry,
        workspace_roots: Sequence[Path],
        exclude_prefixes: Sequence[Path],
        socket_path: Path,
    ) -> None:
        self.registry = registry
        self.workspace_roots = tuple(workspace_roots)
        self.exclude_prefixes = tuple(exclude_prefixes)
        self.socket_path = socket_path
        self._active: _ActiveInvocation | None = None
        self._settled_snapshot: dict[str, FileFingerprint] = {}
        self._failure: str | None = None
        self._request_sequence = 0
        self._listener: socket.socket | None = None
        self._thread: threading.Thread | None = None
        self._stopping = threading.Event()
        self._lock = threading.RLock()

    @property
    def active(self) -> _ActiveInvocation | None:
        return self._active

    @property
    def failure(self) -> str | None:
        return self._failure

    def _take_snapshot(self) -> dict[str, FileFingerprint]:
        warnings: list[str] = []
        started = time.perf_counter()
        snapshot = snapshot_workspace(
            self.workspace_roots,
            exclude_prefixes=self.exclude_prefixes,
            warnings=warnings,
        )
        self.registry.record_snapshot(time.perf_counter() - started, warnings)
        return snapshot

    def _record_unleased_changes(
        self,
        *,
        command_item_id: str,
        command: str,
        before: dict[str, FileFingerprint],
        after: dict[str, FileFingerprint],
    ) -> None:
        started = time.perf_counter()
        changes = diff_snapshots(before, after)
        self.registry.diff_seconds += time.perf_counter() - started
        if changes:
            self.registry.record_unleased_changes(
                command_item_id=command_item_id,
                command=command,
                changes=changes,
            )
            raise DefenseInstrumentationError("workspace changed outside an active Skill lease")

    def _next_control_id(self, action: str) -> str:
        self._request_sequence += 1
        return f"socket-{action}-{self._request_sequence:06d}"

    def start(self) -> None:
        self.socket_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            self.socket_path.lstat()
        except FileNotFoundError:
            pass
        else:
            raise DefenseInstrumentationError(
                f"Skill lease socket path already exists: {self.socket_path}"
            )
        self._settled_snapshot = self._take_snapshot()
        listener = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        try:
            listener.bind(os.fspath(self.socket_path))
            os.chmod(self.socket_path, 0o666)
            listener.listen(8)
            listener.settimeout(0.2)
        except Exception:
            listener.close()
            try:
                self.socket_path.unlink()
            except FileNotFoundError:
                pass
            raise
        self._listener = listener
        self._thread = threading.Thread(
            target=self._serve,
            name="skillsbench-skill-lease-sidecar",
            daemon=True,
        )
        self._thread.start()

    def stop(self) -> None:
        self._stopping.set()
        if self._listener is not None:
            try:
                self._listener.close()
            except OSError:
                pass
        if self._thread is not None:
            self._thread.join(timeout=5)
        try:
            metadata = self.socket_path.lstat()
        except FileNotFoundError:
            return
        if stat.S_ISSOCK(metadata.st_mode):
            self.socket_path.unlink()

    def assert_no_unleased_tail(self) -> None:
        with self._lock:
            if self._active is not None:
                raise DefenseInstrumentationError(
                    f"Skill lease did not close: {self._active.invocation_id} ({self._active.skill_id})"
                )
            after = self._take_snapshot()
            self._record_unleased_changes(
                command_item_id="outside-lease-tail",
                command="[post-run outside-lease reconciliation]",
                before=self._settled_snapshot,
                after=after,
            )
            self._settled_snapshot = after

    def close_for_normal_completion(self) -> None:
        """Close one final single-scope lease after Codex exits successfully."""
        with self._lock:
            active = self._active
            if active is None:
                return
            if active.open_scopes != 1:
                raise DefenseInstrumentationError(
                    f"Skill lease has {active.open_scopes} open scopes at normal completion: "
                    f"{active.invocation_id} ({active.skill_id})"
                )
            self._exit(
                active.skill_id,
                event_type="skill_implicit_exit_agent_completed",
                control_action="implicit-agent-completed",
                exit_command="[sidecar implicit_exit_agent_completed: Codex child exited with returncode 0]",
                closure_reason="Codex child exited with returncode 0",
            )

    def close_for_failed_leased_command(
        self, *, skill_id: str, exit_code: int, command: str
    ) -> None:
        """Close a lease when its entered shell command fails before explicit exit."""
        with self._lock:
            active = self._active
            if active is None or active.skill_id != skill_id:
                raise DefenseInstrumentationError(
                    f"failed leased command has no matching active Skill: {skill_id}"
                )
            self._exit(
                skill_id,
                event_type="skill_implicit_exit_command_failed",
                control_action="implicit-command-failed",
                exit_command=f"[sidecar implicit_exit_command_failed: exit={exit_code}; {command}]",
                closure_reason=f"leased command completed with exit={exit_code}",
                exit_code=exit_code,
            )

    def _serve(self) -> None:
        assert self._listener is not None
        while not self._stopping.is_set():
            try:
                connection, _ = self._listener.accept()
            except socket.timeout:
                continue
            except OSError as exc:
                if not self._stopping.is_set():
                    self._set_failure(f"Skill lease socket accept failed: {exc}")
                return
            with connection:
                connection.settimeout(5)
                response = self._handle_connection(connection)
                try:
                    connection.sendall(
                        (json.dumps(response, ensure_ascii=False, separators=(",", ":")) + "\n").encode("utf-8")
                    )
                except OSError:
                    pass

    def _set_failure(self, message: str) -> None:
        with self._lock:
            if self._failure is None:
                self._failure = message

    def _handle_connection(self, connection: socket.socket) -> dict[str, Any]:
        request = bytearray()
        try:
            while b"\n" not in request:
                chunk = connection.recv(4096)
                if not chunk:
                    break
                request.extend(chunk)
                if len(request) > self._MAX_REQUEST_BYTES:
                    raise DefenseInstrumentationError("Skill lease request exceeds size limit")
            payload = json.loads(bytes(request).split(b"\n", 1)[0].decode("utf-8"))
        except (OSError, UnicodeDecodeError, json.JSONDecodeError, DefenseInstrumentationError) as exc:
            message = f"invalid Skill lease sidecar request: {exc}"
            self._set_failure(message)
            return {"ok": False, "error": message}
        if not isinstance(payload, dict) or set(payload) != {"action", "skill_id"}:
            message = "invalid Skill lease sidecar request shape"
            self._set_failure(message)
            return {"ok": False, "error": message}
        action = payload.get("action")
        skill_id = payload.get("skill_id")
        if not isinstance(action, str) or not isinstance(skill_id, str):
            message = "invalid Skill lease sidecar request fields"
            self._set_failure(message)
            return {"ok": False, "error": message}
        try:
            with self._lock:
                if self._failure is not None:
                    raise DefenseInstrumentationError(self._failure)
                if action == "enter":
                    invocation_id = self._enter(skill_id)
                elif action == "exit":
                    invocation_id = self._exit(skill_id)
                else:
                    raise DefenseInstrumentationError("Skill lease action must be enter or exit")
        except DefenseInstrumentationError as exc:
            message = str(exc)
            self._set_failure(message)
            return {"ok": False, "error": message}
        except Exception as exc:  # noqa: BLE001 - surface a sidecar failure to the supervisor
            message = f"{type(exc).__name__}: {exc}"
            self._set_failure(message)
            return {"ok": False, "error": message}
        return {"ok": True, "action": action, "invocation_id": invocation_id}

    def _enter(self, skill_id: str) -> str:
        if skill_id not in self.registry.skill_names:
            raise DefenseInstrumentationError(f"Skill lease names an uninstalled Skill: {skill_id}")
        if self._active is not None:
            if self._active.skill_id == skill_id:
                self._active.open_scopes += 1
                join_command_item_id = self._next_control_id("join")
                self.registry.record_lease_event(
                    event_type="skill_join",
                    invocation_id=self._active.invocation_id,
                    skill_id=skill_id,
                    command_item_id=join_command_item_id,
                )
                self.registry.persist()
                return self._active.invocation_id
            if self._active.open_scopes != 1:
                raise DefenseInstrumentationError(
                    f"overlapping Skill lease enter with {self._active.open_scopes} active scopes: "
                    f"{self._active.skill_id} -> {skill_id}"
                )
            self._exit(
                self._active.skill_id,
                event_type="skill_implicit_exit_next_skill",
                control_action="implicit-next-skill",
                exit_command=(
                    f"[sidecar implicit_exit_next_skill: observed enter {skill_id}]"
                ),
                closure_reason=f"observed enter of next installed Skill: {skill_id}",
            )
        before = self._take_snapshot()
        self._record_unleased_changes(
            command_item_id="outside-lease-before-enter",
            command=f"{SKILL_LEASE_COMMAND_NAME} enter {skill_id}",
            before=self._settled_snapshot,
            after=before,
        )
        invocation_id = f"inv-{len(self.registry.invocations) + 1:06d}"
        command_item_id = self._next_control_id("enter")
        command = f"{SKILL_LEASE_COMMAND_NAME} enter {skill_id}"
        self._active = _ActiveInvocation(
            invocation_id=invocation_id,
            skill_id=skill_id,
            command_item_id=command_item_id,
            command=command,
            open_scopes=1,
            before=before,
        )
        self.registry.record_lease_event(
            event_type="skill_enter",
            invocation_id=invocation_id,
            skill_id=skill_id,
            command_item_id=command_item_id,
        )
        self.registry.persist()
        return invocation_id

    def _exit(
        self,
        skill_id: str,
        *,
        event_type: str = "skill_exit",
        control_action: str = "exit",
        exit_command: str | None = None,
        closure_reason: str = "",
        exit_code: int = 0,
    ) -> str:
        active = self._active
        if active is None or active.skill_id != skill_id:
            raise DefenseInstrumentationError(
                f"Skill lease exit does not match active Skill: {skill_id}"
            )
        if active.open_scopes > 1:
            active.open_scopes -= 1
            leave_command_item_id = self._next_control_id("leave")
            self.registry.record_lease_event(
                event_type="skill_leave",
                invocation_id=active.invocation_id,
                skill_id=active.skill_id,
                command_item_id=leave_command_item_id,
            )
            self.registry.persist()
            return active.invocation_id
        after = self._take_snapshot()
        exit_command_item_id = self._next_control_id(control_action)
        exit_command = exit_command or f"{SKILL_LEASE_COMMAND_NAME} exit {skill_id}"
        self.registry.apply_invocation(
            invocation_id=active.invocation_id,
            skill_id=active.skill_id,
            command_item_id=active.command_item_id,
            command=active.command,
            exit_command_item_id=exit_command_item_id,
            exit_command=exit_command,
            closure_reason=closure_reason,
            exit_code=exit_code,
            before=active.before,
            after=after,
        )
        self.registry.record_lease_event(
            event_type=event_type,
            invocation_id=active.invocation_id,
            skill_id=active.skill_id,
            command_item_id=exit_command_item_id,
        )
        self.registry.persist()
        self._active = None
        self._settled_snapshot = after
        return active.invocation_id


def _parse_codex_event(line: str) -> dict[str, Any] | None:
    try:
        loaded = json.loads(line)
    except json.JSONDecodeError:
        return None
    return loaded if isinstance(loaded, dict) else None


def supervise_codex_command(
    command: Sequence[str],
    *,
    registry_path: Path,
    projection_path: Path,
    log_path: Path,
    workspace_roots: Sequence[Path],
    exclude_prefixes: Sequence[Path],
    skill_names: Sequence[str],
    original_user_request_sha256: str,
    require_skill_lease: bool = False,
    skill_lease_socket_path: Path | None = None,
) -> int:
    if require_skill_lease:
        return _supervise_codex_with_skill_leases(
            command,
            registry_path=registry_path,
            projection_path=projection_path,
            log_path=log_path,
            workspace_roots=workspace_roots,
            exclude_prefixes=exclude_prefixes,
            skill_names=skill_names,
            original_user_request_sha256=original_user_request_sha256,
            skill_lease_socket_path=(
                skill_lease_socket_path
                if skill_lease_socket_path is not None
                else projection_path.parent / ".skill-lease.sock"
            ),
        )
    registry = TaintRegistry(
        registry_path=registry_path,
        projection_path=projection_path,
        workspace_roots=workspace_roots,
        exclude_prefixes=exclude_prefixes,
        skill_names=skill_names,
        original_user_request_sha256=original_user_request_sha256,
        require_skill_lease=False,
    )
    registry.persist(verify_projection=False)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    active: _ActiveInvocation | None = None
    child: subprocess.Popen[str] | None = None
    try:
        with log_path.open("w", encoding="utf-8") as log_handle:
            child = subprocess.Popen(
                list(command),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            if child.stdout is None:
                raise DefenseInstrumentationError("Codex supervisor did not receive a stdout stream")
            for line in child.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                log_handle.write(line)
                log_handle.flush()
                event = _parse_codex_event(line)
                if event is None:
                    continue
                item = event.get("item")
                if not isinstance(item, dict) or item.get("type") != "command_execution":
                    continue
                event_type = str(event.get("type", ""))
                item_id = str(item.get("id", ""))
                if event_type == "item.started":
                    command_text = str(item.get("command", ""))
                    skill_id = detect_skill_command(command_text, skill_names)
                    if skill_id is None:
                        continue
                    if active is not None:
                        raise DefenseInstrumentationError(
                            f"overlapping Skill command executions: {active.command_item_id} and {item_id}"
                        )
                    invocation_id = f"inv-{len(registry.invocations) + 1:06d}"
                    warnings: list[str] = []
                    snapshot_started = time.perf_counter()
                    before = snapshot_workspace(
                        workspace_roots,
                        exclude_prefixes=exclude_prefixes,
                        warnings=warnings,
                    )
                    registry.record_snapshot(time.perf_counter() - snapshot_started, warnings)
                    active = _ActiveInvocation(
                        invocation_id=invocation_id,
                        skill_id=skill_id,
                        command_item_id=item_id,
                        command=command_text,
                        before=before,
                    )
                    continue
                if event_type != "item.completed" or active is None or active.command_item_id != item_id:
                    continue
                warnings = []
                snapshot_started = time.perf_counter()
                after = snapshot_workspace(
                    workspace_roots,
                    exclude_prefixes=exclude_prefixes,
                    warnings=warnings,
                )
                registry.record_snapshot(time.perf_counter() - snapshot_started, warnings)
                exit_code_raw = item.get("exit_code")
                exit_code = int(exit_code_raw) if isinstance(exit_code_raw, int) else None
                registry.apply_invocation(
                    invocation_id=active.invocation_id,
                    skill_id=active.skill_id,
                    command_item_id=active.command_item_id,
                    command=active.command,
                    exit_code=exit_code,
                    before=active.before,
                    after=after,
                )
                active = None
            child_returncode = child.wait()
        if active is not None:
            raise DefenseInstrumentationError(
                f"Skill command execution did not complete: {active.command_item_id}"
            )
        registry.complete(child_returncode)
        return child_returncode
    except Exception as exc:  # noqa: BLE001 - wrapper must persist all instrumentation failures
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        message = f"{type(exc).__name__}: {exc}"
        try:
            registry.fail(message, child_returncode=child.returncode if child is not None else None)
        except Exception as persist_exc:  # noqa: BLE001
            message += f"; registry failure: {type(persist_exc).__name__}: {persist_exc}"
        failure_line = json.dumps(
            {"type": "global_skill_artifact_distrust.error", "message": message},
            ensure_ascii=False,
        )
        sys.stdout.write(failure_line + "\n")
        sys.stdout.flush()
        try:
            with log_path.open("a", encoding="utf-8") as log_handle:
                log_handle.write(failure_line + "\n")
        except OSError:
            pass
        return DEFENSE_FAILURE_RETURN_CODE


def _supervise_codex_with_skill_leases(
    command: Sequence[str],
    *,
    registry_path: Path,
    projection_path: Path,
    log_path: Path,
    workspace_roots: Sequence[Path],
    exclude_prefixes: Sequence[Path],
    skill_names: Sequence[str],
    original_user_request_sha256: str,
    skill_lease_socket_path: Path,
) -> int:
    """Run the defense-only explicit Skill lease protocol.

    A synchronous sidecar owns the actual enter and exit boundaries. Codex JSON
    output is retained for trace logging and diagnostics only; it must never
    decide when a before or after workspace snapshot is captured.
    """

    registry = TaintRegistry(
        registry_path=registry_path,
        projection_path=projection_path,
        workspace_roots=workspace_roots,
        exclude_prefixes=exclude_prefixes,
        skill_names=skill_names,
        original_user_request_sha256=original_user_request_sha256,
        require_skill_lease=True,
    )
    registry.persist(verify_projection=False)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    broker = _SkillLeaseSocketBroker(
        registry=registry,
        workspace_roots=workspace_roots,
        exclude_prefixes=exclude_prefixes,
        socket_path=skill_lease_socket_path,
    )
    child: subprocess.Popen[str] | None = None
    prior_termination_handlers: dict[int, Any] = {}

    def _record_termination(signum: int, _frame: Any) -> None:
        raise DefenseInstrumentationError(f"supervisor received termination signal {signum}")

    for termination_signal in (signal.SIGTERM, signal.SIGHUP):
        try:
            prior_termination_handlers[termination_signal] = signal.signal(
                termination_signal, _record_termination
            )
        except ValueError:
            # Signal handlers are installable only from the process main thread.
            # The supervisor is normally launched there; retain normal behavior
            # when a unit test invokes it from a worker thread.
            pass
    broker_started = False
    try:
        broker.start()
        broker_started = True
        with log_path.open("w", encoding="utf-8") as log_handle:
            child = subprocess.Popen(
                list(command),
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1,
            )
            if child.stdout is None:
                raise DefenseInstrumentationError("Codex supervisor did not receive a stdout stream")
            for line in child.stdout:
                sys.stdout.write(line)
                sys.stdout.flush()
                log_handle.write(line)
                log_handle.flush()
                event = _parse_codex_event(line)
                if event is None:
                    continue
                item = event.get("item")
                if not isinstance(item, dict) or item.get("type") != "command_execution":
                    continue
                command_text = str(item.get("command", ""))
                control = parse_skill_lease_command(command_text, skill_names)
                if control is not None:
                    if str(event.get("type", "")) == "item.completed":
                        exit_code_raw = item.get("exit_code")
                        exit_code = int(exit_code_raw) if isinstance(exit_code_raw, int) else None
                        if exit_code not in {0, None}:
                            if is_pure_skill_lease_command(command_text):
                                raise DefenseInstrumentationError(
                                    f"Skill lease helper command failed for {control[1]}: exit={exit_code}"
                                )
                            active = broker.active
                            active_skill_id = control[1].rsplit("->", 1)[-1]
                            if active is None or active.skill_id != active_skill_id:
                                raise DefenseInstrumentationError(
                                    "failed leased command has no matching active Skill: "
                                    f"{active_skill_id}"
                                )
                            broker.close_for_failed_leased_command(
                                skill_id=active_skill_id,
                                exit_code=exit_code,
                                command=command_text,
                            )
                    continue
                detected_skill = detect_skill_command(command_text, skill_names)
                if detected_skill is None:
                    continue
                active = broker.active
                if active is None:
                    raise DefenseInstrumentationError(
                        f"Skill script executed outside an active Skill lease: {detected_skill}"
                    )
                if active.skill_id != detected_skill:
                    raise DefenseInstrumentationError(
                        f"active Skill {active.skill_id} executed another Skill package: {detected_skill}"
                    )
            child_returncode = child.wait()
        if broker.failure is not None:
            raise DefenseInstrumentationError(broker.failure)
        if child_returncode == 0:
            broker.close_for_normal_completion()
        broker.assert_no_unleased_tail()
        if broker.failure is not None:
            raise DefenseInstrumentationError(broker.failure)
        registry.complete(child_returncode)
        return child_returncode
    except Exception as exc:  # noqa: BLE001 - wrapper must persist all instrumentation failures
        if child is not None and child.poll() is None:
            child.terminate()
            try:
                child.wait(timeout=5)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()
        message = f"{type(exc).__name__}: {exc}"
        try:
            registry.fail(message, child_returncode=child.returncode if child is not None else None)
        except Exception as persist_exc:  # noqa: BLE001
            message += f"; registry failure: {type(persist_exc).__name__}: {persist_exc}"
        failure_line = json.dumps(
            {"type": "global_skill_artifact_distrust.error", "message": message},
            ensure_ascii=False,
        )
        sys.stdout.write(failure_line + "\n")
        sys.stdout.flush()
        try:
            with log_path.open("a", encoding="utf-8") as log_handle:
                log_handle.write(failure_line + "\n")
        except OSError:
            pass
        return DEFENSE_FAILURE_RETURN_CODE
    finally:
        if broker_started:
            broker.stop()
        for termination_signal, prior_handler in prior_termination_handlers.items():
            try:
                signal.signal(termination_signal, prior_handler)
            except ValueError:
                pass


def render_supervisor_script() -> str:
    return Path(__file__).read_text(encoding="utf-8")


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Supervise Codex with Global Skill-Artifact Distrust tracking")
    parser.add_argument("--registry-path", type=Path, required=True)
    parser.add_argument("--projection-path", type=Path, required=True)
    parser.add_argument("--log-path", type=Path, required=True)
    parser.add_argument("--workspace-root", type=Path, action="append", default=[])
    parser.add_argument("--exclude-prefix", type=Path, action="append", default=[])
    parser.add_argument("--skill-name", action="append", default=[])
    parser.add_argument("--original-user-request-sha256", required=True)
    parser.add_argument("--require-skill-lease", action="store_true")
    parser.add_argument("--skill-lease-socket", type=Path)
    parser.add_argument("command", nargs=argparse.REMAINDER)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    command = list(args.command)
    if command and command[0] == "--":
        command = command[1:]
    if not command:
        raise SystemExit("missing supervised Codex command")
    workspace_roots = tuple(args.workspace_root) or DEFAULT_WORKSPACE_ROOTS
    exclude_prefixes = tuple(args.exclude_prefix) or DEFAULT_EXCLUDE_PREFIXES
    return supervise_codex_command(
        command,
        registry_path=args.registry_path,
        projection_path=args.projection_path,
        log_path=args.log_path,
        workspace_roots=workspace_roots,
        exclude_prefixes=exclude_prefixes,
        skill_names=tuple(args.skill_name),
        original_user_request_sha256=args.original_user_request_sha256,
        require_skill_lease=args.require_skill_lease,
        skill_lease_socket_path=args.skill_lease_socket,
    )


if __name__ == "__main__":
    raise SystemExit(main())
