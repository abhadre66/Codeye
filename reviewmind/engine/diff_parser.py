from __future__ import annotations

from pathlib import Path

from unidiff import PatchSet

from reviewmind.engine.models import ChangeType, DiffLine, FileDiff, Hunk

_LANG_MAP: dict[str, str] = {
    ".py":   "python",
    ".js":   "javascript",
    ".ts":   "typescript",
    ".tsx":  "typescript",
    ".jsx":  "javascript",
    ".yaml": "yaml",
    ".yml":  "yaml",
    ".toml": "toml",
    ".json": "json",
    ".go":   "go",
    ".rb":   "ruby",
    ".rs":   "rust",
    ".java": "java",
    ".cs":   "csharp",
    ".md":   "markdown",
    ".sh":   "shell",
}


def _detect_language(filename: str) -> str:
    return _LANG_MAP.get(Path(filename).suffix.lower(), "unknown")


def _change_type(patched_file) -> ChangeType:
    if patched_file.is_added_file:
        return "added"
    if patched_file.is_removed_file:
        return "deleted"
    if patched_file.is_rename:
        return "renamed"
    return "modified"


def parse_diff(raw_diff: str) -> list[FileDiff]:
    """Parse a full unified diff string → list[FileDiff]."""
    if not raw_diff or not raw_diff.strip():
        return []

    patch = PatchSet.from_string(raw_diff)
    result: list[FileDiff] = []

    for pf in patch:
        fd = FileDiff(
            filename=pf.path,
            change_type=_change_type(pf),
            language=_detect_language(pf.path),
            old_filename=pf.source_file if pf.is_rename else None,
        )
        for hunk in pf:
            h = Hunk(
                old_start=hunk.source_start,
                old_length=hunk.source_length,
                new_start=hunk.target_start,
                new_length=hunk.target_length,
            )
            for line in hunk:
                if line.is_added:
                    lt = "added"
                elif line.is_removed:
                    lt = "removed"
                else:
                    lt = "context"
                h.lines.append(DiffLine(
                    line_type=lt,
                    content=line.value,
                    new_lineno=line.target_line_no,
                    old_lineno=line.source_line_no,
                ))
            fd.hunks.append(h)
        result.append(fd)

    return result


def synthetic_diff(filename: str, content: str) -> list[FileDiff]:
    """Wrap pasted/uploaded code as a single all-added FileDiff.

    Used by the paste and upload analysis paths where no real diff exists.
    """
    lines = content.splitlines(keepends=True)
    if not lines:
        lines = [""]

    hunk = Hunk(
        old_start=0,
        old_length=0,
        new_start=1,
        new_length=len(lines),
    )
    for i, line in enumerate(lines, start=1):
        hunk.lines.append(DiffLine(
            line_type="added",
            content=line,
            new_lineno=i,
            old_lineno=None,
        ))

    return [FileDiff(
        filename=filename,
        change_type="added",
        language=_detect_language(filename),
        hunks=[hunk],
    )]
