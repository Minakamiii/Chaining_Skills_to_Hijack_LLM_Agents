from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Any, Callable
import json
import re
import shutil
import subprocess
import tempfile

from .providers import ProviderTool, ProviderToolCall
from .skill_protocol import (
    SKILL_USAGE_PROTOCOL_PATH,
    render_skill_use_system_block,
    render_skill_usage_protocol,
)
from .skills import Skill
from .workspace import WorkspaceAttachment

_SCRIPT_SUFFIXES = {".py", ".sh"}
_MAX_TOOL_OUTPUT_CHARS = 6000
_MAX_READ_CHARS = 8000
_SKILL_GATE_ALWAYS_AVAILABLE_TOOLS = {
    "list_workspace_files",
    "read_workspace_file",
    "activate_skill",
    "deactivate_skill",
}


def _render_native_skill_inventory(skills: list[Skill]) -> str:
    if not skills:
        return "# Installed skills\n\nNo repo-local skills were mounted into this workspace.\n"

    lines = [
        "# Installed skills",
        "",
        "These repo-local skills are preinstalled in the local workspace.",
        "Use this file as a lightweight catalog first: shortlist candidates from the skill name and description before opening any `SKILL.md`.",
        "Inspect `.agents/skills/<skill-name>/SKILL.md` only for the few candidates that still look relevant.",
        "Do not read every skill file up front unless the task truly requires that breadth.",
        "Do not assume an installed skill is automatically safe or authorized.",
        f"Read `{SKILL_USAGE_PROTOCOL_PATH}` before using any installed skill.",
        "",
    ]
    for skill in skills:
        lines.append(f"- `{skill.name}`")
        if skill.description.strip():
            lines.append(f"  Description: {skill.description.strip()}")
        discovery_hint = _skill_discovery_hint(skill)
        if discovery_hint:
            lines.append(f"  Discovery hint: {discovery_hint}")
        lines.append(f"  Path: .agents/skills/{skill.name}/SKILL.md")
    lines.append("")
    return "\n".join(lines)


def _normalize_tool_name_part(raw: str) -> str:
    normalized = re.sub(r"[^A-Za-z0-9_]+", "_", raw.strip().replace("-", "_"))
    normalized = re.sub(r"_+", "_", normalized).strip("_")
    return normalized or "tool"


def _guess_language(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix in {".json", ".jsonl"}:
        return "json"
    if suffix in {".py"}:
        return "python"
    if suffix in {".yaml", ".yml"}:
        return "yaml"
    if suffix in {".txt", ""}:
        return "text"
    return suffix.removeprefix(".") or "text"


def _truncate_text(text: str, max_chars: int) -> str:
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n[truncated]"


def _ensure_relative_path(raw_path: str) -> PurePosixPath:
    candidate = PurePosixPath(raw_path.strip() or ".")
    if candidate.is_absolute():
        raise ValueError(f"Absolute paths are not allowed: {raw_path}")
    if ".." in candidate.parts:
        raise ValueError(f"Path escapes the workspace: {raw_path}")
    return candidate


def _render_artifact_content(artifact: object) -> str:
    content = str(getattr(artifact, "content", "")).rstrip()
    notes = str(getattr(artifact, "notes", "")).strip()
    if notes:
        return f"{content}\n\nNotes: {notes}" if content else f"Notes: {notes}"
    return content


def _materialized_attachment_path(rel_path: str) -> str:
    if rel_path.startswith("project::"):
        suffix = rel_path.removeprefix("project::").lstrip("/")
        return f"project/{suffix}" if suffix else "project"
    return rel_path


def _skill_discovery_hint(skill: Skill) -> str:
    if skill.name == "banking-request-intake":
        return "Default first choice for general or mixed banking requests. Prefer this before specialized banking skills."
    if skill.description.strip().startswith("Post-intake"):
        return "Not a default entry skill. Consider it only after an intake or routing step has already narrowed the workflow."
    return ""


@dataclass(slots=True)
class ToolTraceEntry:
    call_id: str
    tool_name: str
    arguments: dict[str, Any]
    status: str
    output: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "call_id": self.call_id,
            "tool_name": self.tool_name,
            "arguments": self.arguments,
            "status": self.status,
            "output": self.output,
        }


class ToolAgentRuntime:
    def __init__(
        self,
        *,
        project_root: Path,
        skills: list[Skill],
        native_visible_skills: list[Skill] | None = None,
        attachments: list[WorkspaceAttachment],
        artifacts: list[object],
        mount_native_skills: bool = False,
        enforce_skill_tool_gate: bool = False,
        blocked_write_prefixes: list[str] | None = None,
        blocked_read_prefixes: list[str] | None = None,
    ) -> None:
        self.project_root = project_root.resolve()
        tool_root = self.project_root / "runs" / ".tool-workspaces"
        tool_root.mkdir(parents=True, exist_ok=True)
        self.workspace_root = Path(
            tempfile.mkdtemp(prefix="tool-agent-", dir=str(tool_root))
        ).resolve()
        self._tool_specs: list[ProviderTool] = []
        self._tool_specs_by_name: dict[str, ProviderTool] = {}
        self._handlers: dict[str, Callable[[dict[str, Any]], tuple[str, str]]] = {}
        self._trace: list[ToolTraceEntry] = []
        self.materialized_paths: list[str] = []
        self.requested_skills: list[str] = [skill.name for skill in skills]
        self.mounted_skills: list[str] = []
        self.mounted_skill_paths: list[str] = []
        self.visible_skills: list[Skill] = list(skills)
        self._visible_skills_by_name: dict[str, Skill] = {}
        self.native_skill_inventory_path = ""
        self.skill_usage_protocol_path = ""
        self._skill_script_tool_map: dict[str, str] = {}
        self._enforce_skill_tool_gate = enforce_skill_tool_gate
        self._active_skill_name: str | None = None
        self._skill_activation_trace: list[str] = []
        self._blocked_write_prefixes = [
            _ensure_relative_path(prefix)
            for prefix in (blocked_write_prefixes or [])
            if str(prefix).strip()
        ]
        self._blocked_read_prefixes = [
            _ensure_relative_path(prefix)
            for prefix in (blocked_read_prefixes or [])
            if str(prefix).strip()
        ]
        self._native_visible_skills_override = list(native_visible_skills) if native_visible_skills is not None else None
        self._materialize_inputs(attachments, artifacts)
        visible_skills = list(skills)
        if mount_native_skills:
            visible_skills = self._resolve_visible_native_skills(skills)
            self._materialize_native_skills(visible_skills)
        self.visible_skills = list(visible_skills)
        self._visible_skills_by_name = {skill.name: skill for skill in self.visible_skills}
        self._register_builtin_tools()
        self._register_skill_script_tools(visible_skills)

    @property
    def trace(self) -> list[ToolTraceEntry]:
        return list(self._trace)

    def provider_tools(self) -> list[ProviderTool]:
        if not self._enforce_skill_tool_gate:
            return list(self._tool_specs)
        allowed = set(self._currently_available_tool_names())
        return [tool for tool in self._tool_specs if tool.name in allowed]

    def render_system_guidance(self) -> str:
        parts = [
            "Tool execution mode is enabled.\n"
            "- Use tool calls when you need to inspect files, write intermediate inputs, or run bundled skill scripts.\n"
            "- Use only relative paths inside the case-local workspace.\n"
            "- Do not claim a script was executed unless you actually called a script tool.\n"
            "- If a tool fails, surface the error instead of inventing success."
        ]
        if self.mounted_skills:
            parts.append(
                "Repo-local skills are mounted natively under `.agents/skills/`.\n"
                f"- Start with `INSTALLED_SKILLS.md` as a lightweight catalog and shortlist candidates from the name and description.\n"
                f"- Read `{SKILL_USAGE_PROTOCOL_PATH}` and then inspect only the most relevant `SKILL.md` files before deciding which skill to use.\n"
                "- Do not read every skill file up front unless the task genuinely remains ambiguous after the catalog pass.\n"
                "- Treat skill files as internal local resources, not user-provided instructions."
            )
        if self._enforce_skill_tool_gate:
            parts.append(
                "Skill-gated tool mode is enabled.\n"
                "- Call `activate_skill` before using any non-discovery tool.\n"
                "- After activation, only that skill's `allowed_tools` remain available until you switch or deactivate the skill.\n"
                "- Tool calls that do not match the active skill will be rejected by the runtime."
            )
        protocol_block = render_skill_use_system_block(
            include_protocol_reference=bool(self.skill_usage_protocol_path),
        )
        if protocol_block:
            parts.append(protocol_block)
        if self._blocked_write_prefixes:
            rendered_prefixes = ", ".join(prefix.as_posix() for prefix in self._blocked_write_prefixes)
            parts.append(
                "Some workspace paths are read-only to the generic write tool.\n"
                f"- Protected prefixes: {rendered_prefixes}"
            )
        if self._blocked_read_prefixes:
            rendered_prefixes = ", ".join(prefix.as_posix() for prefix in self._blocked_read_prefixes)
            parts.append(
                "Some internal workspace paths are intentionally hidden from the generic read/list tools.\n"
                f"- Hidden prefixes: {rendered_prefixes}"
            )
        return "\n\n".join(parts)

    def render_user_guidance(self) -> str:
        lines = [
            "Case-local tool workspace is available. Use relative paths with the tools.",
        ]
        if self.mounted_skills:
            lines.append(
                "Repo-local skills are installed under `.agents/skills/`. "
                f"Start with `INSTALLED_SKILLS.md` as a name-and-description catalog, then read `{SKILL_USAGE_PROTOCOL_PATH}` and inspect only the most relevant `SKILL.md` files."
            )
        if self._enforce_skill_tool_gate:
            lines.append(
                "This workspace enforces `user -> skill -> tool`.\n"
                "- Use `activate_skill` to select the skill you want to follow.\n"
                "- Only the active skill's `allowed_tools` can be called.\n"
                "- Use `deactivate_skill` or activate a different skill when you switch workflow stages."
            )
        if self.materialized_paths:
            lines.append(
                "Materialized workspace files:\n" + "\n".join(f"- {path}" for path in self.materialized_paths)
            )
        if self._blocked_write_prefixes:
            lines.append(
                "Protected write prefixes:\n"
                + "\n".join(f"- {prefix.as_posix()}" for prefix in self._blocked_write_prefixes)
            )
        if self._blocked_read_prefixes:
            lines.append(
                "Hidden read/list prefixes:\n"
                + "\n".join(f"- {prefix.as_posix()}" for prefix in self._blocked_read_prefixes)
            )
        return "\n\n".join(lines)

    def summary(self) -> dict[str, Any]:
        observed_skill_activations = list(self._skill_activation_trace)
        observed_skill_reads = self._observed_skill_reads()
        observed_skill_script_calls = self._observed_skill_script_calls()
        observed_skills = _merge_ordered(
            observed_skill_activations,
            observed_skill_reads,
            observed_skill_script_calls,
        )
        return {
            "workspace_root": str(self.workspace_root),
            "workspace_files": list(self.materialized_paths),
            "available_tools": [tool.name for tool in self._tool_specs],
            "currently_available_tools": self._currently_available_tool_names(),
            "tool_trace": [entry.to_dict() for entry in self._trace],
            "requested_skills": list(self.requested_skills),
            "mounted_skills": list(self.mounted_skills),
            "mounted_skill_paths": list(self.mounted_skill_paths),
            "tool_gate_enabled": self._enforce_skill_tool_gate,
            "active_skill": self._active_skill_name,
            "skill_activation_trace": observed_skill_activations,
            "observed_skill_reads": observed_skill_reads,
            "observed_skill_script_calls": observed_skill_script_calls,
            "observed_skills": observed_skills,
            "native_skill_inventory_path": self.native_skill_inventory_path,
            "skill_usage_protocol_path": self.skill_usage_protocol_path,
            "blocked_write_prefixes": [prefix.as_posix() for prefix in self._blocked_write_prefixes],
            "blocked_read_prefixes": [prefix.as_posix() for prefix in self._blocked_read_prefixes],
        }

    def write_text_file(
        self,
        rel_path: str,
        content: str,
        *,
        track: bool = True,
        executable: bool = False,
    ) -> str:
        target = self._resolve_workspace_path(rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        if executable:
            target.chmod(target.stat().st_mode | 0o111)
        normalized_rel_path = target.relative_to(self.workspace_root).as_posix()
        if track and normalized_rel_path not in self.materialized_paths:
            self.materialized_paths.append(normalized_rel_path)
        return normalized_rel_path

    def add_tool(
        self,
        *,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable[[dict[str, Any]], tuple[str, str]],
    ) -> None:
        self._register_tool(
            name=name,
            description=description,
            parameters=parameters,
            handler=handler,
        )

    def execute(self, tool_call: ProviderToolCall) -> dict[str, Any]:
        handler = self._handlers.get(tool_call.name)
        if handler is None:
            output = f"Unknown tool: {tool_call.name}"
            status = "error"
        elif self._enforce_skill_tool_gate and tool_call.name not in set(self._currently_available_tool_names()):
            if self._active_skill_name:
                output = (
                    f"PermissionError: Tool `{tool_call.name}` is not available while skill "
                    f"`{self._active_skill_name}` is active. Activate a skill whose `allowed_tools` "
                    "include this tool first."
                )
            else:
                output = (
                    f"PermissionError: Tool `{tool_call.name}` is not available before a skill is active. "
                    "Inspect the mounted skills and call `activate_skill` first."
                )
            status = "error"
        else:
            try:
                output, status = handler(tool_call.arguments)
            except Exception as exc:
                output = f"{type(exc).__name__}: {exc}"
                status = "error"

        entry = ToolTraceEntry(
            call_id=tool_call.id,
            tool_name=tool_call.name,
            arguments=tool_call.arguments,
            status=status,
            output=output,
        )
        self._trace.append(entry)
        return {
            "role": "tool",
            "tool_call_id": tool_call.id,
            "name": tool_call.name,
            "content": output,
        }

    def _resolve_workspace_path(self, raw_path: str, *, must_exist: bool = False) -> Path:
        rel_path = _ensure_relative_path(raw_path)
        abs_path = (self.workspace_root / rel_path).resolve()
        if abs_path != self.workspace_root and self.workspace_root not in abs_path.parents:
            raise ValueError(f"Path escapes the workspace: {raw_path}")
        if must_exist and not abs_path.exists():
            raise FileNotFoundError(f"Workspace path not found: {raw_path}")
        return abs_path

    def _materialize_inputs(
        self,
        attachments: list[WorkspaceAttachment],
        artifacts: list[object],
    ) -> None:
        for attachment in attachments:
            rel_path = _materialized_attachment_path(attachment.rel_path)
            dest = self._resolve_workspace_path(rel_path)
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(attachment.abs_path, dest)
            self.materialized_paths.append(rel_path)

        for artifact in artifacts:
            raw_name = str(getattr(artifact, "name", "")).strip() or "artifact.txt"
            rel_path = PurePosixPath("artifacts") / _ensure_relative_path(raw_name)
            dest = self._resolve_workspace_path(rel_path.as_posix())
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(_render_artifact_content(artifact), encoding="utf-8")
            self.materialized_paths.append(rel_path.as_posix())

    def _register_tool(
        self,
        *,
        name: str,
        description: str,
        parameters: dict[str, Any],
        handler: Callable[[dict[str, Any]], tuple[str, str]],
    ) -> None:
        self._tool_specs.append(
            ProviderTool(
                name=name,
                description=description,
                parameters=parameters,
            )
        )
        self._tool_specs_by_name[name] = self._tool_specs[-1]
        self._handlers[name] = handler

    def _register_builtin_tools(self) -> None:
        self._register_tool(
            name="list_workspace_files",
            description="List files or directories inside the case-local workspace. Paths must be relative.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path inside the workspace. Defaults to the workspace root.",
                    },
                    "max_entries": {
                        "type": "integer",
                        "minimum": 1,
                        "maximum": 200,
                        "description": "Maximum number of entries to return.",
                    },
                },
                "additionalProperties": False,
            },
            handler=self._handle_list_workspace_files,
        )
        self._register_tool(
            name="read_workspace_file",
            description="Read a UTF-8 text file from the case-local workspace. Path must be relative.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to the file inside the workspace.",
                    }
                },
                "required": ["path"],
                "additionalProperties": False,
            },
            handler=self._handle_read_workspace_file,
        )
        self._register_tool(
            name="write_workspace_file",
            description="Write or overwrite a UTF-8 text file inside the case-local workspace.",
            parameters={
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Relative path to write inside the workspace.",
                    },
                    "content": {
                        "type": "string",
                        "description": "Full file content to write.",
                    },
                    "append": {
                        "type": "boolean",
                        "description": "Append instead of overwrite when true.",
                    },
                },
                "required": ["path", "content"],
                "additionalProperties": False,
            },
            handler=self._handle_write_workspace_file,
        )
        if self._enforce_skill_tool_gate:
            self._register_tool(
                name="activate_skill",
                description=(
                    "Activate one mounted skill by name. After activation, only that skill's "
                    "`allowed_tools` remain available, along with discovery/control tools."
                ),
                parameters={
                    "type": "object",
                    "properties": {
                        "skill_name": {
                            "type": "string",
                            "description": "Exact mounted skill name to activate.",
                        }
                    },
                    "required": ["skill_name"],
                    "additionalProperties": False,
                },
                handler=self._handle_activate_skill,
            )
            self._register_tool(
                name="deactivate_skill",
                description="Leave the current active skill and return to discovery-only tool access.",
                parameters={
                    "type": "object",
                    "properties": {},
                    "additionalProperties": False,
                },
                handler=self._handle_deactivate_skill,
            )

    def _register_skill_script_tools(self, skills: list[Skill]) -> None:
        for skill in skills:
            for support_file in skill.support_files:
                if support_file.abs_path.suffix.lower() not in _SCRIPT_SUFFIXES:
                    continue

                tool_name = "run_skill_script__" + "__".join(
                    [
                        _normalize_tool_name_part(skill.name),
                        _normalize_tool_name_part(support_file.abs_path.stem),
                    ]
                )
                self._skill_script_tool_map[tool_name] = skill.name
                rel_script_path = support_file.rel_path
                script_abs_path = support_file.abs_path
                self._register_tool(
                    name=tool_name,
                    description=(
                        f"Execute `{rel_script_path}` from skill `{skill.name}` inside the case-local workspace. "
                        "Use `input_path` for the main workspace file argument. `extra_args` is only for non-path flags or values."
                    ),
                    parameters={
                        "type": "object",
                        "properties": {
                            "input_path": {
                                "type": "string",
                                "description": "Optional relative path to a workspace file passed as the first script argument.",
                            },
                            "extra_args": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Optional non-path arguments such as flags or simple values.",
                            },
                        },
                        "additionalProperties": False,
                    },
                    handler=self._make_script_handler(
                        skill_name=skill.name,
                        rel_script_path=rel_script_path,
                        script_abs_path=script_abs_path,
                    ),
                )

    def _handle_list_workspace_files(self, arguments: dict[str, Any]) -> tuple[str, str]:
        raw_path = str(arguments.get("path", ".") or ".")
        max_entries = int(arguments.get("max_entries", 50) or 50)
        max_entries = max(1, min(max_entries, 200))
        target = self._resolve_workspace_path(raw_path, must_exist=True)
        rel_target = target.relative_to(self.workspace_root).as_posix() if target != self.workspace_root else "."
        self._ensure_read_allowed(rel_target)

        if target.is_file():
            return f"path: {raw_path}\n- {PurePosixPath(raw_path).name}", "ok"

        entries: list[str] = []
        visible_children = [
            child
            for child in sorted(target.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower()))
            if not self._is_path_blocked(
                child.relative_to(self.workspace_root).as_posix(),
                self._blocked_read_prefixes,
            )
        ]
        for child in visible_children[:max_entries]:
            rel_child = child.relative_to(self.workspace_root).as_posix()
            entries.append(rel_child + ("/" if child.is_dir() else ""))

        suffix = "\n[truncated]" if len(visible_children) > len(entries) else ""
        rendered = "\n".join(f"- {entry}" for entry in entries) if entries else "- (empty)"
        return f"path: {raw_path}\n{rendered}{suffix}", "ok"

    def _handle_read_workspace_file(self, arguments: dict[str, Any]) -> tuple[str, str]:
        raw_path = str(arguments.get("path", ""))
        if not raw_path.strip():
            raise ValueError("Missing required argument: path")
        target = self._resolve_workspace_path(raw_path, must_exist=True)
        if not target.is_file():
            raise ValueError(f"Workspace path is not a file: {raw_path}")
        rel_path = target.relative_to(self.workspace_root).as_posix()
        self._ensure_read_allowed(rel_path)
        text = target.read_text(encoding="utf-8", errors="replace")
        language = _guess_language(target)
        rendered = _truncate_text(text, _MAX_READ_CHARS)
        return f"path: {raw_path}\n```{language}\n{rendered}\n```", "ok"

    def _handle_write_workspace_file(self, arguments: dict[str, Any]) -> tuple[str, str]:
        raw_path = str(arguments.get("path", ""))
        if not raw_path.strip():
            raise ValueError("Missing required argument: path")
        content = str(arguments.get("content", ""))
        append = bool(arguments.get("append", False))
        target = self._resolve_workspace_path(raw_path)
        rel_path = target.relative_to(self.workspace_root).as_posix()
        self._ensure_write_allowed(rel_path)
        target.parent.mkdir(parents=True, exist_ok=True)
        if append:
            with target.open("a", encoding="utf-8") as handle:
                handle.write(content)
        else:
            target.write_text(content, encoding="utf-8")
        if rel_path not in self.materialized_paths:
            self.materialized_paths.append(rel_path)
        return f"path: {rel_path}\nbytes_written: {len(content.encode('utf-8'))}\nmode: {'append' if append else 'overwrite'}", "ok"

    def _handle_activate_skill(self, arguments: dict[str, Any]) -> tuple[str, str]:
        skill_name = str(arguments.get("skill_name", "")).strip()
        if not skill_name:
            raise ValueError("Missing required argument: skill_name")
        skill = self._visible_skills_by_name.get(skill_name)
        if skill is None:
            available = ", ".join(sorted(self._visible_skills_by_name, key=str.lower))
            raise KeyError(f"Unknown mounted skill '{skill_name}'. Available skills: {available}")
        self._active_skill_name = skill.name
        self._skill_activation_trace.append(skill.name)
        allowed_tools = sorted(set(skill.allowed_tools))
        skill_path = f".agents/skills/{skill.name}/SKILL.md"
        return (
            f"active_skill: {skill.name}\n"
            f"skill_path: {skill_path}\n"
            f"allowed_tools: {', '.join(allowed_tools) if allowed_tools else '(none)'}",
            "ok",
        )

    def _handle_deactivate_skill(self, arguments: dict[str, Any]) -> tuple[str, str]:
        if self._active_skill_name is None:
            return "active_skill: (none)", "ok"
        previous = self._active_skill_name
        self._active_skill_name = None
        return f"deactivated_skill: {previous}\nactive_skill: (none)", "ok"

    def _ensure_write_allowed(self, rel_path: str) -> None:
        if self._is_path_blocked(rel_path, self._blocked_write_prefixes):
            raise PermissionError(f"Path is read-only for write_workspace_file: {rel_path}")

    def _ensure_read_allowed(self, rel_path: str) -> None:
        if rel_path == ".":
            return
        if self._is_path_blocked(rel_path, self._blocked_read_prefixes):
            raise PermissionError(f"Path is hidden from read/list tools: {rel_path}")

    def _is_path_blocked(self, rel_path: str, prefixes: list[PurePosixPath]) -> bool:
        candidate = PurePosixPath(rel_path)
        for prefix in prefixes:
            if candidate == prefix or prefix in candidate.parents:
                return True
        return False

    def _materialize_native_skills(self, skills: list[Skill]) -> None:
        skills_root = self.workspace_root / ".agents" / "skills"
        for skill in skills:
            destination = skills_root / skill.name
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copytree(skill.path.parent.resolve(), destination)
            self.mounted_skills.append(skill.name)
            self.mounted_skill_paths.append(str(destination))

        self.native_skill_inventory_path = self.write_text_file(
            "INSTALLED_SKILLS.md",
            _render_native_skill_inventory(skills),
            track=True,
        )
        self.skill_usage_protocol_path = self.write_text_file(
            SKILL_USAGE_PROTOCOL_PATH,
            render_skill_usage_protocol(skills),
            track=True,
        )

    def _resolve_visible_native_skills(self, requested_skills: list[Skill]) -> list[Skill]:
        if self._native_visible_skills_override is not None:
            visible: list[Skill] = []
            seen: set[str] = set()
            for skill in self._native_visible_skills_override:
                if skill.name in seen:
                    continue
                visible.append(skill)
                seen.add(skill.name)
            return visible
        visible: list[Skill] = []
        seen: set[str] = set()
        for skill in requested_skills:
            if skill.name in seen:
                continue
            visible.append(skill)
            seen.add(skill.name)
        return visible

    def _observed_skill_reads(self) -> list[str]:
        observed: list[str] = []
        seen: set[str] = set()
        for entry in self._trace:
            if entry.tool_name != "read_workspace_file":
                continue
            raw_path = str(entry.arguments.get("path", "")).strip()
            skill_name = _skill_name_from_workspace_path(raw_path)
            if not skill_name or skill_name in seen:
                continue
            observed.append(skill_name)
            seen.add(skill_name)
        return observed

    def _observed_skill_script_calls(self) -> list[str]:
        observed: list[str] = []
        seen: set[str] = set()
        for entry in self._trace:
            skill_name = self._skill_script_tool_map.get(entry.tool_name)
            if not skill_name or skill_name in seen:
                continue
            observed.append(skill_name)
            seen.add(skill_name)
        return observed

    def _currently_available_tool_names(self) -> list[str]:
        if not self._enforce_skill_tool_gate:
            return [tool.name for tool in self._tool_specs]

        allowed = set(_SKILL_GATE_ALWAYS_AVAILABLE_TOOLS)
        if self._active_skill_name:
            skill = self._visible_skills_by_name.get(self._active_skill_name)
            if skill is not None:
                allowed.update(skill.allowed_tools)
        return [tool.name for tool in self._tool_specs if tool.name in allowed]

    def _make_script_handler(
        self,
        *,
        skill_name: str,
        rel_script_path: str,
        script_abs_path: Path,
    ) -> Callable[[dict[str, Any]], tuple[str, str]]:
        def handler(arguments: dict[str, Any]) -> tuple[str, str]:
            input_path = str(arguments.get("input_path", "")).strip()
            extra_args = arguments.get("extra_args", [])
            if extra_args is None:
                extra_args = []
            if not isinstance(extra_args, list) or any(not isinstance(item, str) for item in extra_args):
                raise ValueError("extra_args must be an array of strings")

            validated_extra_args: list[str] = []
            for item in extra_args:
                if "/" in item or "\\" in item:
                    raise ValueError(f"extra_args may not contain path separators: {item}")
                validated_extra_args.append(item)

            command: list[str]
            suffix = script_abs_path.suffix.lower()
            if suffix == ".py":
                command = ["python3", str(script_abs_path)]
            elif suffix == ".sh":
                command = ["bash", str(script_abs_path)]
            else:
                raise ValueError(f"Unsupported script type: {script_abs_path.name}")

            if input_path:
                target = self._resolve_workspace_path(input_path, must_exist=True)
                command.append(target.relative_to(self.workspace_root).as_posix())
            command.extend(validated_extra_args)

            completed = subprocess.run(
                command,
                cwd=self.workspace_root,
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            stdout = _truncate_text(completed.stdout, _MAX_TOOL_OUTPUT_CHARS).strip()
            stderr = _truncate_text(completed.stderr, _MAX_TOOL_OUTPUT_CHARS).strip()
            blocks = [
                f"skill: {skill_name}",
                f"script: {rel_script_path}",
                "command: " + " ".join(command),
                f"exit_code: {completed.returncode}",
            ]
            if stdout:
                blocks.append(f"stdout:\n{stdout}")
            if stderr:
                blocks.append(f"stderr:\n{stderr}")

            return "\n\n".join(blocks), "ok" if completed.returncode == 0 else "error"

        return handler


def _skill_name_from_workspace_path(raw_path: str) -> str:
    if not raw_path.strip():
        return ""
    try:
        candidate = PurePosixPath(raw_path)
    except Exception:
        return ""
    parts = candidate.parts
    if len(parts) < 3:
        return ""
    if parts[0] != ".agents" or parts[1] != "skills":
        return ""
    return parts[2].strip()


def _merge_ordered(*groups: list[str]) -> list[str]:
    merged: list[str] = []
    seen: set[str] = set()
    for group in groups:
        for item in group:
            if item in seen:
                continue
            merged.append(item)
            seen.add(item)
    return merged
