"""
PR Analysis Service — orchestrates GitHub → semantic diff → security → style.

This is the central service for ReviewMind. MCP tools call methods here;
engines and GitHub client are invoked beneath. Chunk results are cached so
security and style scans don't re-fetch or re-parse the diff.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from reviewmind.core.cache import cache_aside, get_json, pr_key, set_json
from reviewmind.core.logging import get_logger
from reviewmind.engine import analysis as analysis_engine
from reviewmind.engine.models import SemanticChunk
from reviewmind.engine.security import engine as security_engine
from reviewmind.engine.security.models import SecurityFinding
from reviewmind.engine.style import engine as style_engine
from reviewmind.engine.style.models import StyleConfig, StyleFinding, load_config
from reviewmind.services.fix_suggester import fix_for_security_finding, fix_for_style_finding
from reviewmind.services.github.client import NotFoundError
from reviewmind.services.github.repository import GitHubRepository, PRSummary, TTL_DIFF_OPEN

logger = get_logger(__name__)


@dataclass
class PRAnalysisResult:
    pr: PRSummary
    chunks: list[SemanticChunk]
    security_findings: list[SecurityFinding]
    style_findings: list[StyleFinding]
    chunks_by_classification: dict[str, list[SemanticChunk]] = field(default_factory=dict)
    files_changed: int = 0
    additions: int = 0
    deletions: int = 0


class PRAnalysisService:

    def __init__(self, repo: GitHubRepository) -> None:
        self._repo = repo

    async def get_pr_summary(self, owner: str, repo: str, pr_number: int) -> PRSummary:
        return await self._repo.get_pr(owner, repo, pr_number)

    async def get_chunks(
        self, owner: str, repo: str, pr_number: int
    ) -> list[SemanticChunk]:
        """Parse and classify the PR diff into SemanticChunks. Result is cached."""
        key = pr_key(owner, repo, pr_number, "chunks")
        cached = await get_json(key)
        if cached is not None:
            logger.info("pr_analysis_chunks_cache_hit", pr=pr_number)
            return _deserialize_chunks(cached)

        pr = await self._repo.get_pr(owner, repo, pr_number)
        raw_diff = await self._repo.get_pr_diff(owner, repo, pr_number)

        async def fetch_content(filename: str) -> str:
            return await self._repo.get_file_content(owner, repo, filename, pr.head_sha)

        chunks = await analysis_engine.analyze_diff(raw_diff, fetch_content)
        await set_json(key, _serialize_chunks(chunks), TTL_DIFF_OPEN)
        logger.info("pr_analysis_chunks_computed", pr=pr_number, count=len(chunks))
        return chunks

    async def get_security_findings(
        self, owner: str, repo: str, pr_number: int
    ) -> list[SecurityFinding]:
        chunks = await self.get_chunks(owner, repo, pr_number)
        return security_engine.scan(chunks)

    async def get_style_findings(
        self, owner: str, repo: str, pr_number: int
    ) -> list[StyleFinding]:
        chunks = await self.get_chunks(owner, repo, pr_number)
        config = await self._load_style_config(owner, repo, pr_number)
        return style_engine.scan(chunks, config)

    async def _load_style_config(
        self, owner: str, repo: str, pr_number: int
    ) -> StyleConfig:
        try:
            pr = await self._repo.get_pr(owner, repo, pr_number)
            yaml_str = await self._repo.get_file_content(
                owner, repo, "reviewmind.yaml", pr.head_sha
            )
            return load_config(yaml_str)
        except NotFoundError:
            logger.info("pr_analysis_no_reviewmind_yaml", repo=f"{owner}/{repo}")
            return StyleConfig()

    async def full_analysis(
        self, owner: str, repo: str, pr_number: int
    ) -> PRAnalysisResult:
        pr = await self.get_pr_summary(owner, repo, pr_number)
        chunks = await self.get_chunks(owner, repo, pr_number)
        security_findings = security_engine.scan(chunks)
        config = await self._load_style_config(owner, repo, pr_number)
        style_findings = style_engine.scan(chunks, config)

        for finding in security_findings:
            suggestion = fix_for_security_finding(finding)
            finding.fix_description = suggestion.fix_description
            finding.fix_example = suggestion.fix_example
        for finding in style_findings:
            suggestion = fix_for_style_finding(finding)
            finding.fix_description = suggestion.fix_description
            finding.fix_example = suggestion.fix_example

        by_class: dict[str, list[SemanticChunk]] = {}
        for chunk in chunks:
            by_class.setdefault(chunk.classification, []).append(chunk)

        return PRAnalysisResult(
            pr=pr,
            chunks=chunks,
            security_findings=security_findings,
            style_findings=style_findings,
            chunks_by_classification=by_class,
            files_changed=pr.changed_files,
            additions=pr.additions,
            deletions=pr.deletions,
        )


# ── Chunk serialization helpers ───────────────────────────────────────────────
# SemanticChunk contains dataclass fields; we cache as plain dicts and
# reconstruct on read to stay JSON-serializable.

def _serialize_chunks(chunks: list[SemanticChunk]) -> list[dict]:
    import dataclasses
    return [dataclasses.asdict(c) for c in chunks]


def _deserialize_chunks(raw: list[dict]) -> list[SemanticChunk]:
    from reviewmind.engine.models import DiffLine, Hunk  # noqa: F401 — used via dataclass
    result = []
    for d in raw:
        diff_lines = [
            _DiffLine(
                line_type=ln["line_type"],
                content=ln["content"],
                new_lineno=ln.get("new_lineno"),
                old_lineno=ln.get("old_lineno"),
            )
            for ln in d.get("diff_lines", [])
        ]
        result.append(
            SemanticChunk(
                file_path=d["file_path"],
                start_line=d["start_line"],
                end_line=d["end_line"],
                chunk_type=d["chunk_type"],
                classification=d["classification"],
                complexity=d["complexity"],
                symbol_name=d.get("symbol_name"),
                content=d["content"],
                diff_lines=diff_lines,
                language=d.get("language", "unknown"),
                change_type=d.get("change_type", "modified"),
            )
        )
    return result


# Import DiffLine under alias so the module-level import stays clean
from reviewmind.engine.models import DiffLine as _DiffLine  # noqa: E402
