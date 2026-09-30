from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any
import os

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:
    tomllib = None  # type: ignore[assignment]

DEFAULT_PROVIDER = "openai_compatible"
DEFAULT_BASE_URL = "https://api.deepseek.com"
DEFAULT_MODEL = "deepseek-v4-flash"
DEFAULT_SYSTEM_PROMPT = "prompts/base_system.md"


@dataclass(slots=True)
class ModelConfig:
    provider: str = DEFAULT_PROVIDER
    model: str = DEFAULT_MODEL
    base_url: str = DEFAULT_BASE_URL
    api_key_env: str = "DEEPSEEK_API_KEY"
    timeout_seconds: int = 120
    max_retries: int = 0
    retry_backoff_seconds: float = 0.0
    # Optional local bridge guardrails for providers with a smaller context
    # window than Codex fallback metadata assumes. Zero disables the guardrail.
    context_max_input_chars: int = 0
    context_tool_output_max_chars: int = 0
    temperature: float = 0.2
    system_prompt_path: str = DEFAULT_SYSTEM_PROMPT
    reasoning_effort: str | None = None
    reasoning_summary: str | None = None
    extra_headers: dict[str, str] = field(default_factory=dict)
    extra_body: dict[str, Any] = field(default_factory=dict)
    # Claude Code-specific settings used only by the isolated claude-cli
    # generator. They deliberately exclude credentials, which remain in the
    # process environment and are never written to a settings file.
    claude_settings: dict[str, str] = field(default_factory=dict)
    bypass_proxy: bool = False

    def api_key(self) -> str:
        value = os.getenv(self.api_key_env, "").strip()
        if not value:
            raise RuntimeError(
                f"Environment variable {self.api_key_env} is empty. Export an API key or use --dry-run."
            )
        return value

    def as_public_dict(self) -> dict[str, Any]:
        return asdict(self)


def project_root() -> Path:
    return Path(__file__).resolve().parents[1]


def resolve_project_path(root: Path, raw_path: str | Path) -> Path:
    path = Path(raw_path)
    if path.is_absolute():
        return path
    return root / path


def resolve_system_prompt_path(root: Path, model_config: ModelConfig | None = None) -> Path:
    raw_path = DEFAULT_SYSTEM_PROMPT
    if model_config is not None and model_config.system_prompt_path.strip():
        raw_path = model_config.system_prompt_path
    return resolve_project_path(root, raw_path)


def _parse_simple_toml_value(raw_value: str) -> Any:
    value = raw_value.strip()
    if not value:
        return ""
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]

    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    try:
        return int(value)
    except ValueError:
        pass

    try:
        return float(value)
    except ValueError:
        pass

    return value


def _load_toml_fallback(path: Path) -> dict[str, Any]:
    data: dict[str, Any] = {}
    current_section: dict[str, Any] | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line.startswith("[") and line.endswith("]"):
            section_name = line[1:-1].strip()
            current_section = data.setdefault(section_name, {})
            continue
        if "=" not in line:
            continue

        key, raw_value = line.split("=", 1)
        key = key.strip()
        value = _parse_simple_toml_value(raw_value)
        if current_section is None:
            data[key] = value
        else:
            current_section[key] = value

    return data


def load_model_config(path: Path | None) -> ModelConfig:
    config = ModelConfig()
    if path is None:
        return config

    if tomllib is not None:
        with path.open("rb") as handle:
            loaded = tomllib.load(handle)
    else:
        loaded = _load_toml_fallback(path)

    data = loaded.get("model", loaded)

    if "provider" in data:
        config.provider = str(data["provider"])
    if "model" in data:
        config.model = str(data["model"])
    if "base_url" in data:
        config.base_url = str(data["base_url"])
    if "api_key_env" in data:
        config.api_key_env = str(data["api_key_env"])
    if "timeout_seconds" in data:
        config.timeout_seconds = int(data["timeout_seconds"])
    if "max_retries" in data:
        config.max_retries = int(data["max_retries"])
    if "retry_backoff_seconds" in data:
        config.retry_backoff_seconds = float(data["retry_backoff_seconds"])
    if "context_max_input_chars" in data:
        config.context_max_input_chars = int(data["context_max_input_chars"])
    if "context_tool_output_max_chars" in data:
        config.context_tool_output_max_chars = int(data["context_tool_output_max_chars"])
    if "temperature" in data:
        config.temperature = float(data["temperature"])
    if "system_prompt_path" in data:
        config.system_prompt_path = str(data["system_prompt_path"])
    if "reasoning_effort" in data:
        config.reasoning_effort = str(data["reasoning_effort"])
    if "reasoning_summary" in data:
        config.reasoning_summary = str(data["reasoning_summary"])
    if isinstance(data.get("extra_headers"), dict):
        config.extra_headers = {str(key): str(value) for key, value in data["extra_headers"].items()}
    if isinstance(data.get("extra_body"), dict):
        config.extra_body = data["extra_body"]
    if isinstance(loaded.get("claude"), dict):
        config.claude_settings = {
            str(key): str(value)
            for key, value in loaded["claude"].items()
            if isinstance(value, (str, int, float, bool))
        }
    if "bypass_proxy" in data:
        config.bypass_proxy = bool(data["bypass_proxy"])

    return config
