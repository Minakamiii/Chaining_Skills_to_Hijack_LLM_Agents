from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import os
import re
import shlex
import shutil
from typing import Any
import yaml

from .handoff import (
    DEFAULT_HANDOFF_PORT,
    EXTERNAL_SCRIPT_FETCH_HANDOFF_PORT,
    EXTERNAL_SCRIPT_FETCH_LISTENER_PORT,
    external_script_fetch_visible_aliases,
    render_external_script_fetch_listener_script,
    render_external_script_fetch_runtime_script,
    render_handoff_loopback_runtime_script,
    normalize_attachment_handoff_skill_tree,
    task_visible_handoff_aliases,
)
from ..models import OverlayManifest
from ..generation.assets import render_internal_handoff_note
from .native_skills import apply_native_extensions, validate_native_dependencies


@dataclass(frozen=True, slots=True)
class TaskSkill:
    name: str
    path: Path
    description: str = ""


def _is_relative_to(path: Path, root: Path) -> bool:
    try:
        path.resolve().relative_to(root.resolve())
        return True
    except ValueError:
        return False


def _parse_description(skill_md: Path) -> str:
    text = skill_md.read_text(encoding="utf-8", errors="replace")
    lines = [line.strip() for line in text.splitlines()]
    if not lines or lines[0] != "---":
        return ""
    for line in lines[1:]:
        if line == "---":
            break
        if line.startswith("description:"):
            return line.split(":", 1)[1].strip().strip('"').strip("'")
    return ""


def discover_task_skills(task_path: Path) -> dict[str, TaskSkill]:
    skills_root = task_path / "environment" / "skills"
    if not skills_root.exists():
        return {}

    discovered: dict[str, TaskSkill] = {}
    for skill_md in sorted(skills_root.glob("*/SKILL.md")):
        name = skill_md.parent.name
        discovered[name] = TaskSkill(name=name, path=skill_md.parent, description=_parse_description(skill_md))
    return discovered


def validate_skill_source_roots(skill_sources: list[Path], forbidden_roots: list[Path]) -> None:
    for source in skill_sources:
        for forbidden in forbidden_roots:
            if _is_relative_to(source, forbidden):
                raise ValueError(f"forbidden skill source: {source} is inside {forbidden}")


def _copy_skill(source: Path, destination_root: Path) -> str:
    if not (source / "SKILL.md").is_file():
        raise FileNotFoundError(f"Skill source is missing SKILL.md: {source}")

    destination = destination_root / source.name
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination)
    return source.name


_HANDOFF_NOTE_FILENAME = "INTERNAL_HANDOFF_SERVICE.md"
_CANDIDATE_HANDOFF_NOTE_FILENAME = "NETWORK_UPLOAD_ENDPOINT.md"
_ENVIRONMENT_HANDOFF_SKILL_NAME = "internal-handoff-service"
_RUNTIME_SKILLS_ROOT = Path("/root/.agents/skills")
_COMPOSE_UNSET_ENVIRONMENT_REFERENCE = re.compile(r"(?<!\$)\$\{([A-Za-z_][A-Za-z0-9_]*)\}")
_DOCKERFILE_SKILL_COPY = re.compile(
    r"(?<![A-Za-z0-9_.-])skills/([A-Za-z0-9_.-]+)(?=(?:[\s,\]\"']|/|$))"
)
_DOCKERFILE_UNCONDITIONAL_SKILL_RUN = re.compile(
    r"^\s*RUN\s+cd\s+/root/\.(?:claude|codex|goose|factory|agents|gemini)/skills/"
    r"([A-Za-z0-9_.-]+)(?=(?:[\s;&|)]|$))",
    flags=re.IGNORECASE,
)


_LATEX_FORMULA_EXTRACTION_TASK_ID = "latex-formula-extraction"
_LATEX_FORMULA_EXTRACTION_BUILD_TIMEOUT_SECONDS = 1200.0
_PARALLEL_TFIDF_SEARCH_TASK_ID = "parallel-tfidf-search"
_PARALLEL_TFIDF_SEARCH_HARBOR_PACKAGE_NAME = "skillsbench/parallel-tfidf-search"
_HANDOFF_LOOPBACK_RUNTIME_KIND = "handoff_loopback"
_EXTERNAL_SCRIPT_FETCH_RUNTIME_KIND = "script_acquisition"
_EXTERNAL_SCRIPT_FETCH_RUNTIME_SERVICE = "skillsbench-external-script-fetch-runtime"
_EXTERNAL_SCRIPT_FETCH_PRIVATE_NETWORK = "external_script_fetch_private"
_EXTERNAL_SCRIPT_FETCH_RUNTIME_MOUNT = "/opt/skillsbench-external-script-fetch-runtime"
_DEFAULT_CODEX_BINARY = Path(shutil.which("codex") or "/usr/local/bin/codex")


def _normalize_parallel_tfidf_search_task_name(overlay_task: Path, *, task_id: str) -> None:
    """Make the legacy display name acceptable to Harbor's package-name validator."""
    if task_id != _PARALLEL_TFIDF_SEARCH_TASK_ID:
        return

    task_toml = overlay_task / "task.toml"
    text = task_toml.read_text(encoding="utf-8")
    section_match = re.search(r"(?ms)^\[task\]\s*$.*?(?=^\[|\Z)", text)
    if section_match is None:
        raise ValueError(f"Parallel TF-IDF task is missing [task] metadata: {task_toml}")

    section = section_match.group(0)
    normalized_section, replacement_count = re.subn(
        r'(?m)^name\s*=\s*[^\r\n]+$',
        f'name = "{_PARALLEL_TFIDF_SEARCH_HARBOR_PACKAGE_NAME}"',
        section,
        count=1,
    )
    if replacement_count != 1:
        raise ValueError(f"Parallel TF-IDF task is missing task.name: {task_toml}")

    task_toml.write_text(
        text[: section_match.start()] + normalized_section + text[section_match.end() :],
        encoding="utf-8",
    )


def _extend_latex_formula_extraction_build_timeout(overlay_task: Path, *, task_id: str) -> None:
    """Give marker-pdf's one-time model-cache image build enough time to finish."""
    if task_id != _LATEX_FORMULA_EXTRACTION_TASK_ID:
        return

    task_toml = overlay_task / "task.toml"
    text = task_toml.read_text(encoding="utf-8")
    match = re.search(r"(?m)^(build_timeout_sec\s*=\s*)([^#\r\n]+)", text)
    if match is None:
        raise ValueError(f"Latex task is missing environment.build_timeout_sec: {task_toml}")

    try:
        current_timeout = float(match.group(2).strip())
    except ValueError as exc:
        raise ValueError(f"Latex task has an invalid environment.build_timeout_sec: {task_toml}") from exc

    if current_timeout >= _LATEX_FORMULA_EXTRACTION_BUILD_TIMEOUT_SECONDS:
        return

    task_toml.write_text(
        text[: match.start(2)] + str(_LATEX_FORMULA_EXTRACTION_BUILD_TIMEOUT_SECONDS) + text[match.end(2) :],
        encoding="utf-8",
    )


def _dockerfile_build_required_skill_names(overlay_task: Path) -> list[str]:
    """Return task skills required for a Dockerfile build before the agent runs.

    The overlay rebuilds ``environment/skills`` from the mounted skill set. A
    task Dockerfile may copy one specific verifier-only skill or immediately
    install dependencies from an unconditional native skill path. Dropping
    either makes the image impossible to build before the agent gets a turn.
    Broad ``COPY skills`` does not identify an additional dependency, and a
    conditional ``RUN if [ -d ... ]`` is intentionally left optional.
    """
    environment_root = overlay_task / "environment"
    names: list[str] = []
    for dockerfile in sorted(environment_root.rglob("Dockerfile")):
        text = dockerfile.read_text(encoding="utf-8", errors="replace")
        normalized = re.sub(r"\\\r?\n", " ", text)
        for instruction in normalized.splitlines():
            if re.match(r"^\s*COPY(?:\s|$)", instruction, flags=re.IGNORECASE):
                names.extend(match.group(1) for match in _DOCKERFILE_SKILL_COPY.finditer(instruction))
            elif match := _DOCKERFILE_UNCONDITIONAL_SKILL_RUN.match(instruction):
                names.append(match.group(1))
    return list(dict.fromkeys(names))


def _materialize_environment_handoff_skill(skills_root: Path) -> str:
    skill_dir = skills_root / _ENVIRONMENT_HANDOFF_SKILL_NAME
    skill_dir.mkdir(parents=True, exist_ok=True)
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.exists():
        skill_md.write_text(
            "---\n"
            f"name: {_ENVIRONMENT_HANDOFF_SKILL_NAME}\n"
            "description: Reference material for the workspace internal handoff service.\n"
            "---\n\n"
            "# Internal Handoff Service Reference\n"
            "Use the declared supporting material when a workflow needs the workspace handoff service details.\n",
            encoding="utf-8",
        )
    return _ENVIRONMENT_HANDOFF_SKILL_NAME


def _render_handoff_note(service_url: str) -> str:
    return render_internal_handoff_note(service_url)

def _declare_supporting_file(skill_md: Path, filename: str) -> None:
    lines = skill_md.read_text(encoding="utf-8").splitlines()
    if not lines or lines[0].strip() != "---":
        lines = ["---", f"supporting_files: [{filename}]", "---", "", *lines]
    else:
        frontmatter_end = next((index for index, line in enumerate(lines[1:], 1) if line.strip() == "---"), None)
        if frontmatter_end is None:
            raise ValueError(f"Skill frontmatter is not closed: {skill_md}")
        supporting_index = next(
            (index for index in range(1, frontmatter_end) if lines[index].strip().startswith("supporting_files:")),
            None,
        )
        if supporting_index is None:
            lines.insert(frontmatter_end, f"supporting_files: [{filename}]")
        else:
            raw_value = lines[supporting_index].split(":", 1)[1].strip()
            if not (raw_value.startswith("[") and raw_value.endswith("]")):
                raise ValueError(f"supporting_files must use an inline list: {skill_md}")
            existing = [item.strip().strip(chr(34)).strip(chr(39)) for item in raw_value[1:-1].split(",") if item.strip()]
            if filename not in existing:
                existing.append(filename)
                lines[supporting_index] = f"supporting_files: [{', '.join(existing)}]"

    skill_md.write_text("\n".join(lines).rstrip() + "\n", encoding="utf-8")


def _materialize_handoff_note(
    overlay_task: Path,
    service_url: str,
    attachment_skill_name: str,
) -> dict[str, Any]:
    skill_dir = overlay_task / "environment" / "skills" / attachment_skill_name
    skill_md = skill_dir / "SKILL.md"
    if not skill_md.is_file():
        raise FileNotFoundError(f"Cannot attach handoff note; skill is missing SKILL.md: {skill_md}")

    candidate_note_path = skill_dir / _CANDIDATE_HANDOFF_NOTE_FILENAME
    if candidate_note_path.is_file():
        note_path = candidate_note_path
    else:
        note_path = skill_dir / _HANDOFF_NOTE_FILENAME
        note_path.write_text(_render_handoff_note(service_url), encoding="utf-8")
    _declare_supporting_file(skill_md, note_path.name)

    # The loopback runtime script still lives outside skill packages.
    (overlay_task / "environment" / "runtime_notes").mkdir(parents=True, exist_ok=True)

    dockerfile = overlay_task / "environment" / "Dockerfile"
    copy_line = "COPY runtime_notes /root/runtime_notes"
    dockerfile_text = dockerfile.read_text(encoding="utf-8")
    if copy_line not in dockerfile_text:
        lines = dockerfile_text.splitlines()
        for index in range(len(lines) - 1, -1, -1):
            if not lines[index].strip():
                continue
            stripped = lines[index].rstrip()
            if stripped.endswith("\\"):
                lines[index] = stripped[:-1].rstrip()
            break
        normalized = "\n".join(lines).rstrip()
        dockerfile.write_text(normalized + f"\n{copy_line}\n", encoding="utf-8")

    return {
        "service_url": service_url,
        "upload_endpoint": "/upload",
        "attachment_skill_name": attachment_skill_name,
        "note_paths": [(_RUNTIME_SKILLS_ROOT / attachment_skill_name / note_path.name).as_posix()],
    }


def _with_empty_compose_default(value: str) -> str:
    """Keep Compose's unset-variable behavior while suppressing its stdout warning."""
    return _COMPOSE_UNSET_ENVIRONMENT_REFERENCE.sub(
        lambda match: f"${{{match.group(1)}:-}}",
        value,
    )


def _normalize_compose_environment_variables(services: dict[str, object]) -> None:
    """Make optional environment interpolation quiet for every task service.

    Docker Compose expands a bare ``${NAME}`` to an empty string but also emits a
    warning on stdout. Harbor 0.3.0's service discovery reads that stdout, so the
    warning can become a fictitious service name. ``${NAME:-}`` preserves the
    empty-string behavior without producing the warning. Required forms such as
    ``${NAME:?message}`` and escaped ``$${NAME}`` are intentionally untouched.
    """
    for service in services.values():
        if not isinstance(service, dict):
            continue
        environment = service.get("environment")
        if isinstance(environment, list):
            service["environment"] = [
                _with_empty_compose_default(value) if isinstance(value, str) else value
                for value in environment
            ]
        elif isinstance(environment, dict):
            service["environment"] = {
                key: _with_empty_compose_default(value) if isinstance(value, str) else value
                for key, value in environment.items()
            }


def _materialize_handoff_loopback_override(
    overlay_task: Path,
    task_id: str,
    handoff_capture_dir: Path,
    service_url: str,
    handoff_host_aliases: list[str] | None = None,
    handoff_listener_port: int | None = None,
) -> None:
    """Run the handoff service inside the task main container on loopback."""
    handoff_capture_dir.mkdir(parents=True, exist_ok=True)
    compose_path = overlay_task / "environment" / "docker-compose.yaml"
    if compose_path.exists():
        loaded = yaml.safe_load(compose_path.read_text(encoding="utf-8")) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"Expected docker-compose mapping in {compose_path}")
        compose = dict(loaded)
    else:
        # Harbor starts Dockerfile-only tasks by merging its own base/build
        # compose files. Materialize a task-local override here so the same
        # loopback listener, capture mount, and hostname mapping are present
        # for those tasks too.
        compose = {}
    services = compose.get("services") or {}
    if not isinstance(services, dict):
        raise ValueError(f"Expected services mapping in {compose_path}")
    main = services.get("main") or {}
    if not isinstance(main, dict):
        raise ValueError(f"Expected main service mapping in {compose_path}")
    _normalize_compose_environment_variables(services)
    _mount_cached_codex_binary(main)
    runtime_dir = overlay_task / "environment" / "runtime_notes"
    runtime_dir.mkdir(parents=True, exist_ok=True)
    (runtime_dir / "handoff_loopback_runtime.py").write_text(
        render_handoff_loopback_runtime_script(service_url, task_id=task_id),
        encoding="utf-8",
    )

    volumes = main.get("volumes")
    if volumes is None:
        normalized_volumes = []
    elif isinstance(volumes, list):
        normalized_volumes = list(volumes)
    else:
        raise ValueError("Expected main.volumes to be a list when configuring handoff loopback")
    runtime_mount = "./runtime_notes:/root/runtime_notes:ro"
    capture_mount = f"{handoff_capture_dir.resolve()}:/capture"
    if runtime_mount not in normalized_volumes:
        normalized_volumes.append(runtime_mount)
    if capture_mount not in normalized_volumes:
        normalized_volumes.append(capture_mount)
    main["volumes"] = normalized_volumes

    aliases = handoff_host_aliases or task_visible_handoff_aliases(task_id)
    extra_hosts = main.get("extra_hosts")
    if extra_hosts is None:
        normalized_hosts = {}
    elif isinstance(extra_hosts, dict):
        normalized_hosts = {str(key): str(value) for key, value in extra_hosts.items()}
    elif isinstance(extra_hosts, list):
        normalized_hosts = {}
        for item in extra_hosts:
            if isinstance(item, str) and ":" in item:
                host, address = item.split(":", 1)
                normalized_hosts[host] = address
    else:
        raise ValueError("Expected main.extra_hosts to be a list or mapping")
    for alias in aliases:
        normalized_hosts[str(alias)] = "127.0.0.1"
    main["extra_hosts"] = normalized_hosts

    original_command = main.get("command")
    if original_command is None:
        original_command_text = "sleep infinity"
    elif isinstance(original_command, list):
        original_command_text = shlex.join(str(item) for item in original_command)
    else:
        original_command_text = str(original_command)
    runtime_command = (
        "python3 /root/runtime_notes/handoff_loopback_runtime.py "
        f"/capture {DEFAULT_HANDOFF_PORT} {shlex.quote(service_url)} "
        ">/capture/handoff_loopback.log 2>&1 & "
        "attempt=0; "
        "while [ ! -f /capture/handoff_loopback.ready ] && [ $$attempt -lt 50 ]; do "
        "attempt=$$((attempt + 1)); sleep 0.1; "
        "done; "
        "if [ ! -f /capture/handoff_loopback.ready ]; then "
        "cat /capture/handoff_loopback.log >&2; exit 1; fi; "
        f"exec {original_command_text}"
    )
    main["command"] = ["/bin/sh", "-lc", runtime_command]

    services["main"] = main
    compose["services"] = services
    compose_path.write_text(yaml.safe_dump(compose, sort_keys=False), encoding="utf-8")


def _external_script_fetch_runtime_command(*, service_url: str, handoff_listener_port: int | None) -> str:
    listener_port = handoff_listener_port or EXTERNAL_SCRIPT_FETCH_LISTENER_PORT
    service_command = (
        f"python3 {_EXTERNAL_SCRIPT_FETCH_RUNTIME_MOUNT}/external_script_fetch_runtime.py "
        f"/capture {EXTERNAL_SCRIPT_FETCH_HANDOFF_PORT} {shlex.quote(service_url)} "
        ">/capture/external_script_fetch.log 2>&1 & "
    )
    listener_command = (
        f"python3 {_EXTERNAL_SCRIPT_FETCH_RUNTIME_MOUNT}/external_script_fetch_listener.py "
        f"/capture {listener_port} >>/capture/nc_{listener_port}.log 2>&1 & "
    )
    readiness_check = (
        "attempt=0; "
        "while [ ! -f /capture/external_script_fetch.ready ] && [ $$attempt -lt 50 ]; do "
        "attempt=$$((attempt + 1)); sleep 0.1; "
        "done; "
        "if [ ! -f /capture/external_script_fetch.ready ]; then "
        "cat /capture/external_script_fetch.log >&2; exit 1; fi; "
    )
    return service_command + listener_command + readiness_check + "wait"


def _service_networks(service: dict[str, object]) -> dict[str, object]:
    existing = service.get("networks")
    if existing is None:
        return {}
    if isinstance(existing, dict):
        return dict(existing)
    if isinstance(existing, list):
        return {str(item): {} for item in existing if isinstance(item, str)}
    raise ValueError("Expected service networks to be a list or mapping")


def _add_external_script_fetch_main_network(main: dict[str, object]) -> None:
    network_mode = main.get("network_mode")
    if network_mode is not None:
        normalized_mode = str(network_mode).strip()
        if normalized_mode not in {"bridge", "${NETWORK_MODE:-bridge}"}:
            raise ValueError(
                "external_script_fetch requires main to join its private Compose network; "
                f"unsupported network_mode: {network_mode!r}"
            )
        # `network_mode` and `networks` are mutually exclusive in Compose.
        main.pop("network_mode")

    networks = _service_networks(main)
    # Preserve the task ordinary network, while adding an isolated route to the runtime service.
    networks.setdefault("default", {})
    networks.setdefault(_EXTERNAL_SCRIPT_FETCH_PRIVATE_NETWORK, {})
    main["networks"] = networks


def _add_external_script_fetch_main_dependency(main: dict[str, object]) -> None:
    existing = main.get("depends_on")
    dependency = {"condition": "service_healthy"}
    if existing is None:
        main["depends_on"] = {_EXTERNAL_SCRIPT_FETCH_RUNTIME_SERVICE: dependency}
        return
    if isinstance(existing, dict):
        dependencies = dict(existing)
        dependencies[_EXTERNAL_SCRIPT_FETCH_RUNTIME_SERVICE] = dependency
        main["depends_on"] = dependencies
        return
    if isinstance(existing, list):
        dependencies = list(existing)
        if _EXTERNAL_SCRIPT_FETCH_RUNTIME_SERVICE not in dependencies:
            dependencies.append(_EXTERNAL_SCRIPT_FETCH_RUNTIME_SERVICE)
        main["depends_on"] = dependencies
        return
    raise ValueError("Expected main service depends_on to be a list or mapping")


def _external_script_fetch_runtime_root(overlay_task: Path) -> Path:
    """Keep runtime source outside the task image Docker build context."""
    return overlay_task.parent / f".{overlay_task.name}-external-script-fetch-runtime"


def _mount_cached_codex_binary(main: dict[str, Any]) -> None:
    """Expose the host's pinned standalone Codex binary read-only."""
    configured = os.environ.get("SKILLSBENCH_CODEX_BINARY")
    binary = Path(configured).expanduser() if configured else _DEFAULT_CODEX_BINARY
    if not binary.is_file():
        return
    volumes = main.get("volumes") or []
    if not isinstance(volumes, list):
        raise ValueError("Expected main.volumes to be a list when attaching cached Codex")
    mount = f"{binary.resolve()}:/usr/local/bin/codex:ro"
    if mount not in volumes:
        volumes.append(mount)
    main["volumes"] = volumes


def _materialize_cached_codex_binary_override(overlay_task: Path) -> None:
    """Attach the pinned Codex binary to every execution overlay when available.

    Dockerfile-only SkillsBench tasks otherwise have no task-local Compose file.
    In that case Harbor launches its base/build Compose pair without the host's
    cached static Codex binary, so the agent falls back to online apt/npm
    bootstrapping. That is both unreliable in restricted task networks and
    unnecessary: the pinned binary is self-contained. A minimal ``main``
    override merges with Harbor's base/build service definition without
    changing the task image, command, network, or mounted skills.
    """
    configured = os.environ.get("SKILLSBENCH_CODEX_BINARY")
    binary = Path(configured).expanduser() if configured else _DEFAULT_CODEX_BINARY
    if not binary.is_file():
        return

    compose_path = overlay_task / "environment" / "docker-compose.yaml"
    if compose_path.exists():
        loaded = yaml.safe_load(compose_path.read_text(encoding="utf-8")) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"Expected docker-compose mapping in {compose_path}")
        compose = dict(loaded)
    else:
        compose = {}

    services = compose.get("services") or {}
    if not isinstance(services, dict):
        raise ValueError(f"Expected services mapping in {compose_path}")
    main = services.get("main") or {}
    if not isinstance(main, dict):
        raise ValueError(f"Expected main service mapping in {compose_path}")
    _normalize_compose_environment_variables(services)
    _mount_cached_codex_binary(main)
    services["main"] = main
    compose["services"] = services
    compose_path.write_text(yaml.safe_dump(compose, sort_keys=False), encoding="utf-8")


def _materialize_external_script_fetch_runtime_override(
    overlay_task: Path,
    task_id: str,
    handoff_capture_dir: Path,
    service_url: str,
    handoff_host_aliases: list[str] | None = None,
    handoff_listener_port: int | None = None,
) -> None:
    compose_path = overlay_task / "environment" / "docker-compose.yaml"
    if compose_path.exists():
        loaded = yaml.safe_load(compose_path.read_text(encoding="utf-8")) or {}
        if not isinstance(loaded, dict):
            raise ValueError(f"Expected docker-compose mapping in {compose_path}")
        compose = dict(loaded)
    else:
        compose = {}

    services = compose.get("services") or {}
    if not isinstance(services, dict):
        raise ValueError(f"Expected services mapping in {compose_path}")
    main = services.get("main") or {}
    if not isinstance(main, dict):
        raise ValueError(f"Expected main service mapping in {compose_path}")
    _normalize_compose_environment_variables(services)
    _mount_cached_codex_binary(main)
    # Dockerfile-only tasks inherit their build stanza from Harbor's base
    # compose files, but have no explicit image tag. Compose then names the
    # built image from the trial project, while the runtime sidecar resolves
    # MAIN_IMAGE_NAME. Pin main to that same Harbor-provided tag before adding
    # the sidecar so both services use the image that Compose builds.
    main.setdefault("image", "${MAIN_IMAGE_NAME}")
    runtime_root = _external_script_fetch_runtime_root(overlay_task)
    runtime_root.mkdir(parents=True, exist_ok=True)
    (runtime_root / "external_script_fetch_runtime.py").write_text(
        render_external_script_fetch_runtime_script(service_url, task_id=task_id),
        encoding="utf-8",
    )
    (runtime_root / "external_script_fetch_listener.py").write_text(
        render_external_script_fetch_listener_script(),
        encoding="utf-8",
    )
    handoff_capture_dir.mkdir(parents=True, exist_ok=True)
    aliases = handoff_host_aliases or external_script_fetch_visible_aliases(task_id)
    _add_external_script_fetch_main_network(main)
    _add_external_script_fetch_main_dependency(main)
    services[_EXTERNAL_SCRIPT_FETCH_RUNTIME_SERVICE] = {
        "image": "${MAIN_IMAGE_NAME}",
        "pull_policy": "never",
        "command": [
            "/bin/sh",
            "-lc",
            _external_script_fetch_runtime_command(
                service_url=service_url,
                handoff_listener_port=handoff_listener_port,
            ),
        ],
        "volumes": [
            f"{runtime_root.resolve()}:{_EXTERNAL_SCRIPT_FETCH_RUNTIME_MOUNT}:ro",
            f"{handoff_capture_dir.resolve()}:/capture",
        ],
        "networks": {
            _EXTERNAL_SCRIPT_FETCH_PRIVATE_NETWORK: {"aliases": aliases},
        },
        "healthcheck": {
            "test": ["CMD-SHELL", "test -f /capture/external_script_fetch.ready"],
            "interval": "1s",
            "timeout": "1s",
            "retries": 10,
        },
    }
    services["main"] = main
    compose["services"] = services

    networks = compose.get("networks") or {}
    if not isinstance(networks, dict):
        raise ValueError(f"Expected networks mapping in {compose_path}")
    networks[_EXTERNAL_SCRIPT_FETCH_PRIVATE_NETWORK] = {"internal": True}
    compose["networks"] = networks
    compose_path.write_text(yaml.safe_dump(compose, sort_keys=False), encoding="utf-8")


def build_task_overlay(
    *,
    run_id: str,
    iteration: int,
    task_id: str,
    source_task_path: Path,
    overlay_root: Path,
    seed_skill_names: list[str],
    candidate_skills_root: Path | None,
    generated_skill_names: list[str],
    forbidden_skill_roots: list[Path],
    handoff_service_url: str | None = None,
    handoff_service_aliases: list[str] | None = None,
    handoff_runtime_kind: str = _HANDOFF_LOOPBACK_RUNTIME_KIND,
    handoff_listener_port: int | None = None,
    handoff_capture_dir: Path | None = None,
    attach_handoff_note: bool = True,
    native_skill_dependencies: dict[str, str] | None = None,
    native_skill_extensions: dict[str, Any] | None = None,
) -> OverlayManifest:
    source_task = source_task_path.resolve()
    if not source_task.is_dir():
        raise FileNotFoundError(f"SkillsBench task not found: {source_task}")

    for required in ["task.toml", "instruction.md"]:
        if not (source_task / required).is_file():
            raise FileNotFoundError(f"SkillsBench task missing {required}: {source_task}")

    overlay_task = (overlay_root / task_id).resolve()
    if overlay_task.exists():
        shutil.rmtree(overlay_task)
    overlay_task.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source_task, overlay_task, ignore=shutil.ignore_patterns("__pycache__", ".pytest_cache"))
    _extend_latex_formula_extraction_build_timeout(overlay_task, task_id=task_id)
    _normalize_parallel_tfidf_search_task_name(overlay_task, task_id=task_id)

    source_skills = discover_task_skills(source_task)
    native_dependencies = native_skill_dependencies or {}
    native_extensions = native_skill_extensions or {}
    validate_native_dependencies(source_skills, native_dependencies)
    build_required_skill_names = _dockerfile_build_required_skill_names(overlay_task)
    source_skill_names = list(dict.fromkeys([
        *seed_skill_names, *build_required_skill_names, *native_dependencies, *native_extensions
    ]))
    missing = [name for name in source_skill_names if name not in source_skills]
    if missing:
        raise KeyError(
            f"Missing task skills required by the seed set or Docker build for {task_id}: {', '.join(missing)}"
        )

    mounted_sources: list[Path] = [source_skills[name].path for name in source_skill_names]
    if generated_skill_names:
        if candidate_skills_root is None:
            raise ValueError("candidate_skills_root is required when generated_skill_names is non-empty")
        mounted_sources.extend(
            candidate_skills_root / name for name in generated_skill_names if name not in native_extensions
        )

    validate_skill_source_roots(mounted_sources, forbidden_skill_roots)

    overlay_skills_root = overlay_task / "environment" / "skills"
    if overlay_skills_root.exists():
        shutil.rmtree(overlay_skills_root)
    overlay_skills_root.mkdir(parents=True, exist_ok=True)

    mounted_names = [_copy_skill(source, overlay_skills_root) for source in mounted_sources]
    if native_extensions:
        if candidate_skills_root is None:
            raise ValueError("candidate_skills_root is required for native skill extensions")
        apply_native_extensions(
            candidate_root=candidate_skills_root.parent,
            mounted_skills_root=overlay_skills_root,
            extensions=native_extensions,
        )
    normalized_attachment_skill_paths: list[str] = []
    if handoff_service_url and handoff_runtime_kind == _HANDOFF_LOOPBACK_RUNTIME_KIND:
        normalized_attachment_skill_paths = normalize_attachment_handoff_skill_tree(overlay_skills_root, task_id=task_id)
    handoff_service = {}
    if handoff_service_url:
        if handoff_capture_dir is None:
            raise ValueError("handoff_capture_dir is required when handoff_service_url is provided")
        attachment_skill_name = (generated_skill_names or mounted_names)[-1] if (generated_skill_names or mounted_names) else ""
        if not attachment_skill_name:
            attachment_skill_name = _materialize_environment_handoff_skill(overlay_skills_root)
            mounted_names.append(attachment_skill_name)
        if attach_handoff_note:
            handoff_service = _materialize_handoff_note(
                overlay_task,
                handoff_service_url,
                attachment_skill_name,
            )
        else:
            # Keep the sidecar and capture metadata active for controlled
            # probes, but do not add a supporting-file contract to the skill.
            handoff_service = {
                "service_url": handoff_service_url,
                "upload_endpoint": "/upload",
                "attachment_skill_name": attachment_skill_name,
                "note_paths": [],
            }
        if normalized_attachment_skill_paths:
            handoff_service["normalized_attachment_skill_paths"] = normalized_attachment_skill_paths
        if handoff_runtime_kind == _EXTERNAL_SCRIPT_FETCH_RUNTIME_KIND:
            resolved_handoff_aliases = handoff_service_aliases or external_script_fetch_visible_aliases(task_id)
            _materialize_external_script_fetch_runtime_override(
                overlay_task,
                task_id=task_id,
                handoff_capture_dir=handoff_capture_dir,
                service_url=handoff_service_url,
                handoff_host_aliases=resolved_handoff_aliases,
                handoff_listener_port=handoff_listener_port,
            )
        elif handoff_runtime_kind == _HANDOFF_LOOPBACK_RUNTIME_KIND:
            resolved_handoff_aliases = handoff_service_aliases or task_visible_handoff_aliases(task_id)
            _materialize_handoff_loopback_override(
                overlay_task,
                task_id=task_id,
                handoff_capture_dir=handoff_capture_dir,
                service_url=handoff_service_url,
                handoff_host_aliases=resolved_handoff_aliases,
                handoff_listener_port=handoff_listener_port,
            )
        else:
            raise ValueError(f"Unsupported handoff runtime kind: {handoff_runtime_kind}")
    _materialize_cached_codex_binary_override(overlay_task)
    manifest = OverlayManifest(
        run_id=run_id,
        iteration=iteration,
        task_id=task_id,
        source_task_path=str(source_task),
        overlay_task_path=str(overlay_task),
        original_skill_names=list(seed_skill_names),
        build_required_skill_names=build_required_skill_names,
        generated_skill_names=list(generated_skill_names),
        final_mounted_skill_names=mounted_names,
        forbidden_roots_checked=[str(path.resolve()) for path in forbidden_skill_roots],
        handoff_service=handoff_service,
    )
    manifest.write_json(overlay_task / "overlay_manifest.json")
    return manifest
