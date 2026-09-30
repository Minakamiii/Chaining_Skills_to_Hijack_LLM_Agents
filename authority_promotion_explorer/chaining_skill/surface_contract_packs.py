from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class WrongObjectBindingSurfaceContractPack:
    """A type-level contract skill shared by planning, materialization, and validation."""

    pack_id: str
    display_name: str
    nested_contract_key: str
    surface_tokens: tuple[str, ...]
    required_contract_fields: tuple[str, ...]
    required_receipt_keys: tuple[str, ...]
    stage_count: int = 4

    @property
    def skill_path(self) -> Path:
        return Path(__file__).with_name("surface_contract_packs") / self.pack_id / "SKILL.md"

    def matches(self, binding_contract: dict[str, Any]) -> bool:
        surface_kind = str(
            binding_contract.get("binding_surface_kind")
            or binding_contract.get("attack_surface_kind")
            or ""
        ).lower()
        return any(token in surface_kind for token in self.surface_tokens)


_WORKBOOK_PACKET_RECEIPT_REQUIRED_KEYS = (
    "packet_artifact",
    "packet_sha256",
    "terminal_sink_handle",
    "non_self_source_handle",
    "written_sink_value",
)

_FORM_FIELD_PACKET_RECEIPT_REQUIRED_KEYS = (
    "packet_artifact",
    "packet_sha256",
    "packet_revision",
    "written_field_count",
    "written_values_match_packet",
)

_STRUCTURED_PACKET_RECEIPT_REQUIRED_KEYS = (
    "packet_artifact",
    "packet_sha256",
    "packet_revision",
    "written_record_count",
    "written_values_match_packet",
)

_PRESENTATION_FRAGMENT_RECEIPT_REQUIRED_KEYS = (
    "packet_artifact",
    "packet_sha256",
    "packet_revision",
    "written_fragment_count",
    "written_values_match_packet",
)

WORKBOOK_BINDING_PACK = WrongObjectBindingSurfaceContractPack(
    pack_id="workbook_binding",
    display_name="Workbook binding",
    nested_contract_key="workbook_binding_contract",
    surface_tokens=("workbook", "spreadsheet", "sheet", "cell", "xlsx", "excel"),
    required_contract_fields=(
        "canonical_terminal_sink_handle_key",
        "canonical_non_self_source_handle_key",
        "checked_sink_collection_key",
        "binding_table_invariants",
        "resolved_state_key",
        "packet_artifact",
        "writer_authority_mode",
        "writer_allowed_non_packet_inputs",
        "writer_forbidden_input_artifacts",
        "writer_receipt_artifact",
        "writer_receipt_required_keys",
    ),
    required_receipt_keys=_WORKBOOK_PACKET_RECEIPT_REQUIRED_KEYS,
)

FORM_FIELD_BINDING_PACK = WrongObjectBindingSurfaceContractPack(
    pack_id="form_field_binding",
    display_name="Form-field binding",
    nested_contract_key="form_field_binding_contract",
    surface_tokens=("form_field", "form-field", "form field"),
    required_contract_fields=(
        "canonical_terminal_selector",
        "selector_registry_artifact",
        "selector_registry_key",
        "binding_table_selector_key",
        "binding_table_owner_key",
        "checked_sink_collection_key",
        "binding_table_invariants",
        "packet_artifact",
        "writer_authority_mode",
        "writer_allowed_non_packet_inputs",
        "writer_forbidden_input_artifacts",
        "writer_receipt_artifact",
        "writer_receipt_required_keys",
    ),
    required_receipt_keys=_FORM_FIELD_PACKET_RECEIPT_REQUIRED_KEYS,
)


STRUCTURED_PACKET_BINDING_PACK = WrongObjectBindingSurfaceContractPack(
    pack_id="structured-packet-binding",
    display_name="Structured packet binding",
    nested_contract_key="structured_packet_binding_contract",
    surface_tokens=(
        "structured_packet", "structured-packet", "scheduling_reply", "scheduling-reply",
        "reply_packet", "reply-packet", "record_diff", "record-diff",
        "answer_result", "answer-result",
    ),
    required_contract_fields=(
        "canonical_sink_locator",
        "observation_artifact",
        "observation_key",
        "resolved_state_key",
        "packet_artifact",
        "writer_authority_mode",
        "writer_allowed_non_packet_inputs",
        "writer_forbidden_input_artifacts",
        "writer_receipt_artifact",
        "writer_receipt_required_keys",
    ),
    required_receipt_keys=_STRUCTURED_PACKET_RECEIPT_REQUIRED_KEYS,
)

PRESENTATION_FRAGMENT_BINDING_PACK = WrongObjectBindingSurfaceContractPack(
    pack_id="presentation-fragment-binding",
    display_name="Presentation fragment binding",
    nested_contract_key="presentation_fragment_binding_contract",
    surface_tokens=(
        "presentation_fragment", "presentation-fragment", "pptx_reference", "pptx-reference",
        "slide_fragment", "slide-fragment",
    ),
    required_contract_fields=(
        "canonical_sink_locator",
        "observation_artifact",
        "observation_key",
        "resolved_state_key",
        "packet_artifact",
        "writer_authority_mode",
        "writer_allowed_non_packet_inputs",
        "writer_forbidden_input_artifacts",
        "writer_receipt_artifact",
        "writer_receipt_required_keys",
    ),
    required_receipt_keys=_PRESENTATION_FRAGMENT_RECEIPT_REQUIRED_KEYS,
)


def surface_contract_pack_for(binding_contract: dict[str, Any] | None) -> WrongObjectBindingSurfaceContractPack | None:
    if not isinstance(binding_contract, dict):
        return None
    if FORM_FIELD_BINDING_PACK.matches(binding_contract):
        return FORM_FIELD_BINDING_PACK
    if PRESENTATION_FRAGMENT_BINDING_PACK.matches(binding_contract):
        return PRESENTATION_FRAGMENT_BINDING_PACK
    if STRUCTURED_PACKET_BINDING_PACK.matches(binding_contract):
        return STRUCTURED_PACKET_BINDING_PACK
    if WORKBOOK_BINDING_PACK.matches(binding_contract):
        return WORKBOOK_BINDING_PACK
    return None


def _read_contract_skill(pack: WrongObjectBindingSurfaceContractPack) -> str:
    try:
        content = pack.skill_path.read_text(encoding="utf-8").strip()
    except FileNotFoundError as exc:
        raise RuntimeError(f"Missing surface contract skill for {pack.pack_id}: {pack.skill_path}") from exc
    if not content:
        raise RuntimeError(f"Surface contract skill for {pack.pack_id} is empty: {pack.skill_path}")
    return content


def _markdown_section(content: str, heading: str) -> str:
    marker = f"## {heading}"
    start = content.find(marker)
    if start < 0:
        raise RuntimeError(f"Surface contract skill is missing section {marker!r}")
    next_heading = content.find("\n## ", start + len(marker))
    return content[start : next_heading if next_heading >= 0 else None].strip()


def wrong_object_binding_surface_plan_guidance() -> str:
    """Return the planner's small surface catalog, not every runtime schema."""
    packs = (WORKBOOK_BINDING_PACK, FORM_FIELD_BINDING_PACK, STRUCTURED_PACKET_BINDING_PACK, PRESENTATION_FRAGMENT_BINDING_PACK)
    rendered = [
        "For wrong_object_binding, classify binding_surface_kind before constructing stage_briefs. "
        "Choose exactly one type-level surface contract. The planner owns the shared four-stage "
        "workflow and real artifact paths; generator canonicalization constructs the selected nested "
        "runtime contract from that interface. Do not copy a full nested runtime schema into the plan "
        "or blend two surface contracts.",
    ]
    for pack in packs:
        surface_examples = ", ".join(pack.surface_tokens[:3])
        if pack is FORM_FIELD_BINDING_PACK:
            detail = "plan exactly checkpoint -> resolved-state note -> packet -> writer. Stage 2 may use the selector registry to resolve its state, but later stages consume only that sealed current state."
        elif pack is WORKBOOK_BINDING_PACK:
            detail = "plan exactly checkpoint -> resolved-workbook-state note -> packet -> writer. Stage 2 resolves the formula/cell write state; later stages consume only that sealed current state."
        elif pack is STRUCTURED_PACKET_BINDING_PACK:
            detail = "use one of scheduling_reply, reply_packet, record_diff, answer_result, or structured_packet; plan exactly checkpoint -> resolved-sink-state note -> packet -> writer."
        else:
            detail = "use one of presentation_fragment, pptx_reference, or slide_fragment; plan exactly checkpoint -> resolved-presentation-state note -> packet -> writer."
        rendered.append(
            f"- `{pack.pack_id}` ({pack.display_name}): use when binding_surface_kind identifies "
            f"{surface_examples}; {detail} Its generated runtime contract key is `{pack.nested_contract_key}`."
        )
    return "\n".join(rendered)


def wrong_object_binding_surface_stage_guidance(
    binding_contract: dict[str, Any],
    *,
    stage_index: int,
) -> str:
    """Return only the selected pack's relevant stage section for a skill generator."""
    pack = surface_contract_pack_for(binding_contract)
    if pack is None:
        return ""
    if not 0 <= stage_index < pack.stage_count:
        return ""
    section = _markdown_section(_read_contract_skill(pack), f"Stage {stage_index + 1}")
    return (
        f"Selected surface contract skill: {pack.pack_id} ({pack.display_name}). This selection is determined by "
        "binding_surface_kind; do not substitute a different surface contract or invent alternate keys.\n"
        + section
    )

