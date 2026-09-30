from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any
import json
import os
import shutil
import subprocess
import tempfile

from agent_sec_lab.codex_provider_bridge import start_codex_provider_bridge
from agent_sec_lab.config import ModelConfig
from agent_sec_lab.skillsbench_chain.execution.harbor_bridge import provider_uses_direct_responses


_DEFAULT_WORKSPACE_ROOT = Path(tempfile.gettempdir()) / "agent-sec-lab-skillsbench-codex-bridge"


@dataclass(slots=True)
class CodexProviderNativePromptResult:
    model: str
    text: str
    returncode: int
    command: list[str]
    workspace_root: Path
    stdout: str
    stderr: str
    provider_bridge: dict[str, str]
    error: str = ""

    def raw_payload(self) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": self.model,
            "text": self.text,
            "returncode": self.returncode,
            "command": list(self.command),
            "workspace_root": str(self.workspace_root),
            "stdout": self.stdout,
            "stderr": self.stderr,
            "provider_bridge": dict(self.provider_bridge),
        }
        if self.error:
            payload["error"] = self.error
        return payload


def _write_text(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _resolve_provider_backed_codex_model(model_config: ModelConfig, codex_model: str | None = None) -> str:
    if codex_model and codex_model.strip():
        return codex_model.strip()
    return model_config.model.strip()


def _build_codex_command(
    *,
    workspace_root: Path,
    last_message_path: Path,
    codex_model: str,
    config_overrides: list[str],
) -> list[str]:
    command = [
        shutil.which("codex") or "codex",
        "exec",
        "-",
        "--json",
        "--ephemeral",
        "--skip-git-repo-check",
        "-C",
        str(workspace_root),
        "-o",
        str(last_message_path),
        "--sandbox",
        "workspace-write",
    ]
    for override in config_overrides:
        command.extend(["-c", override])
    command.extend(["-m", codex_model])
    return command


def _direct_responses_codex_overrides(model_config: ModelConfig) -> list[str]:
    provider_name = "skillsbench-chain-provider"
    display_name = "SkillsBench Chain Provider"
    provider_table = (
        "{"
        f"name={json.dumps(display_name)},"
        f"base_url={json.dumps(model_config.base_url)},"
        f"env_key={json.dumps(model_config.api_key_env)},"
        'wire_api="responses",'
        "supports_websockets=false,"
        "requires_openai_auth=false"
        "}"
    )
    return [
        f"model_provider={json.dumps(provider_name)}",
        f"model_providers.{provider_name}={provider_table}",
    ]


def _codex_reasoning_overrides(model_config: ModelConfig) -> list[str]:
    """Translate provider reasoning settings to Codex's native config keys."""

    if not model_config.reasoning_effort:
        return []
    return [f"model_reasoning_effort={json.dumps(model_config.reasoning_effort)}"]


def run_codex_provider_native_prompt(
    *,
    prompt_id: str,
    system_prompt: str,
    user_prompt: str,
    model_config: ModelConfig,
    codex_model: str,
    timeout_seconds: int,
    workspace_parent: Path | None = None,
) -> CodexProviderNativePromptResult:
    if shutil.which("codex") is None:
        raise RuntimeError("`codex` is not installed or not available on PATH.")

    workspace_base = (workspace_parent or _DEFAULT_WORKSPACE_ROOT).resolve()
    workspace_base.mkdir(parents=True, exist_ok=True)

    workspace_root = Path(
        tempfile.mkdtemp(
            prefix=f"{prompt_id}-",
            dir=str(workspace_base),
        )
    )
    workspace_root.mkdir(parents=True, exist_ok=True)
    _write_text(workspace_root / "AGENTS.md", system_prompt.rstrip() + "\n")
    codex_dir = workspace_root / "_codex"
    codex_dir.mkdir(parents=True, exist_ok=True)
    last_message_path = codex_dir / "last_message.txt"

    effective_config = ModelConfig(
        provider=model_config.provider,
        model=codex_model,
        base_url=model_config.base_url,
        api_key_env=model_config.api_key_env,
        timeout_seconds=timeout_seconds,
        max_retries=model_config.max_retries,
        retry_backoff_seconds=model_config.retry_backoff_seconds,
        temperature=model_config.temperature,
        system_prompt_path=model_config.system_prompt_path,
        reasoning_effort=model_config.reasoning_effort,
        reasoning_summary=model_config.reasoning_summary,
        extra_headers=dict(model_config.extra_headers),
        extra_body=dict(model_config.extra_body),
    )

    resolved_model = _resolve_provider_backed_codex_model(effective_config, codex_model=codex_model)
    if provider_uses_direct_responses(effective_config):
        command = _build_codex_command(
            workspace_root=workspace_root,
            last_message_path=last_message_path,
            codex_model=resolved_model,
            config_overrides=[
                *_direct_responses_codex_overrides(effective_config),
                *_codex_reasoning_overrides(effective_config),
            ],
        )
        completed = subprocess.run(
            command,
            input=user_prompt,
            text=True,
            capture_output=True,
            cwd=workspace_root,
            env=os.environ.copy(),
            timeout=timeout_seconds,
        )
        provider_metadata = {
            "provider_name": "skillsbench-chain-provider",
            "display_name": "SkillsBench Chain Provider",
            "base_url": effective_config.base_url,
            "env_key": effective_config.api_key_env,
            "mode": "direct_responses",
        }
    else:
        with start_codex_provider_bridge(effective_config) as bridge:
            command = _build_codex_command(
                workspace_root=workspace_root,
                last_message_path=last_message_path,
                codex_model=resolved_model,
                config_overrides=[
                    *bridge.codex_config_overrides(),
                    *_codex_reasoning_overrides(effective_config),
                ],
            )
            completed = subprocess.run(
                command,
                input=user_prompt,
                text=True,
                capture_output=True,
                cwd=workspace_root,
                env=bridge.subprocess_env(os.environ.copy()),
                timeout=timeout_seconds,
            )
            provider_metadata = {
                "provider_name": bridge.provider_name,
                "display_name": bridge.display_name,
                "base_url": bridge.base_url,
                "env_key": bridge.env_key,
                "mode": "bridge",
            }

    text = last_message_path.read_text(encoding="utf-8").strip() if last_message_path.exists() else ""
    error = ""
    if completed.returncode != 0:
        error = completed.stderr.strip() or completed.stdout.strip() or "codex exec failed without output"

    return CodexProviderNativePromptResult(
        model=resolved_model or "codex-provider-bridge",
        text=text,
        returncode=completed.returncode,
        command=command,
        workspace_root=workspace_root,
        stdout=completed.stdout,
        stderr=completed.stderr,
        provider_bridge=provider_metadata,
        error=error,
    )
