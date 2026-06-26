from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

ChunkType      = Literal["function", "class", "module", "test", "config", "raw"]
Classification = Literal["new_feature", "bug_fix", "refactor", "test", "config", "dep", "unknown"]
ChangeType     = Literal["added", "modified", "deleted", "renamed"]
LineType       = Literal["added", "removed", "context"]


@dataclass
class DiffLine:
    line_type:   LineType
    content:     str
    new_lineno:  int | None = None
    old_lineno:  int | None = None


@dataclass
class Hunk:
    old_start:  int
    old_length: int
    new_start:  int
    new_length: int
    lines:      list[DiffLine] = field(default_factory=list)


@dataclass
class FileDiff:
    filename:     str
    change_type:  ChangeType
    language:     str           # "python", "typescript", "yaml", "unknown", …
    hunks:        list[Hunk]   = field(default_factory=list)
    old_filename: str | None   = None   # populated for renames


@dataclass
class SemanticChunk:
    """One meaningful unit of change — maps 1-to-1 with a DiffChunk DB row."""
    file_path:      str
    start_line:     int
    end_line:       int
    chunk_type:     ChunkType
    classification: Classification
    complexity:     int
    symbol_name:    str | None      # function / class name; None for module-level
    content:        str             # joined added+removed lines
    diff_lines:     list[DiffLine] = field(default_factory=list)
    language:       str            = "unknown"
    change_type:    ChangeType     = "modified"
