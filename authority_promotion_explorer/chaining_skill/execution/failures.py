"""Central classification and recovery for execution-time failures.

All provider-timeout fallback decisions and post-timeout Compose cleanup live
here. Callers receive structured evidence instead of duplicating cleanup
commands or transport-marker lists.
"""

from __future__ import annotations

from pathlib import Path
import re
import subprocess
from typing import Any

from agent_sec_lab.config import ModelConfig


_CLEANUP_TIMEOUT_SECONDS = 30
_DOCKER_COMPOSE_WORKING_DIR_LABEL = "com.docker.compose.project.working_dir"
_DOCKER_CONTAINER_ID_RE = re.compile(r"^[0-9a-f]{12,64}$")
_CODEX_TRANSPORT_MARKERS = (
    "timed out after",
    "timeoutexpired",
    "failed to refresh available models",
    "stream disconnected before completion",
    "transport channel closed",
    "http/request failed",
    "failed to decode models response",
    "expected value at line 1 column 1",
    "body: <!doctype html>",
    "warning: no last agent message",
    "no last agent message",
    "wrote empty content",
)


def should_fallback_from_codex_timeout(model_config: ModelConfig, error: BaseException | str) -> bool:
    """Whether a provider-backed Codex failure should use the direct fallback."""
    if model_config.provider not in {"openai_compatible", "openai_responses"}:
        return False
    if isinstance(error, subprocess.TimeoutExpired):
        return True
    message = str(error).casefold()
    return any(marker in message for marker in _CODEX_TRANSPORT_MARKERS)


def cleanup_timed_out_compose_containers(overlay_task_path: Path, *, runner: Any = subprocess.run) -> dict[str, Any]:
    """Force-remove only containers owned by one timed-out staged overlay."""
    environment_path = (overlay_task_path / "environment").resolve()
    label_filter = f"label={_DOCKER_COMPOSE_WORKING_DIR_LABEL}={environment_path}"
    cleanup: dict[str, Any] = {
        "environment_path": str(environment_path),
        "label_filter": label_filter,
        "matched_container_ids": [],
        "removed_container_ids": [],
        "list_returncode": None,
        "remove_returncode": None,
        "errors": [],
    }
    try:
        listed = runner(
            ["docker", "ps", "-aq", "--filter", label_filter],
            capture_output=True,
            text=True,
            check=False,
            timeout=_CLEANUP_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        cleanup["errors"].append(f"docker container discovery failed: {exc}")
        return cleanup
    cleanup["list_returncode"] = listed.returncode
    if listed.returncode != 0:
        cleanup["errors"].append((listed.stderr or "docker ps failed").strip())
        return cleanup
    container_ids = [
        container_id
        for container_id in (line.strip() for line in listed.stdout.splitlines())
        if _DOCKER_CONTAINER_ID_RE.fullmatch(container_id)
    ]
    cleanup["matched_container_ids"] = container_ids
    if not container_ids:
        return cleanup
    try:
        removed = runner(
            ["docker", "rm", "-f", *container_ids],
            capture_output=True,
            text=True,
            check=False,
            timeout=_CLEANUP_TIMEOUT_SECONDS,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        cleanup["errors"].append(f"docker container removal failed: {exc}")
        return cleanup
    cleanup["remove_returncode"] = removed.returncode
    if removed.returncode != 0:
        cleanup["errors"].append((removed.stderr or "docker rm failed").strip())
        return cleanup
    cleanup["removed_container_ids"] = list(container_ids)
    return cleanup
