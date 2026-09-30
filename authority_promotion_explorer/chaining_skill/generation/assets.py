"""Central registry for every reusable SkillsBench prompt asset.

Dynamic prompt builders stay next to the schema they validate, while this
module owns prompt-file locations and shared prompt fragments. That makes the
prompt surface auditable from one place and prevents generators, overlays, and
executors from each discovering their own copy of an asset path.
"""

from __future__ import annotations

from pathlib import Path


_PACKAGE_ROOT = Path(__file__).resolve().parents[1]
_PROMPT_ROOT = _PACKAGE_ROOT / "prompts"
_REFERENCE_ROOT = _PACKAGE_ROOT / "references"

_PROMPT_FILES = {
    "execution_safety": "execution_safety_minimal.j2",
    "execution_skill_adoption": "execution_skill_adoption.j2",
    "internal_handoff_note": "internal_handoff_service_note.md.j2",
}


def prompt_asset_path(name: str) -> Path:
    """Return the packaged path for a named reusable prompt asset."""
    try:
        filename = _PROMPT_FILES[name]
    except KeyError as exc:
        choices = ", ".join(sorted(_PROMPT_FILES))
        raise ValueError(f"Unknown prompt asset {name!r}; choose one of: {choices}") from exc
    return _PROMPT_ROOT / filename


def load_prompt_asset(name: str) -> str:
    """Read a reusable prompt asset exactly once at its point of use."""
    return prompt_asset_path(name).read_text(encoding="utf-8")


def render_internal_handoff_note(service_url: str) -> str:
    return load_prompt_asset("internal_handoff_note").replace("{{ service_url }}", service_url)


def read_generated_prompt(iteration_root: Path) -> str:
    """Load the canonical generator prompt materialized for one iteration."""
    return (iteration_root / "generator_prompt.md").read_text(encoding="utf-8")


def recurrent_golden_reference() -> str:
    return (_REFERENCE_ROOT / "recurrent_loop_golden_reference.md").read_text(encoding="utf-8").strip()


def recurrent_optimizer_repair_playbook() -> str:
    """Return the optional recurrent-loop repair guide without hiding I/O errors."""
    try:
        return (_REFERENCE_ROOT / "recurrent_loop_runtime_repair_playbook.md").read_text(
            encoding="utf-8"
        ).strip()
    except OSError:
        return "Runtime repair playbook unavailable; use only direct trace facts."
