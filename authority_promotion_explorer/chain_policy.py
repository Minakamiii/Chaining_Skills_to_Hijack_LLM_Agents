from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

try:
    import tomllib  # type: ignore[attr-defined]
except ModuleNotFoundError:
    tomllib = None  # type: ignore[assignment]

RISK_LEVELS = {
    "unspecified": 0,
    "none": 0,
    "low": 1,
    "guarded": 2,
    "medium": 3,
    "high": 4,
    "critical": 5,
}


@dataclass(slots=True)
class ChainPattern:
    id: str
    severity: str
    description: str
    required_primitives: list[str]
    mitigation: str = ""

    def to_dict(self) -> dict[str, object]:
        return {
            "id": self.id,
            "severity": self.severity,
            "description": self.description,
            "required_primitives": self.required_primitives,
            "mitigation": self.mitigation,
        }


def risk_score(level: str) -> int:
    return RISK_LEVELS.get(level.strip().lower(), 0)


def _parse_simple_toml_value(raw_value: str) -> object:
    value = raw_value.strip()
    if value.startswith('"') and value.endswith('"'):
        return value[1:-1]
    if value.startswith("'") and value.endswith("'"):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [item.strip().strip("'\"") for item in inner.split(",") if item.strip()]
    return value


def _load_patterns_fallback(path: Path) -> dict[str, object]:
    patterns: list[dict[str, object]] = []
    current_pattern: dict[str, object] | None = None

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue
        if line == "[[pattern]]":
            current_pattern = {}
            patterns.append(current_pattern)
            continue
        if "=" not in line or current_pattern is None:
            continue
        key, raw_value = line.split("=", 1)
        current_pattern[key.strip()] = _parse_simple_toml_value(raw_value)

    return {"pattern": patterns}


def load_chain_patterns(path: Path) -> list[ChainPattern]:
    if not path.exists():
        return []

    if tomllib is not None:
        with path.open("rb") as handle:
            loaded = tomllib.load(handle)
    else:
        loaded = _load_patterns_fallback(path)

    patterns: list[ChainPattern] = []
    for item in loaded.get("pattern", []):
        required = item.get("required_primitives", [])
        patterns.append(
            ChainPattern(
                id=str(item["id"]),
                severity=str(item.get("severity", "medium")),
                description=str(item.get("description", "")),
                required_primitives=[str(value) for value in required],
                mitigation=str(item.get("mitigation", "")),
            )
        )

    return patterns
