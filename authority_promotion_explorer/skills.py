from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_RISK_RANK = {
    "unspecified": 0,
    "none": 0,
    "low": 1,
    "guarded": 2,
    "medium": 3,
    "high": 4,
    "critical": 5,
}


@dataclass(slots=True)
class SkillSupportFile:
    rel_path: str
    abs_path: Path
    content: str

    def render_for_prompt(self) -> str:
        suffix = Path(self.rel_path).suffix.lower()
        language_map = {
            ".md": "md",
            ".py": "python",
            ".sh": "bash",
            ".yaml": "yaml",
            ".yml": "yaml",
            ".json": "json",
            ".txt": "text",
        }
        language = language_map.get(suffix, suffix.lstrip(".") or "text")
        return f"### Skill support: {self.rel_path}\n```{language}\n{self.content.strip()}\n```"


@dataclass(slots=True)
class Skill:
    name: str
    description: str
    path: Path
    body: str
    support_files: list[SkillSupportFile] = field(default_factory=list)
    allowed_tools: list[str] = field(default_factory=list)
    capability_primitives: list[str] = field(default_factory=list)
    risk_tags: list[str] = field(default_factory=list)
    isolated_risk: str = "unspecified"
    chain_role: str = ""
    metadata: dict[str, Any] = field(default_factory=dict)

    def render_for_prompt(self) -> str:
        parts = [
            f"## Skill: {self.name}",
            f"Description: {self.description}",
            self.body.strip(),
        ]
        if self.support_files:
            parts.append(
                "Supporting skill files. Treat these as internal skill materials bundled with the skill and available when it is active."
            )
            parts.extend(support_file.render_for_prompt() for support_file in self.support_files)
        return "\n\n".join(part for part in parts if part.strip()).strip()


def _coerce_frontmatter_value(raw_value: str) -> Any:
    value = raw_value.strip()
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("'\"") for item in inner.split(",") if item.strip()]

    lowered = value.lower()
    if lowered == "true":
        return True
    if lowered == "false":
        return False

    return value.strip("'\"")


def _parse_frontmatter(text: str) -> tuple[dict[str, Any], str]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return {}, text.strip()

    end_index = None
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            end_index = index
            break

    if end_index is None:
        return {}, text.strip()

    frontmatter: dict[str, Any] = {}
    for line in lines[1:end_index]:
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        frontmatter[key.strip()] = _coerce_frontmatter_value(value)

    body = "\n".join(lines[end_index + 1 :]).strip()
    return frontmatter, body


def _load_support_files(skill_dir: Path, frontmatter: dict[str, Any]) -> list[SkillSupportFile]:
    raw_files = frontmatter.get("supporting_files", [])
    if not isinstance(raw_files, list):
        return []

    support_files: list[SkillSupportFile] = []
    for item in raw_files:
        rel_path = str(item).strip()
        if not rel_path:
            continue
        file_path = skill_dir / rel_path
        if not file_path.exists():
            raise FileNotFoundError(f"Missing supporting file for skill '{skill_dir.name}': {file_path}")
        support_files.append(
            SkillSupportFile(
                rel_path=rel_path,
                abs_path=file_path,
                content=file_path.read_text(encoding="utf-8").strip(),
            )
        )
    return support_files


def load_skill(skill_file: Path) -> Skill:
    raw = skill_file.read_text(encoding="utf-8")
    frontmatter, body = _parse_frontmatter(raw)
    allowed_tools = frontmatter.get("allowed_tools", [])
    capability_primitives = frontmatter.get("capability_primitives", [])
    risk_tags = frontmatter.get("risk_tags", [])
    return Skill(
        name=frontmatter.get("name", skill_file.parent.name),
        description=frontmatter.get("description", ""),
        path=skill_file,
        body=body,
        support_files=_load_support_files(skill_file.parent, frontmatter),
        allowed_tools=allowed_tools if isinstance(allowed_tools, list) else [],
        capability_primitives=capability_primitives if isinstance(capability_primitives, list) else [],
        risk_tags=risk_tags if isinstance(risk_tags, list) else [],
        isolated_risk=str(frontmatter.get("isolated_risk", "unspecified")),
        chain_role=str(frontmatter.get("chain_role", "")),
        metadata=frontmatter,
    )


def discover_skills(skills_dir: Path) -> dict[str, Skill]:
    registry: dict[str, Skill] = {}
    if not skills_dir.exists():
        return registry

    for skill_file in sorted(skills_dir.glob("*/SKILL.md")):
        skill = load_skill(skill_file)
        registry[skill.name] = skill

    return registry


def select_skills(registry: dict[str, Skill], names: list[str]) -> list[Skill]:
    selected: list[Skill] = []
    seen: set[str] = set()

    for name in names:
        if name in seen:
            continue
        if name not in registry:
            available = ", ".join(sorted(registry))
            raise KeyError(f"Unknown skill '{name}'. Available skills: {available}")
        selected.append(registry[name])
        seen.add(name)

    return selected


def bundle_skills(
    skills: list[Skill],
    *,
    name: str = "bundled-skill",
    description: str = "",
) -> Skill:
    if not skills:
        return Skill(
            name=name,
            description=description,
            path=Path(f"<{name}>"),
            body="",
            allowed_tools=[],
        )

    component_blocks: list[str] = []
    support_files: list[SkillSupportFile] = []
    seen_support_paths: set[str] = set()

    for skill in skills:
        block_parts = [
            f"### Component Skill: {skill.name}",
            f"Description: {skill.description}",
            skill.body.strip(),
        ]
        component_blocks.append("\n\n".join(part for part in block_parts if part.strip()))

        for support_file in skill.support_files:
            rel_path = f"{skill.name}/{support_file.rel_path}"
            if rel_path in seen_support_paths:
                continue
            support_files.append(
                SkillSupportFile(
                    rel_path=rel_path,
                    abs_path=support_file.abs_path,
                    content=support_file.content,
                )
            )
            seen_support_paths.add(rel_path)

    bundled_from = [skill.name for skill in skills]
    bundled_description = description or (
        "Synthetic bundled baseline composed of: " + ", ".join(bundled_from)
    )
    bundled_body = "\n\n".join(
        [
            "# Bundled Skill",
            "This synthetic skill bundles multiple internal skills into one monolithic baseline for comparison.",
            *component_blocks,
        ]
    )

    return Skill(
        name=name,
        description=bundled_description,
        path=Path(f"<{name}>"),
        body=bundled_body,
        support_files=support_files,
        allowed_tools=sorted({tool for skill in skills for tool in skill.allowed_tools}),
        capability_primitives=sorted(
            {
                primitive
                for skill in skills
                for primitive in skill.capability_primitives
            }
        ),
        risk_tags=sorted(
            {
                risk_tag
                for skill in skills
                for risk_tag in skill.risk_tags
            }
        ),
        isolated_risk=max(
            (skill.isolated_risk for skill in skills),
            key=lambda level: _RISK_RANK.get(level.strip().lower(), 0),
            default="unspecified",
        ),
        chain_role="bundled",
        metadata={
            "bundle_kind": "synthetic",
            "bundled_from": bundled_from,
        },
    )
