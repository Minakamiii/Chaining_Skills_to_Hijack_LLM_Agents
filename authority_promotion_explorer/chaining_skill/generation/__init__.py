"""Candidate planning, prompt construction, materialization, and provider-neutral generation."""

from .prompts import (
    build_optimizer_messages,
    build_planning_messages,
    build_recurrent_optimizer_messages,
    build_recurrent_self_review_messages,
    build_skill_messages,
    build_skill_retry_messages,
    render_generator_contract,
    write_generator_prompt_pack,
    write_revision_prompt,
)
from .service import CandidateGenerationRequest, GeneratorBackend, GeneratorResult, generate_candidate, resolve_generator_backend

__all__ = [
    "CandidateGenerationRequest",
    "GeneratorBackend",
    "GeneratorResult",
    "build_optimizer_messages",
    "build_planning_messages",
    "build_recurrent_optimizer_messages",
    "build_recurrent_self_review_messages",
    "build_skill_messages",
    "build_skill_retry_messages",
    "generate_candidate",
    "render_generator_contract",
    "resolve_generator_backend",
    "write_generator_prompt_pack",
    "write_revision_prompt",
]
