"""
Code Analysis Service — analyze pasted code or uploaded files without a GitHub PR.

Used by the analyze_paste and analyze_upload MCP tools. Runs the same full pipeline
as PRAnalysisService (semantic chunking → security → style) but takes raw code
instead of a PR reference.
"""

from __future__ import annotations

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
class CodeAnalysisResult:
    filename: str
    chunks: list[SemanticChunk]
    security_findings: list[SecurityFinding]
    style_findings: list[StyleFinding]
    chunks_by_classification: dict[str, list[SemanticChunk]] = field(default_factory=dict)


async def analyze_paste(
    code: str,
    filename: str = "snippet.py",
    style_config: StyleConfig | None = None,
) -> CodeAnalysisResult:
    """Analyze a pasted code snippet through the full pipeline."""
    chunks = await analysis_engine.analyze_code(filename, code)
    return _build_result(filename, chunks, style_config)


async def analyze_uploads(
    files: list[dict],
    style_config: StyleConfig | None = None,
) -> list[CodeAnalysisResult]:
    """Analyze one or more uploaded files.

    files: list of {"name": str, "content": str} dicts (content is plain text).
    """
    results = []
    for f in files:
        filename = f.get("name", "upload.py")
        content = f.get("content", "")
        chunks = await analysis_engine.analyze_code(filename, content)
        results.append(_build_result(filename, chunks, style_config))
        logger.info("code_upload_analyzed", filename=filename, chunks=len(chunks))
    return results


def _build_result(
    filename: str,
    chunks: list[SemanticChunk],
    style_config: StyleConfig | None,
) -> CodeAnalysisResult:
    security_findings = security_engine.scan(chunks)
    style_findings = style_engine.scan(chunks, style_config)

    by_class: dict[str, list[SemanticChunk]] = {}
    for chunk in chunks:
        by_class.setdefault(chunk.classification, []).append(chunk)

    logger.info(
        "code_analysis_complete",
        filename=filename,
        chunks=len(chunks),
        security=len(security_findings),
        style=len(style_findings),
    )
    return CodeAnalysisResult(
        filename=filename,
        chunks=chunks,
        security_findings=security_findings,
        style_findings=style_findings,
        chunks_by_classification=by_class,
    )
