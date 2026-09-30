from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Literal

from agent_sec_lab.config import ModelConfig

from .claude_cli import ClaudeGeneratorResult, run_claude_candidate_generator
from .materializer import OpenAIGeneratorResult, run_codex_provider_native_candidate_generator, run_openai_candidate_generator

GeneratorBackend = Literal["auto", "direct", "codex-native", "claude-cli"]
GeneratorResult = ClaudeGeneratorResult | OpenAIGeneratorResult


@dataclass(frozen=True, slots=True)
class CandidateGenerationRequest:
    """One provider-neutral request to materialize a candidate in an iteration directory."""

    iteration_root: Path
    model_config: ModelConfig
    model_name: str
    backend: GeneratorBackend = "auto"
    timeout_seconds: int = 600


def resolve_generator_backend(request: CandidateGenerationRequest) -> GeneratorBackend:
    """Select an internal transport adapter without exposing provider-specific APIs."""

    if request.backend != "auto":
        return request.backend
    if request.model_config.provider == "anthropic":
        return "claude-cli"
    return "direct"


def generate_candidate(request: CandidateGenerationRequest) -> GeneratorResult:
    """Materialize one candidate through the selected provider adapter."""

    backend = resolve_generator_backend(request)
    if backend == "claude-cli":
        return run_claude_candidate_generator(
            request.iteration_root,
            model_config=request.model_config,
            model_name=request.model_name,
            timeout_seconds=request.timeout_seconds,
        )
    if backend == "codex-native":
        return run_codex_provider_native_candidate_generator(
            request.iteration_root,
            model_config=request.model_config,
            model_name=request.model_name,
            timeout_seconds=request.timeout_seconds,
        )
    if backend == "direct":
        return run_openai_candidate_generator(
            request.iteration_root,
            model_config=request.model_config,
            model_name=request.model_name,
            timeout_seconds=request.timeout_seconds,
        )
    raise ValueError(f"Unsupported generator backend: {backend}")
"""Execution-time policy, recovery, and runtime helpers."""
