from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Iterable

from .config import resolve_project_path
from .workspace import WorkspaceAttachment, load_path_attachments

DEFAULT_EXCLUDE_PATTERNS = (
    ".git",
    ".git/**",
    ".hg",
    ".hg/**",
    ".svn",
    ".svn/**",
    ".venv",
    ".venv/**",
    "node_modules",
    "node_modules/**",
    "__pycache__",
    "__pycache__/**",
    ".mypy_cache",
    ".mypy_cache/**",
    ".pytest_cache",
    ".pytest_cache/**",
    "dist",
    "dist/**",
    "build",
    "build/**",
    "target",
    "target/**",
    ".idea",
    ".idea/**",
    ".vscode",
    ".vscode/**",
)

DEFAULT_DISCOVERY_PATTERNS = (
    "README*",
    "pyproject.toml",
    "package.json",
    "Cargo.toml",
    "go.mod",
    "Makefile",
    "src/**/*",
    "app/**/*",
    "lib/**/*",
    "tests/**/*",
    "docs/**/*",
)


@dataclass(slots=True)
class ProjectContext:
    root: str = "."
    label: str = "target engineering repository"
    files: list[str] = field(default_factory=list)
    include: list[str] = field(default_factory=list)
    exclude: list[str] = field(default_factory=list)
    notes: str = ""
    max_files: int = 8
    max_chars_per_file: int = 3000
    tree_max_entries: int = 30
    tree_max_depth: int = 3

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "ProjectContext":
        return cls(
            root=str(data.get("root", ".")),
            label=str(data.get("label", "target engineering repository")),
            files=[str(item) for item in data.get("files", [])],
            include=[str(item) for item in data.get("include", [])],
            exclude=[str(item) for item in data.get("exclude", [])],
            notes=str(data.get("notes", "")),
            max_files=max(1, int(data.get("max_files", 8))),
            max_chars_per_file=max(200, int(data.get("max_chars_per_file", 3000))),
            tree_max_entries=max(1, int(data.get("tree_max_entries", 30))),
            tree_max_depth=max(1, int(data.get("tree_max_depth", 3))),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "root": self.root,
            "label": self.label,
            "files": self.files,
            "include": self.include,
            "exclude": self.exclude,
            "notes": self.notes,
            "max_files": self.max_files,
            "max_chars_per_file": self.max_chars_per_file,
            "tree_max_entries": self.tree_max_entries,
            "tree_max_depth": self.tree_max_depth,
        }


@dataclass(slots=True)
class ProjectSnapshot:
    root: Path
    label: str
    selected_files: list[str]
    tree_preview: list[str]
    attachments: list[WorkspaceAttachment]
    notes: str = ""

    def render_summary(self) -> str:
        blocks = [
            f"Read-only repository snapshot: {self.label}. Paths prefixed with `project::` come from the target repo.",
            f"Snapshot root name: {self.root.name or str(self.root)}",
        ]
        if self.notes.strip():
            blocks.append(f"Snapshot notes: {self.notes.strip()}")

        if self.selected_files:
            selected = "\n".join(f"- {path}" for path in self.selected_files)
            blocks.append(f"Selected repository files ({len(self.selected_files)}):\n{selected}")
        else:
            blocks.append("Selected repository files: none matched the current snapshot filters.")

        if self.tree_preview:
            tree = "\n".join(f"- {entry}" for entry in self.tree_preview)
            blocks.append(f"Repository tree preview:\n{tree}")

        return "\n\n".join(blocks)

    def to_dict(self) -> dict[str, object]:
        return {
            "root": str(self.root),
            "label": self.label,
            "selected_files": self.selected_files,
            "tree_preview": self.tree_preview,
            "notes": self.notes,
            "attachment_paths": [attachment.rel_path for attachment in self.attachments],
        }


def _matches_any(rel_path: str, patterns: Iterable[str]) -> bool:
    pure_path = PurePosixPath(rel_path)
    return any(pure_path.match(pattern) for pattern in patterns if pattern.strip())


def _is_within_root(root: Path, path: Path) -> bool:
    return path == root or root in path.parents


def _iter_candidate_paths(root: Path, patterns: Iterable[str]) -> Iterable[Path]:
    for pattern in patterns:
        if not pattern.strip():
            continue
        yield from sorted(root.glob(pattern))


def _collect_selected_files(root: Path, spec: ProjectContext) -> list[str]:
    exclude_patterns = list(DEFAULT_EXCLUDE_PATTERNS) + list(spec.exclude)
    selected: list[str] = []
    seen: set[str] = set()

    candidate_patterns = list(spec.include)
    if not spec.files and not candidate_patterns:
        candidate_patterns = list(DEFAULT_DISCOVERY_PATTERNS)

    explicit_paths = [root / rel_path for rel_path in spec.files]
    for candidate in explicit_paths + list(_iter_candidate_paths(root, candidate_patterns)):
        resolved = candidate.resolve()
        if not candidate.exists() or not candidate.is_file():
            continue
        if not _is_within_root(root, resolved):
            continue

        rel_path = resolved.relative_to(root).as_posix()
        if _matches_any(rel_path, exclude_patterns):
            continue
        if rel_path in seen:
            continue

        selected.append(rel_path)
        seen.add(rel_path)
        if len(selected) >= spec.max_files:
            break

    return selected


def _build_tree_preview(root: Path, *, exclude_patterns: list[str], max_entries: int, max_depth: int) -> list[str]:
    entries: list[str] = []

    def visit(path: Path, depth: int) -> bool:
        if depth > max_depth:
            return False

        for child in sorted(path.iterdir(), key=lambda item: (not item.is_dir(), item.name.lower())):
            rel_path = child.relative_to(root).as_posix()
            if _matches_any(rel_path, exclude_patterns):
                continue

            entry = f"{rel_path}/" if child.is_dir() else rel_path
            entries.append(entry)
            if len(entries) >= max_entries:
                return True

            if child.is_dir() and visit(child, depth + 1):
                return True

        return False

    visit(root, 1)
    if entries and len(entries) >= max_entries:
        entries[-1] = entries[-1] + " ..."
    return entries


def build_project_snapshot(
    lab_root: Path,
    spec: ProjectContext,
    *,
    project_root_override: Path | None = None,
) -> ProjectSnapshot:
    raw_root = project_root_override or resolve_project_path(lab_root, spec.root)
    target_root = raw_root.resolve()
    if not target_root.exists():
        raise FileNotFoundError(f"Project root not found: {target_root}")
    if not target_root.is_dir():
        raise ValueError(f"Project root is not a directory: {target_root}")

    selected_files = _collect_selected_files(target_root, spec)
    attachments = load_path_attachments(
        target_root,
        selected_files,
        max_chars=spec.max_chars_per_file,
        rel_prefix="project::",
    )
    tree_preview = _build_tree_preview(
        target_root,
        exclude_patterns=list(DEFAULT_EXCLUDE_PATTERNS) + list(spec.exclude),
        max_entries=spec.tree_max_entries,
        max_depth=spec.tree_max_depth,
    )
    return ProjectSnapshot(
        root=target_root,
        label=spec.label,
        selected_files=selected_files,
        tree_preview=tree_preview,
        attachments=attachments,
        notes=spec.notes,
    )
