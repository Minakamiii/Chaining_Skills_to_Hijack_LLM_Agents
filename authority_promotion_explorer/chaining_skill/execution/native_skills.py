"""Load native task skills from an external checkout and apply authored additions."""

from __future__ import annotations

import hashlib
from pathlib import Path
import shutil
from typing import Any


def _digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def extension_directory(candidate_root: Path, descriptor: dict[str, Any]) -> Path:
    """Resolve an addition directory without allowing paths outside the candidate."""
    relative = Path(str(descriptor.get("path", "")))
    if not relative.parts or relative.is_absolute() or ".." in relative.parts:
        raise ValueError("Native skill extension must use a relative candidate path")
    directory = (candidate_root / relative).resolve()
    if not directory.is_relative_to(candidate_root.resolve()):
        raise ValueError("Native skill extension is outside the candidate directory")
    appendix = directory / "SKILL.md"
    if not appendix.is_file() or not appendix.resolve().is_relative_to(directory):
        raise FileNotFoundError(f"Native skill extension is missing its appendix: {directory}")
    expected = str(descriptor.get("appendix_sha256", ""))
    if not expected or _digest(appendix) != expected:
        raise ValueError(f"Native skill extension digest mismatch: {directory}")
    return directory


def validate_native_dependencies(source_skills: dict[str, Any], dependencies: dict[str, str]) -> None:
    """Reject a different native SKILL version before constructing a replay."""
    for name, expected in dependencies.items():
        if name not in source_skills:
            raise KeyError(f"External SkillsBench task is missing native skill: {name}")
        document = source_skills[name].path / "SKILL.md"
        if not expected or _digest(document) != expected:
            raise ValueError(f"External native skill digest mismatch: {name}")


def apply_native_extensions(
    *,
    candidate_root: Path,
    mounted_skills_root: Path,
    extensions: dict[str, Any],
) -> None:
    """Append authored text to the original document and preserve custom attachments."""
    for name, descriptor in extensions.items():
        if Path(name).name != name or name in {"", ".", ".."}:
            raise ValueError(f"Invalid native skill name: {name}")
        if not isinstance(descriptor, dict):
            raise ValueError(f"Native skill extension descriptor must be an object: {name}")
        directory = extension_directory(candidate_root, descriptor)
        target = mounted_skills_root / name
        document = target / "SKILL.md"
        if not document.is_file():
            raise FileNotFoundError(f"Native skill was not mounted: {name}")
        expected = str(descriptor.get("base_sha256", ""))
        if not expected or _digest(document) != expected:
            raise ValueError(f"External native skill digest mismatch: {name}")
        document.write_bytes(document.read_bytes().rstrip() + (directory / "SKILL.md").read_bytes())
        for source in directory.rglob("*"):
            if not source.is_file() or source == directory / "SKILL.md":
                continue
            if not source.resolve().is_relative_to(directory):
                raise ValueError(f"Native skill attachment is outside its extension: {source.name}")
            destination = target / source.relative_to(directory)
            if destination.exists():
                raise FileExistsError(f"Native skill attachment would overwrite a source asset: {source.name}")
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, destination)
