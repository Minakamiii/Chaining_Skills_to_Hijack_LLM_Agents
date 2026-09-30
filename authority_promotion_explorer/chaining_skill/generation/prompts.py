"""The single public API for constructing generator-facing prompts.

Prompt text has two deliberate layers: static assets live in the repository
catalog, while schema-aware text stays near the validators that use it. This
module is the only public assembly surface; provider adapters and the
optimizer consume these functions instead of exposing model-specific prompt
files to callers.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from .planner import render_generator_attack_contract, write_prompt_pack


def render_generator_contract(objective_family: str) -> str:
    """Return the validated, family-specific planning contract."""

    return render_generator_attack_contract(objective_family)


def write_generator_prompt_pack(**kwargs: Any) -> Any:
    """Write one iteration prompt pack and return its candidate manifest."""

    return write_prompt_pack(**kwargs)


def build_planning_messages(*args: Any, **kwargs: Any) -> list[dict[str, str]]:
    """Build the planner-stage provider messages."""

    from .materializer import _build_plan_messages

    return _build_plan_messages(*args, **kwargs)


def build_skill_messages(*args: Any, **kwargs: Any) -> list[dict[str, str]]:
    """Build one schema-aware skill materialization prompt."""

    from .materializer import _build_skill_messages

    return _build_skill_messages(*args, **kwargs)


def build_skill_retry_messages(*args: Any, **kwargs: Any) -> list[dict[str, str]]:
    """Build the bounded retry prompt for a rejected skill materialization."""

    from .materializer import _build_skill_wrong_path_retry_messages

    return _build_skill_wrong_path_retry_messages(*args, **kwargs)


def build_recurrent_self_review_messages(*args: Any, **kwargs: Any) -> list[dict[str, str]]:
    """Build the recurrent-chain self-review prompt."""

    from .materializer import _build_recurrent_self_review_messages

    return _build_recurrent_self_review_messages(*args, **kwargs)


def build_optimizer_messages(*args: Any, **kwargs: Any) -> list[dict[str, Any]]:
    """Build the general evaluator-feedback revision brief prompt."""

    from ..optimizer import _optimizer_agent_messages

    return _optimizer_agent_messages(*args, **kwargs)


def build_recurrent_optimizer_messages(*args: Any, **kwargs: Any) -> list[dict[str, str]]:
    """Build the recurrent-chain evaluator-feedback revision brief prompt."""

    from ..optimizer import _recurrent_obligation_loop_optimizer_agent_messages

    return _recurrent_obligation_loop_optimizer_agent_messages(*args, **kwargs)


def write_revision_prompt(*args: Any, **kwargs: Any) -> Path:
    """Write the next-iteration generator prompt from evaluator feedback."""

    from ..optimizer import write_next_iteration_prompt

    return write_next_iteration_prompt(*args, **kwargs)
