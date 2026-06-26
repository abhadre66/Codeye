from __future__ import annotations

from typing import Awaitable, Callable

from reviewmind.engine.chunker import FetchContent, chunk_file_diffs
from reviewmind.engine.classifier import classify
from reviewmind.engine.complexity import cyclomatic_complexity
from reviewmind.engine.diff_parser import parse_diff, synthetic_diff
from reviewmind.engine.models import SemanticChunk


async def analyze_diff(
    raw_diff: str,
    fetch_content: FetchContent | None = None,
) -> list[SemanticChunk]:
    """Full pipeline for a unified diff string (e.g., from get_pr_diff()).

    fetch_content: async (filename -> source) for AST chunking of Python files.
    Pass None to skip AST and use raw hunk-per-chunk for every file.
    """
    file_diffs = parse_diff(raw_diff)
    chunks     = await chunk_file_diffs(file_diffs, fetch_content)
    return _enrich(chunks)


async def analyze_code(filename: str, content: str) -> list[SemanticChunk]:
    """Pipeline for pasted or uploaded code (no real diff exists).

    Treats the entire file as newly added via a synthetic diff.
    """
    file_diffs = synthetic_diff(filename, content)
    chunks     = await chunk_file_diffs(file_diffs, fetch_content=None)
    return _enrich(chunks)


def _enrich(chunks: list[SemanticChunk]) -> list[SemanticChunk]:
    for chunk in chunks:
        chunk.classification = classify(chunk)
        chunk.complexity     = cyclomatic_complexity(chunk.content)
    return chunks
