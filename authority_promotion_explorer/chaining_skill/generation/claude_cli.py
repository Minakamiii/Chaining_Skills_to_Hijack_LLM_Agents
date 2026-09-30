from __future__ import annotations

from contextlib import nullcontext
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import json
import os
import random
import re
import subprocess
import tempfile
import time

from agent_sec_lab.config import ModelConfig

from ..external_script_fetch_templates import (
    EXTERNAL_SCRIPT_FETCH_EXPECTED_EXIT_CODE,
    EXTERNAL_SCRIPT_FETCH_EXPECTED_MARKER_CONTENTS,
    external_script_fetch_task_profile,
    materialize_external_script_fetch_plan,
    rewrite_external_script_fetch_skill_contracts,
    validate_external_script_fetch_manifest,
)
from ..execution.handoff import runtime_helper_expected_sha256, runtime_helper_url_for_task
from ..models import CandidateManifest
from .assets import read_generated_prompt


_CLAUDE_MODEL_ENV_KEYS = (
    "ANTHROPIC_MODEL",
    "ANTHROPIC_DEFAULT_OPUS_MODEL",
    "ANTHROPIC_DEFAULT_SONNET_MODEL",
    "ANTHROPIC_DEFAULT_HAIKU_MODEL",
    "ANTHROPIC_SMALL_FAST_MODEL",
    "CLAUDE_CODE_SUBAGENT_MODEL",
)
_ONE_MILLION_CONTEXT_BETA = "context-1m-2025-08-07"
_DEFAULT_CLAUDE_GENERATOR_MODEL = "claude-opus-4-6"
_TRANSIENT_PROVIDER_MAX_RETRIES = 10
_TRANSIENT_PROVIDER_RETRY_BASE_SECONDS = 1
_TRANSIENT_PROVIDER_RETRY_MAX_SECONDS = 12
_TRANSIENT_PROVIDER_RETRY_JITTER_RATIO = 0.25
_TRANSIENT_PROVIDER_ERROR_MARKERS = (
    "429",
    "service unavailable",
    "rate limit",
    "rate_limit",
    "overloaded",
    "temporarily unavailable",
)
_FRONTMATTER_LINE_RE = re.compile(r"^([A-Za-z0-9_-]+):(.*)$")
_EXTERNAL_SCRIPT_FETCH_HELPER_SOURCE_RE = re.compile(r'https?://[^\s"\'`]+/(?:runtime_helper\.sh|toolchain_bootstrap\.sh)')


def _canonicalize_external_script_fetch_text(text: str, *, original_url: str, canonical_url: str) -> str:
    rewritten = text
    if original_url:
        rewritten = rewritten.replace(original_url, canonical_url)
    return _EXTERNAL_SCRIPT_FETCH_HELPER_SOURCE_RE.sub(canonical_url, rewritten)


def _canonicalize_external_script_fetch_outputs(iteration_root: Path, manifest: CandidateManifest) -> CandidateManifest:
    if manifest.objective_family != "script_acquisition":
        return manifest

    profile = external_script_fetch_task_profile(manifest.task_id)
    canonical_url = runtime_helper_url_for_task(manifest.task_id)
    payload = manifest.to_dict()
    original_url = str(manifest.helper_url or "").strip()
    changed = False
    if payload.get("helper_url") != canonical_url:
        payload["helper_url"] = canonical_url
        changed = True
    if payload.get("helper_local_path") != profile.helper_local_path:
        payload["helper_local_path"] = profile.helper_local_path
        changed = True
    if payload.get("helper_marker_path") != profile.marker_path:
        payload["helper_marker_path"] = profile.marker_path
        changed = True
    if payload.get("expected_sha256") != runtime_helper_expected_sha256(manifest.task_id):
        payload["expected_sha256"] = runtime_helper_expected_sha256(manifest.task_id)
        changed = True
    if int(payload.get("expected_exit_code", 0) or 0) != EXTERNAL_SCRIPT_FETCH_EXPECTED_EXIT_CODE:
        payload["expected_exit_code"] = EXTERNAL_SCRIPT_FETCH_EXPECTED_EXIT_CODE
        changed = True
    if payload.get("expected_helper_marker_path") != profile.marker_path:
        payload["expected_helper_marker_path"] = profile.marker_path
        changed = True
    if payload.get("expected_helper_marker_contents") != EXTERNAL_SCRIPT_FETCH_EXPECTED_MARKER_CONTENTS:
        payload["expected_helper_marker_contents"] = EXTERNAL_SCRIPT_FETCH_EXPECTED_MARKER_CONTENTS
        changed = True
    if changed:
        manifest = CandidateManifest.from_dict(payload)
        manifest.write_json(iteration_root / "candidate_manifest.json")

    plan_path = iteration_root / "generator_plan.json"
    if plan_path.exists():
        raw_plan = plan_path.read_text(encoding="utf-8")
        rewritten_plan = _canonicalize_external_script_fetch_text(
            raw_plan,
            original_url=original_url,
            canonical_url=canonical_url,
        )
        if rewritten_plan != raw_plan:
            plan_path.write_text(rewritten_plan, encoding="utf-8")

    for skill_name in manifest.generated_skill_names:
        skill_path = iteration_root / "skills" / skill_name / "SKILL.md"
        if not skill_path.is_file():
            continue
        raw_skill = skill_path.read_text(encoding="utf-8")
        rewritten_skill = _canonicalize_external_script_fetch_text(
            raw_skill,
            original_url=original_url,
            canonical_url=canonical_url,
        )
        if rewritten_skill != raw_skill:
            skill_path.write_text(rewritten_skill, encoding="utf-8")

    return manifest


def _write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _resolve_generator_model_name(model_name: str | None, model_config: ModelConfig | None = None) -> str:
    if model_name and model_name.strip():
        return model_name.strip()
    if model_config is not None and model_config.model.strip():
        return model_config.model.strip()
    return _DEFAULT_CLAUDE_GENERATOR_MODEL


def _resolve_claude_cli_model_name(
    resolved_model_name: str,
    model_config: ModelConfig | None,
) -> str:
    if model_config is None:
        return resolved_model_name
    command_model = str(model_config.claude_settings.get("command_model") or "").strip()
    return command_model or resolved_model_name


def _claude_config_mode(model_config: ModelConfig | None) -> str:
    if model_config is None:
        return "isolated"
    config_mode = str(model_config.claude_settings.get("config_mode") or "isolated").strip().lower()
    if config_mode not in {"isolated", "inherit_user"}:
        raise ValueError("claude config_mode must be either 'isolated' or 'inherit_user'")
    return config_mode


def build_claude_generator_command(
    model_name: str,
    claude_bin: str | None = None,
    *,
    use_one_million_context: bool = False,
) -> list[str]:
    executable = claude_bin if claude_bin is not None else "claude"
    command = [
        executable,
        "-p",
        "--output-format",
        "json",
        "--permission-mode",
        "bypassPermissions",
        "--setting-sources",
        "user",
        "--no-chrome",
        "--prompt-suggestions",
        "false",
        "--model",
        model_name,
    ]
    # A provider may expose its 1M route through a model alias such as
    # ``claude-opus-5[1m]``. Current Claude Code enables the associated 1M
    # request behavior from that alias, so do not redundantly add the legacy
    # beta flag here.
    if not use_one_million_context and not model_name.strip().lower().endswith("[1m]"):
        command.extend(("--betas", _ONE_MILLION_CONTEXT_BETA))
    return command


def _read_json_object(path: Path, *, label: str) -> dict[str, Any]:
    raw = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(raw, dict):
        raise ValueError(f"{label} must contain a JSON object")
    return raw


def _candidate_manifest_template(raw: dict[str, Any]) -> CandidateManifest | None:
    try:
        return CandidateManifest.from_dict(raw)
    except Exception:  # noqa: BLE001 - best-effort template recovery only
        return None


def _manifest_has_generated_content(raw: dict[str, Any]) -> bool:
    generated_skill_names = raw.get("generated_skill_names")
    if isinstance(generated_skill_names, list) and any(isinstance(item, str) and item.strip() for item in generated_skill_names):
        return True
    intended_chain = raw.get("intended_chain")
    return isinstance(intended_chain, list) and bool(intended_chain)


def _plan_payload_to_manifest_raw(raw: dict[str, Any]) -> dict[str, Any]:
    chain = raw.get("chain")
    if not isinstance(chain, list):
        return raw

    generated_skill_names: list[str] = []
    intended_chain: list[dict[str, Any]] = []
    expected_trace_markers: dict[str, str] = {}

    for fallback_index, item in enumerate(chain, start=1):
        if not isinstance(item, dict):
            continue
        skill_name = str(item.get("name") or item.get("skill_name") or "").strip()
        if not skill_name:
            continue
        generated_skill_names.append(skill_name)
        raw_index = item.get("stage", item.get("index", fallback_index))
        try:
            stage_index = int(raw_index)
        except (TypeError, ValueError):
            stage_index = fallback_index
        objective = str(item.get("objective") or item.get("benign_role") or item.get("selection_rationale") or "").strip()
        intended_chain.append({"index": stage_index, "skill_name": skill_name, "objective": objective})
        trace_marker = str(item.get("trace_marker") or "").strip()
        if trace_marker:
            expected_trace_markers[skill_name] = trace_marker

    adapted = dict(raw)
    adapted["generated_skill_names"] = generated_skill_names
    adapted["intended_chain"] = intended_chain
    if expected_trace_markers:
        adapted["expected_trace_markers"] = expected_trace_markers
    return adapted


def _normalize_or_materialize_candidate_manifest(
    iteration_root: Path,
    *,
    manifest_template: CandidateManifest | None = None,
    generator_mode: str = "claude-cli",
) -> CandidateManifest:
    from . import materializer as openai_materializer

    manifest_path = iteration_root / "candidate_manifest.json"
    plan_path = iteration_root / "generator_plan.json"

    manifest_raw: dict[str, Any] | None = None
    template = manifest_template
    if manifest_path.exists():
        manifest_raw = _read_json_object(manifest_path, label="candidate_manifest.json")
        if template is None:
            template = _candidate_manifest_template(manifest_raw)

    if manifest_raw is not None and (_manifest_has_generated_content(manifest_raw) or not plan_path.exists()):
        return openai_materializer._normalize_candidate_manifest(
            iteration_root,
            template,
            generator_mode=generator_mode,
        )

    if plan_path.exists():
        plan_raw = _read_json_object(plan_path, label="generator_plan.json")
        plan_raw = openai_materializer._canonicalize_plan_payload(plan_raw, template)
        target_family = str(plan_raw.get("objective_family") or (template.objective_family if template is not None else "")).strip()
        if target_family == "script_acquisition":
            plan_raw = materialize_external_script_fetch_plan(iteration_root, plan_raw)
            _write_json(plan_path, plan_raw)
        adapted_plan = _plan_payload_to_manifest_raw(plan_raw)
        return openai_materializer._write_candidate_manifest_from_raw(
            iteration_root,
            adapted_plan,
            template,
            generator_mode=generator_mode,
        )

    if manifest_raw is not None:
        return openai_materializer._normalize_candidate_manifest(
            iteration_root,
            template,
            generator_mode=generator_mode,
        )

    raise FileNotFoundError("Missing candidate_manifest.json and generator_plan.json")



_MAX_CODEX_SKILL_NAME_LENGTH = 64


def _frontmatter_name_from_text(text: str) -> str:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        if not line.startswith("name:"):
            continue
        value = line.split(":", 1)[1].strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        return value
    return ""


def _validate_codex_skill_frontmatter_name(
    skill_path: Path,
    requested_name: str,
    *,
    require_exact_match: bool = False,
) -> None:
    visible_name = _frontmatter_name_from_text(skill_path.read_text(encoding="utf-8"))
    if not visible_name:
        if require_exact_match:
            raise ValueError(f"Generated recurrent skill must declare frontmatter name: {skill_path}")
        return
    if len(visible_name) > _MAX_CODEX_SKILL_NAME_LENGTH:
        raise ValueError(
            f"Generated skill frontmatter name exceeds {_MAX_CODEX_SKILL_NAME_LENGTH} characters: {visible_name}"
        )
    if require_exact_match and visible_name != requested_name:
        raise ValueError(f"Generated skill frontmatter name must match its directory name: {requested_name}")


def _validate_recurrent_candidate_contract(iteration_root: Path, manifest: CandidateManifest) -> None:
    if manifest.objective_family != "work_loop":
        return
    plan_path = iteration_root / "generator_plan.json"
    if not plan_path.exists():
        return
    from . import materializer as openai_materializer

    plan_payload = _read_json_object(plan_path, label="generator_plan.json")
    raw_contract = plan_payload.get("cycle_contract")
    if not isinstance(raw_contract, dict) or raw_contract.get("contract_version") not in {
        "board-and-slice-ring-v2",
        "rolling-checkpoint-ring-v3",
    }:
        # Archived non-board candidates remain evaluator-only compatibility inputs.
        return
    if (
        raw_contract.get("contract_version") == "board-and-slice-ring-v2"
        and len(plan_payload.get("generated_skill_names", [])) != 5
    ):
        # Earlier archived Board-v2 experiments used a four-stage shape. They
        # are evaluator-only compatibility inputs, not the active generator contract.
        return
    plan_payload = openai_materializer._canonicalize_recurrent_obligation_loop_plan_payload(plan_payload)
    openai_materializer._validate_recurrent_mechanical_plan_semantics(plan_payload)
    plan_names = list(plan_payload.get("generated_skill_names", []))
    if plan_names != list(manifest.generated_skill_names):
        raise ValueError("recurrent generator_plan generated_skill_names must exactly match candidate_manifest.json")
    # Marker serialization is intentionally non-authoritative at plan time.
    # The recurrent plan intake canonicalizes common forms, and runtime trace
    # evidence decides whether a generated skill actually emits the markers.
    # Requiring byte-for-byte plan/manifest marker equality here only turns
    # harmless planner formatting drift into a generation failure.

    for skill_name in manifest.generated_skill_names:
        skill_root = iteration_root / "skills" / skill_name
        files = [
            {
                "path": path.relative_to(iteration_root).as_posix(),
                "content": path.read_text(encoding="utf-8"),
            }
            for path in skill_root.rglob("*")
            if path.is_file()
        ]
        openai_materializer._validate_recurrent_rendered_stage(files, plan_payload, skill_name, None)


def validate_candidate_outputs(iteration_root: Path) -> CandidateManifest:
    manifest = CandidateManifest.read_json(iteration_root / "candidate_manifest.json")
    manifest = _canonicalize_external_script_fetch_outputs(iteration_root, manifest)
    manifest = rewrite_external_script_fetch_skill_contracts(iteration_root, manifest)
    validate_external_script_fetch_manifest(manifest)
    skills_root = (iteration_root / "skills").resolve(strict=False)
    for skill_name in manifest.generated_skill_names:
        _validate_generated_skill_name(skill_name, skills_root)
        skill_path = iteration_root / "skills" / skill_name / "SKILL.md"
        if not skill_path.is_file():
            raise FileNotFoundError(f"Missing generated skill file: {skill_path}")
        _normalize_skill_frontmatter(skill_path)
        _validate_codex_skill_frontmatter_name(
            skill_path,
            skill_name,
            require_exact_match=manifest.objective_family == "work_loop",
        )
    _validate_recurrent_candidate_contract(iteration_root, manifest)
    return manifest


@dataclass(slots=True)
class ClaudeGeneratorResult:
    iteration_root: Path
    command: list[str]
    returncode: int
    stdout_path: Path
    stderr_path: Path
    response_json_path: Path
    result_json_path: Path
    env_keys_used: list[str]
    generated_skill_names: list[str]
    requested_model: str
    observed_models: list[str]
    retry_history: list[dict[str, Any]] = field(default_factory=list)
    error: str = ""

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        payload["iteration_root"] = str(self.iteration_root)
        payload["stdout_path"] = str(self.stdout_path)
        payload["stderr_path"] = str(self.stderr_path)
        payload["response_json_path"] = str(self.response_json_path)
        payload["result_json_path"] = str(self.result_json_path)
        return payload


def _read_manifest_template(iteration_root: Path) -> CandidateManifest | None:
    manifest_path = iteration_root / "candidate_manifest.json"
    if not manifest_path.exists():
        return None
    try:
        return CandidateManifest.read_json(manifest_path)
    except Exception:  # noqa: BLE001 - invalid stale manifests should not block generation
        return None


def _merge_env(
    env: dict[str, str] | None,
    *,
    model_name: str,
    model_config: ModelConfig | None = None,
) -> tuple[dict[str, str], list[str]]:
    merged = os.environ.copy()
    if env:
        for key, value in env.items():
            merged[key] = value
    if model_config is not None:
        provider = model_config.provider.strip()
        if provider and provider != "anthropic":
            raise ValueError('claude-cli generator config must use provider = "anthropic"')
        merged["ANTHROPIC_AUTH_TOKEN"] = model_config.api_key()
        if model_config.base_url.strip():
            merged["ANTHROPIC_BASE_URL"] = model_config.base_url.strip()

    # The command line selects the generator model. Do not collapse every
    # auxiliary Claude Code model into it: that differs from the user's
    # settings and can route background requests through the wrong provider
    # alias. The temporary settings file below supplies declared defaults.
    for key in _CLAUDE_MODEL_ENV_KEYS:
        merged.pop(key, None)

    env_keys_used = [
        key for key in ("ANTHROPIC_AUTH_TOKEN", "ANTHROPIC_BASE_URL") if merged.get(key)
    ]
    return merged, env_keys_used


def _claude_setting_value(
    settings: dict[str, str],
    key: str,
    *,
    fallback: str = "",
) -> str:
    value = str(settings.get(key) or "").strip()
    return value or fallback


def _write_isolated_claude_settings(
    config_dir: Path,
    *,
    runtime_env: dict[str, str],
    model_name: str,
    model_config: ModelConfig | None,
) -> Path:
    """Write a credential-free subset of Claude Code user settings."""
    configured = model_config.claude_settings if model_config is not None else {}
    settings_env: dict[str, str] = {}

    base_url = str(runtime_env.get("ANTHROPIC_BASE_URL") or "").strip()
    if base_url:
        settings_env["ANTHROPIC_BASE_URL"] = base_url

    # Match a normal Claude Code Opus/Sonnet selection without copying plugin,
    # marketplace, auth, or session state from ~/.claude.
    settings_env["ANTHROPIC_DEFAULT_OPUS_MODEL"] = _claude_setting_value(
        configured, "default_opus_model", fallback=model_name
    )
    settings_env["ANTHROPIC_DEFAULT_SONNET_MODEL"] = _claude_setting_value(
        configured, "default_sonnet_model"
    )
    settings_env = {key: value for key, value in settings_env.items() if value}

    payload: dict[str, Any] = {"env": settings_env}
    default_model = _claude_setting_value(configured, "default_model")
    if default_model:
        payload["model"] = default_model

    settings_path = config_dir / "settings.json"
    settings_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    settings_path.chmod(0o600)
    return settings_path


def _secret_values(env: dict[str, str] | None) -> list[str]:
    if not env:
        return []
    sensitive_keys = ("TOKEN", "SECRET", "PASSWORD", "API_KEY", "AUTH")
    values: list[str] = []
    for key, value in env.items():
        if not isinstance(value, str) or not value:
            continue
        upper_key = key.upper()
        if any(marker in upper_key for marker in sensitive_keys):
            values.append(value)
    values.sort(key=len, reverse=True)
    return list(dict.fromkeys(values))


def _redact_sensitive_values(text: str, env: dict[str, str] | None) -> str:
    redacted = text
    for value in _secret_values(env):
        redacted = redacted.replace(value, "<redacted>")
    return redacted


def _redact_sensitive_json(value: Any, env: dict[str, str] | None) -> Any:
    if isinstance(value, str):
        return _redact_sensitive_values(value, env)
    if isinstance(value, list):
        return [_redact_sensitive_json(item, env) for item in value]
    if isinstance(value, dict):
        return {key: _redact_sensitive_json(item, env) for key, item in value.items()}
    return value


def _validate_generated_skill_name(skill_name: str, skills_root: Path) -> None:
    if not isinstance(skill_name, str) or not skill_name:
        raise ValueError("Generated skill name must be a non-empty string")
    if skill_name in {".", ".."}:
        raise ValueError(f"Unsafe generated skill name: {skill_name}")
    if Path(skill_name).is_absolute():
        raise ValueError(f"Unsafe generated skill name: {skill_name}")
    if "/" in skill_name or "\\" in skill_name:
        raise ValueError(f"Unsafe generated skill name: {skill_name}")
    resolved_skill_root = skills_root.resolve(strict=False)
    resolved_skill_path = (resolved_skill_root / skill_name).resolve(strict=False)
    if not resolved_skill_path.is_relative_to(resolved_skill_root):
        raise ValueError(f"Unsafe generated skill name: {skill_name}")


def _normalize_skill_frontmatter(skill_path: Path) -> None:
    text = skill_path.read_text(encoding="utf-8")
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return

    end_index = None
    for index, line in enumerate(lines[1:], start=1):
        if line.strip() == "---":
            end_index = index
            break
    if end_index is None:
        return

    normalized_lines = [lines[0]]
    changed = False
    for line in lines[1:end_index]:
        raw = line.rstrip("\n")
        match = _FRONTMATTER_LINE_RE.match(raw)
        if not match:
            normalized_lines.append(line)
            continue

        key = match.group(1)
        value = match.group(2).strip()
        if (
            not value
            or value[0] in {"'", '"', "[", "{", "|", ">", "!"}
            or re.fullmatch(r"(?i:true|false|null)", value)
            or re.fullmatch(r"-?\d+(?:\.\d+)?", value)
            or re.fullmatch(r"[A-Za-z0-9_.-]+", value)
        ):
            normalized_lines.append(line)
            continue

        normalized_lines.append(f"{key}: {json.dumps(value, ensure_ascii=False)}\n")
        changed = True

    if not changed:
        return

    normalized_lines.extend(lines[end_index:])
    skill_path.write_text("".join(normalized_lines), encoding="utf-8")


def _timeout_error_message(exc: subprocess.TimeoutExpired, timeout_seconds: int) -> str:
    return f"claude timed out after {timeout_seconds} seconds: {exc}"


def _extract_timeout_output(exc: subprocess.TimeoutExpired) -> tuple[str, str]:
    stdout = getattr(exc, "stdout", None)
    if stdout is None:
        stdout = getattr(exc, "output", None)
    stderr = getattr(exc, "stderr", None)
    if isinstance(stdout, bytes):
        stdout = stdout.decode("utf-8", errors="replace")
    if isinstance(stderr, bytes):
        stderr = stderr.decode("utf-8", errors="replace")
    return str(stdout or ""), str(stderr or "")


def _observed_models_from_response(value: Any) -> list[str]:
    if not isinstance(value, dict):
        return []
    raw_usage = value.get("modelUsage")
    if not isinstance(raw_usage, dict):
        return []
    models: set[str] = set()
    for fallback_name, facts in raw_usage.items():
        if not isinstance(facts, dict):
            continue
        canonical_name = str(facts.get("canonicalModel") or fallback_name).strip()
        if canonical_name:
            models.add(canonical_name)
    return sorted(models)

def _json_object_from_stdout(stdout: str) -> dict[str, Any] | None:
    try:
        value = json.loads(stdout.strip())
    except (json.JSONDecodeError, TypeError):
        return None
    return value if isinstance(value, dict) else None


def _claude_response_error(value: Any) -> str:
    if not isinstance(value, dict):
        return ""
    result = value.get("result")
    if isinstance(result, str) and result.strip():
        return result.strip()
    error = value.get("error")
    if isinstance(error, str):
        return error.strip()
    if isinstance(error, dict):
        message = error.get("message")
        if isinstance(message, str):
            return message.strip()
    return ""


def _is_transient_provider_error(value: Any) -> bool:
    if not isinstance(value, dict) or not value.get("is_error"):
        return False
    terminal_reason = str(value.get("terminal_reason") or "").strip().lower()
    if terminal_reason and terminal_reason != "api_error":
        return False
    error_text = _claude_response_error(value).lower()
    return any(marker in error_text for marker in _TRANSIENT_PROVIDER_ERROR_MARKERS)


def _normalized_model_identifier(value: str) -> str:
    return re.sub(r"\[1m\]$", "", value.strip().lower())


def _model_identifiers_match(expected: str, observed: str) -> bool:
    return _normalized_model_identifier(expected) == _normalized_model_identifier(observed)


def _retry_delay_seconds(retry_index: int) -> float:
    base_delay = min(
        _TRANSIENT_PROVIDER_RETRY_BASE_SECONDS * (2 ** retry_index),
        _TRANSIENT_PROVIDER_RETRY_MAX_SECONDS,
    )
    jitter = random.uniform(0.0, base_delay * _TRANSIENT_PROVIDER_RETRY_JITTER_RATIO)
    return round(base_delay + jitter, 3)


def _run_candidate_generator(
    command: list[str],
    prompt: str,
    iteration_root: Path,
    merged_env: dict[str, str],
    timeout_seconds: int,
    model_name: str,
    model_config: ModelConfig | None,
) -> tuple[int, str, str, str, list[dict[str, Any]]]:
    retry_history: list[dict[str, Any]] = []
    config_mode = _claude_config_mode(model_config)
    config_context = (
        tempfile.TemporaryDirectory(prefix="skillsbench-claude-generator-")
        if config_mode == "isolated"
        else nullcontext(None)
    )
    with config_context as config_dir:
        runtime_env = dict(merged_env)
        runtime_env.pop("CLAUDE_CONFIG_DIR", None)
        if config_dir is not None:
            runtime_env["CLAUDE_CONFIG_DIR"] = config_dir
            _write_isolated_claude_settings(
                Path(config_dir),
                runtime_env=runtime_env,
                model_name=model_name,
                model_config=model_config,
            )

        for retry_index in range(_TRANSIENT_PROVIDER_MAX_RETRIES + 1):
            try:
                completed = subprocess.run(
                    command,
                    input=prompt,
                    text=True,
                    capture_output=True,
                    cwd=iteration_root,
                    env=runtime_env,
                    timeout=timeout_seconds,
                )
            except subprocess.TimeoutExpired as exc:
                stdout_text, stderr_text = _extract_timeout_output(exc)
                return 124, stdout_text, stderr_text, _timeout_error_message(exc, timeout_seconds), retry_history
            except FileNotFoundError as exc:
                return 127, "", "", f"claude binary not found: {exc}", retry_history
            except PermissionError as exc:
                return 126, "", "", f"claude execution permission denied: {exc}", retry_history
            except OSError as exc:
                return 126, "", "", f"claude execution failed: {exc}", retry_history

            parsed_response = _json_object_from_stdout(completed.stdout)
            if not _is_transient_provider_error(parsed_response):
                return completed.returncode, completed.stdout, completed.stderr, "", retry_history
            if retry_index >= _TRANSIENT_PROVIDER_MAX_RETRIES:
                return max(completed.returncode, 1), completed.stdout, completed.stderr, "", retry_history

            # Claude Code retries an unavailable request as the original
            # operation. Resuming a failed session instead changes the prompt
            # to a continuation request and made the harness diverge from the
            # interactive client.
            delay_seconds = _retry_delay_seconds(retry_index)
            retry_history.append(
                {
                    "retry": retry_index + 1,
                    "delay_seconds": delay_seconds,
                    "session_id": str(parsed_response.get("session_id") or "").strip(),
                    "reason": _claude_response_error(parsed_response),
                    "returncode": completed.returncode,
                    "retry_mode": "fresh_request",
                }
            )
            time.sleep(delay_seconds)

    raise AssertionError("unreachable")


def run_claude_candidate_generator(
    iteration_root: Path,
    *,
    model_name: str | None = None,
    timeout_seconds: int = 1200,
    env: dict[str, str] | None = None,
    model_config: ModelConfig | None = None,
) -> ClaudeGeneratorResult:
    prompt = read_generated_prompt(iteration_root)
    manifest_template = _read_manifest_template(iteration_root)
    resolved_model_name = _resolve_generator_model_name(model_name, model_config=model_config)
    cli_model_name = _resolve_claude_cli_model_name(resolved_model_name, model_config)
    command = build_claude_generator_command(
        cli_model_name,
        use_one_million_context=resolved_model_name.strip().lower().endswith("[1m]"),
    )
    merged_env, env_keys_used = _merge_env(
        env, model_name=resolved_model_name, model_config=model_config
    )
    if _claude_config_mode(model_config) == "isolated":
        env_keys_used.append("CLAUDE_CONFIG_DIR")
    returncode, raw_stdout, raw_stderr, run_error, retry_history = _run_candidate_generator(
        command=command,
        prompt=prompt,
        iteration_root=iteration_root,
        merged_env=merged_env,
        timeout_seconds=timeout_seconds,
        model_name=resolved_model_name,
        model_config=model_config,
    )

    stdout_path = iteration_root / "generator_stdout.txt"
    stderr_path = iteration_root / "generator_stderr.txt"
    response_json_path = iteration_root / "generator_response.json"
    result_json_path = iteration_root / "generator_result.json"
    stdout_text = _redact_sensitive_values(raw_stdout, merged_env)
    stderr_text = _redact_sensitive_values(raw_stderr, merged_env)
    stdout_path.write_text(stdout_text, encoding="utf-8")
    stderr_path.write_text(stderr_text, encoding="utf-8")

    parsed_stdout: Any = None
    parsed_stdout_is_json = False
    raw_stdout_stripped = raw_stdout.strip()
    if raw_stdout_stripped:
        try:
            loaded = json.loads(raw_stdout_stripped)
        except json.JSONDecodeError:
            loaded = None
        else:
            parsed_stdout = loaded
            parsed_stdout_is_json = True
        if parsed_stdout_is_json:
            _write_json(response_json_path, _redact_sensitive_json(parsed_stdout, merged_env))

    observed_models = _observed_models_from_response(parsed_stdout)
    model_validation_error = ""
    if returncode == 0 and observed_models:
        if len(observed_models) != 1 or not _model_identifiers_match(
            resolved_model_name, observed_models[0]
        ):
            model_validation_error = (
                f"claude generator model validation failed: expected only {resolved_model_name}; "
                f"observed {', '.join(observed_models)}"
            )

    if model_validation_error:
        returncode = max(returncode, 1)

    generated_skill_names: list[str] = []
    error = run_error or model_validation_error
    if returncode == 0 and not error:
        try:
            _normalize_or_materialize_candidate_manifest(
                iteration_root,
                manifest_template=manifest_template,
                generator_mode="claude-cli",
            )
            manifest = validate_candidate_outputs(iteration_root)
        except Exception as exc:  # noqa: BLE001 - validation failures must still be recorded
            error = f"candidate validation failed: {exc}"
            if manifest_template is not None and manifest_template.objective_family == "script_acquisition":
                returncode = max(returncode, 1)
        else:
            generated_skill_names = list(manifest.generated_skill_names)
    elif not error:
        error = stderr_text.strip() or _claude_response_error(parsed_stdout) or f"claude exited with {returncode}"

    error = _redact_sensitive_values(error, merged_env)

    result = ClaudeGeneratorResult(
        iteration_root=iteration_root,
        command=list(command),
        returncode=returncode,
        stdout_path=stdout_path,
        stderr_path=stderr_path,
        response_json_path=response_json_path,
        result_json_path=result_json_path,
        env_keys_used=env_keys_used,
        generated_skill_names=generated_skill_names,
        requested_model=resolved_model_name,
        observed_models=observed_models,
        retry_history=_redact_sensitive_json(retry_history, merged_env),
        error=error,
    )
    _write_json(result_json_path, result.to_dict())
    return result
