"""
Snippet Comparison Service — before/after code comparison without a GitHub PR.

Takes two versions of the same code, synthesizes a unified diff using difflib,
and runs the full analysis pipeline on the delta. Useful for reviewing refactors
or checking whether a rewrite is actually safer/cleaner than the original.
"""

from __future__ import annotations

import difflib
from dataclasses import dataclass, field

from reviewmind.engine import analysis as analysis_engine
from reviewmind.engine.models import SemanticChunk
from reviewmind.engine.security import engine as security_engine
from reviewmind.engine.security.models import SecurityFinding
from reviewmind.engine.style import engine as style_engine
from reviewmind.engine.style.models import StyleConfig, StyleFinding
from reviewmind.core.logging import get_logger

logger = get_logger(__name__)


@dataclass
class ComparisonResult:
    filename: str
    raw_diff: str
    chunks_added: list[SemanticChunk]       # new_feature / refactor chunks
    chunks_removed: list[SemanticChunk]     # deleted change_type chunks
    security_findings: list[SecurityFinding]
    style_findings: list[StyleFinding]
    complexity_delta: int                   # after_complexity - before_complexity
    chunks_by_classification: dict[str, list[SemanticChunk]] = field(default_factory=dict)


async def compare_snippets(
    before: str,
    after: str,
    filename: str = "snippet.py",
    style_config: StyleConfig | None = None,
) -> ComparisonResult:
    """
    Compare two versions of the same code and analyze what changed.

    before: original code
    after:  revised code
    filename: used for language detection and diff headers
    """
    raw_diff = _make_unified_diff(before, after, filename)

    if not raw_diff:
        # No changes between before and after
        logger.info("snippet_compare_no_diff", filename=filename)
        return ComparisonResult(
            filename=filename,
            raw_diff="",
            chunks_added=[],
            chunks_removed=[],
            security_findings=[],
            style_findings=[],
            complexity_delta=0,
        )

    chunks = await analysis_engine.analyze_diff(raw_diff)
    security_findings = security_engine.scan(chunks)
    style_findings = style_engine.scan(chunks, style_config)

    chunks_added = [c for c in chunks if c.change_type in ("added", "modified")]
    chunks_removed = [c for c in chunks if c.change_type == "deleted"]

    before_complexity = _estimate_complexity(before)
    after_complexity = _estimate_complexity(after)
    complexity_delta = after_complexity - before_complexity

    by_class: dict[str, list[SemanticChunk]] = {}
    for chunk in chunks:
        by_class.setdefault(chunk.classification, []).append(chunk)

    logger.info(
        "snippet_compare_complete",
        filename=filename,
        chunks=len(chunks),
        security=len(security_findings),
        style=len(style_findings),
        complexity_delta=complexity_delta,
    )
    return ComparisonResult(
        filename=filename,
        raw_diff=raw_diff,
        chunks_added=chunks_added,
        chunks_removed=chunks_removed,
        security_findings=security_findings,
        style_findings=style_findings,
        complexity_delta=complexity_delta,
        chunks_by_classification=by_class,
    )


def _make_unified_diff(before: str, after: str, filename: str) -> str:
    # Ensure both inputs end with a newline so hunk counts are accurate
    before = before if before.endswith("\n") else before + "\n"
    after = after if after.endswith("\n") else after + "\n"
    before_lines = before.splitlines(keepends=True)
    after_lines = after.splitlines(keepends=True)
    return "".join(difflib.unified_diff(
        before_lines,
        after_lines,
        fromfile=f"a/{filename}",
        tofile=f"b/{filename}",
    ))


def _estimate_complexity(code: str) -> int:
    from reviewmind.engine.complexity import cyclomatic_complexity
    return cyclomatic_complexity(code)
