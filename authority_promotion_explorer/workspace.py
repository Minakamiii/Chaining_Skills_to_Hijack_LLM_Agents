from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(slots=True)
class WorkspaceAttachment:
    rel_path: str
    abs_path: Path
    language: str
    content: str
    truncated: bool


def _ensure_within_root(root: Path, abs_path: Path, rel_path: str) -> None:
    if abs_path != root and root not in abs_path.parents:
        raise ValueError(f"Workspace file escapes root: {rel_path}")


def _guess_language(path: Path) -> str:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        return "csv"
    if suffix in {".md", ".markdown"}:
        return "markdown"
    if suffix in {".json", ".jsonl"}:
        return "json"
    if suffix in {".py"}:
        return "python"
    if suffix in {".txt", ""}:
        return "text"
    return suffix.removeprefix(".") or "text"


def load_path_attachments(
    root_path: Path,
    relative_paths: list[str],
    *,
    max_chars: int = 4000,
    rel_prefix: str = "",
) -> list[WorkspaceAttachment]:
    root = root_path.resolve()
    attachments: list[WorkspaceAttachment] = []

    for rel_path in relative_paths:
        abs_path = (root_path / rel_path).resolve()
        _ensure_within_root(root, abs_path, rel_path)
        if not abs_path.exists():
            raise FileNotFoundError(f"Workspace file not found: {rel_path}")
        if not abs_path.is_file():
            raise ValueError(f"Workspace path is not a file: {rel_path}")

        raw_bytes = abs_path.read_bytes()
        if b"\x00" in raw_bytes[:1024]:
            content = "[binary file omitted]"
            truncated = False
        else:
            decoded = raw_bytes.decode("utf-8", errors="replace")
            truncated = len(decoded) > max_chars
            content = decoded[:max_chars]

        attachments.append(
            WorkspaceAttachment(
                rel_path=f"{rel_prefix}{rel_path}" if rel_prefix else rel_path,
                abs_path=abs_path,
                language=_guess_language(abs_path),
                content=content,
                truncated=truncated,
            )
        )

    return attachments


def load_workspace_attachments(
    project_root: Path,
    relative_paths: list[str],
    *,
    max_chars: int = 4000,
) -> list[WorkspaceAttachment]:
    return load_path_attachments(project_root, relative_paths, max_chars=max_chars)


def render_workspace_context(attachments: list[WorkspaceAttachment]) -> str:
    if not attachments:
        return ""

    blocks = ["Visible file context. Reason only over these snippets."]
    for attachment in attachments:
        truncated_note = "\n[truncated]" if attachment.truncated else ""
        blocks.append(
            f"File: {attachment.rel_path}\n"
            f"```{attachment.language}\n"
            f"{attachment.content}{truncated_note}\n"
            f"```"
        )

    return "\n\n".join(blocks)
