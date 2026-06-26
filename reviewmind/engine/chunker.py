from __future__ import annotations

import ast
from typing import Awaitable, Callable

from reviewmind.engine.models import (
    ChunkType,
    DiffLine,
    FileDiff,
    Hunk,
    SemanticChunk,
)

# Callable signature injected by callers — returns full file source for AST mapping.
FetchContent = Callable[[str], Awaitable[str]]


async def chunk_file_diffs(
    file_diffs: list[FileDiff],
    fetch_content: FetchContent | None = None,
) -> list[SemanticChunk]:
    """Convert a list of FileDiffs into SemanticChunks.

    For Python files: maps hunks to enclosing AST nodes (function/class).
    For all other files: one SemanticChunk per Hunk (chunk_type='raw').

    fetch_content: async callable (filename -> source str).  If None, all files
    use raw chunking even if they are Python.
    """
    chunks: list[SemanticChunk] = []

    for fd in file_diffs:
        if fd.language == "python" and fetch_content is not None:
            try:
                source = await fetch_content(fd.filename)
                chunks.extend(_chunk_python(fd, source))
            except Exception:
                chunks.extend(_chunk_raw(fd))
        else:
            chunks.extend(_chunk_raw(fd))

    return chunks


# ── Python AST chunking ───────────────────────────────────────────────────────

def _chunk_python(fd: FileDiff, source: str) -> list[SemanticChunk]:
    """Map hunks to Python AST FunctionDef / ClassDef nodes."""
    try:
        tree = ast.parse(source)
    except SyntaxError:
        return _chunk_raw(fd)

    # line_map[line_number] = (chunk_type, symbol_name, node_start, node_end)
    line_map: dict[int, tuple[ChunkType, str, int, int]] = {}
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            ntype: ChunkType = "function"
        elif isinstance(node, ast.ClassDef):
            ntype = "class"
        else:
            continue
        start = node.lineno
        end   = node.end_lineno or node.lineno
        for ln in range(start, end + 1):
            line_map[ln] = (ntype, node.name, start, end)

    # Group hunks by their enclosing AST node.
    # key = (ntype, name, node_start, node_end) or None for module-level code
    groups: dict[tuple | None, list[Hunk]] = {}
    for hunk in fd.hunks:
        node_key = _find_node_key(hunk, line_map)
        groups.setdefault(node_key, []).append(hunk)

    chunks: list[SemanticChunk] = []
    for node_key, hunks in groups.items():
        chunk = _build_chunk(fd, node_key, hunks)
        if chunk is not None:
            chunks.append(chunk)

    return chunks


def _find_node_key(hunk: Hunk, line_map: dict) -> tuple | None:
    """Return the AST node key for the first changed line in a hunk."""
    for line in hunk.lines:
        if line.line_type in ("added", "removed") and line.new_lineno:
            if line.new_lineno in line_map:
                return line_map[line.new_lineno]
    # Fallback: check old line numbers for removals
    for line in hunk.lines:
        if line.line_type == "removed" and line.old_lineno:
            if line.old_lineno in line_map:
                return line_map[line.old_lineno]
    return None  # module-level


def _build_chunk(
    fd: FileDiff,
    node_key: tuple | None,
    hunks: list[Hunk],
) -> SemanticChunk | None:
    all_lines: list[DiffLine] = [l for h in hunks for l in h.lines]
    changed = [l for l in all_lines if l.line_type in ("added", "removed")]
    if not changed:
        return None

    new_linenos = [l.new_lineno for l in all_lines if l.new_lineno]
    hunk_start = min(new_linenos) if new_linenos else 1
    hunk_end   = max(new_linenos) if new_linenos else hunk_start

    if node_key:
        ntype, name, node_start, node_end = node_key
        start = min(hunk_start, node_start)
        end   = max(hunk_end,   node_end)
    else:
        ntype, name = "module", None
        start, end  = hunk_start, hunk_end

    content = "".join(l.content for l in changed)

    return SemanticChunk(
        file_path=fd.filename,
        start_line=start,
        end_line=end,
        chunk_type=ntype,
        classification="unknown",   # filled by classifier
        complexity=0,               # filled by complexity module
        symbol_name=name,
        content=content,
        diff_lines=all_lines,
        language=fd.language,
        change_type=fd.change_type,
    )


# ── Raw chunking (non-Python or no fetch_content) ────────────────────────────

def _chunk_raw(fd: FileDiff) -> list[SemanticChunk]:
    """One SemanticChunk per Hunk — no AST involved."""
    chunks: list[SemanticChunk] = []
    for hunk in fd.hunks:
        new_linenos = [l.new_lineno for l in hunk.lines if l.new_lineno]
        start = min(new_linenos) if new_linenos else 1
        end   = max(new_linenos) if new_linenos else start
        changed = [l for l in hunk.lines if l.line_type in ("added", "removed")]
        content = "".join(l.content for l in changed)

        chunks.append(SemanticChunk(
            file_path=fd.filename,
            start_line=start,
            end_line=end,
            chunk_type="raw",
            classification="unknown",
            complexity=0,
            symbol_name=None,
            content=content,
            diff_lines=list(hunk.lines),
            language=fd.language,
            change_type=fd.change_type,
        ))
    return chunks
