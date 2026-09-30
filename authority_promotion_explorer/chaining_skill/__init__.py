from __future__ import annotations

import sys
from importlib import import_module
from types import ModuleType

from .models import CandidateManifest, DiagnosticReport, OverlayManifest, SkillChainStage
from .generation import claude_cli as _claude_cli
from .generation import materializer as _materializer
from .generation import planner as _planner
from .execution import codex_adapter as _codex_adapter
from .execution import compose as _compose
from .execution import failures as _failures
from .execution import harbor_bridge as _harbor_bridge
from .execution import harbor_cli as _harbor_cli
from .execution import handoff as _handoff
from .execution import loop_guard as _loop_guard
from .execution import overlay as _overlay
from .execution import runner as _runner
from .evaluation import adjudication as _adjudication
from .evaluation import trace as _trace
from .evaluation import utility as _utility
from .generation import assets as _prompt_assets

_COMPATIBILITY_MODULES = {
    "candidate_generator": _planner,
    "openai_candidate_generator": _materializer,
    "claude_candidate_generator": _claude_cli,
    "grok45_tool_loop_guard": _loop_guard,
    "execution_harness": _runner,
    "task_overlay": _overlay,
    "handoff_sidecar": _handoff,
    "harbor_agent_support": _harbor_bridge,
    "harbor_cli": _harbor_cli,
    "harbor_compose_compat": _compose,
    "codex_provider_native_backend": _codex_adapter,
    "codex_timeout_fallback": _failures,
    "evaluator_adjudicator": _adjudication,
    "trace_evaluator": _trace,
    "uniform_check_utility": _utility,
    "prompt_catalog": _prompt_assets,
}
for _legacy_name, _module in _COMPATIBILITY_MODULES.items():
    globals()[_legacy_name] = _module
    sys.modules.setdefault(f"{__name__}.{_legacy_name}", _module)


def _register_lazy_compatibility_module(name: str, target: str) -> None:
    alias = f"{__name__}.{name}"
    proxy = ModuleType(alias)

    def load_attribute(attribute: str):
        module = import_module(target)
        sys.modules[alias] = module
        globals()[name] = module
        return getattr(module, attribute)

    proxy.__getattr__ = load_attribute  # type: ignore[attr-defined]
    globals()[name] = proxy
    sys.modules.setdefault(alias, proxy)


_register_lazy_compatibility_module(
    "harbor_deepseek_codex_agent",
    f"{__name__}.execution.harbor_agent",
)

__all__ = [
    "CandidateManifest",
    "DiagnosticReport",
    "OverlayManifest",
    "SkillChainStage",
]
