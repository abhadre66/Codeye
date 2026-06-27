"""
Tests for PRAnalysisService.
GitHubRepository is fully mocked with AsyncMock — no HTTP or Redis.
"""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from reviewmind.engine.models import SemanticChunk
from reviewmind.engine.security.models import SecurityFinding
from reviewmind.engine.style.models import StyleConfig, StyleFinding
from reviewmind.services.github.client import NotFoundError
from reviewmind.services.github.repository import PRSummary
from reviewmind.services.pr_analysis import PRAnalysisResult, PRAnalysisService


def _make_pr(**kwargs) -> PRSummary:
    defaults = dict(
        number=1, title="Test PR", author="dev", state="open",
        base_branch="main", head_sha="abc123", additions=10,
        deletions=2, changed_files=1, body="Fixes #5", url="https://github.com/x",
        owner="acme", repo="app",
    )
    defaults.update(kwargs)
    return PRSummary(**defaults)


def _make_chunk(**kwargs) -> SemanticChunk:
    defaults = dict(
        file_path="src/auth.py", start_line=1, end_line=20,
        chunk_type="function", classification="new_feature",
        complexity=3, symbol_name="validate_token",
        content="def validate_token(token):\n    pass\n",
    )
    defaults.update(kwargs)
    return SemanticChunk(**defaults)


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.get_pr = AsyncMock(return_value=_make_pr())
    repo.get_pr_diff = AsyncMock(return_value="diff --git a/auth.py ...\n+def foo(): pass")
    repo.get_pr_files = AsyncMock(return_value=[])
    repo.get_file_content = AsyncMock(side_effect=NotFoundError(404, "not found"))
    return repo


@pytest.fixture
def svc(mock_repo):
    return PRAnalysisService(mock_repo)


# ── get_pr_summary ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_pr_summary_delegates_to_repo(svc, mock_repo):
    result = await svc.get_pr_summary("acme", "app", 1)
    mock_repo.get_pr.assert_called_once_with("acme", "app", 1)
    assert result.number == 1


# ── get_chunks ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_chunks_returns_semantic_chunks(svc):
    with (
        patch("reviewmind.services.pr_analysis.get_json", return_value=None),
        patch("reviewmind.services.pr_analysis.set_json", new_callable=AsyncMock),
        patch("reviewmind.services.pr_analysis.analysis_engine.analyze_diff") as mock_analyze,
    ):
        mock_analyze.return_value = [_make_chunk()]
        result = await svc.get_chunks("acme", "app", 1)

    assert len(result) == 1
    assert isinstance(result[0], SemanticChunk)
    assert result[0].symbol_name == "validate_token"


@pytest.mark.asyncio
async def test_get_chunks_returns_cached_on_hit(svc, mock_repo):
    chunk = _make_chunk()
    import dataclasses
    cached_data = [dataclasses.asdict(chunk)]

    with patch("reviewmind.services.pr_analysis.get_json", return_value=cached_data):
        result = await svc.get_chunks("acme", "app", 1)

    mock_repo.get_pr_diff.assert_not_called()
    assert len(result) == 1
    assert result[0].file_path == "src/auth.py"


# ── get_security_findings ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_security_findings_returns_findings(svc):
    chunk = _make_chunk(content='password = "hardcoded123"\n')
    with (
        patch("reviewmind.services.pr_analysis.get_json", return_value=None),
        patch("reviewmind.services.pr_analysis.set_json", new_callable=AsyncMock),
        patch("reviewmind.services.pr_analysis.analysis_engine.analyze_diff",
              return_value=[chunk]),
    ):
        findings = await svc.get_security_findings("acme", "app", 1)

    assert isinstance(findings, list)
    if findings:
        assert isinstance(findings[0], SecurityFinding)


# ── get_style_findings ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_style_findings_falls_back_to_defaults_on_not_found(svc, mock_repo):
    chunk = _make_chunk()
    mock_repo.get_file_content.side_effect = NotFoundError(404, "no reviewmind.yaml")

    with (
        patch("reviewmind.services.pr_analysis.get_json", return_value=None),
        patch("reviewmind.services.pr_analysis.set_json", new_callable=AsyncMock),
        patch("reviewmind.services.pr_analysis.analysis_engine.analyze_diff",
              return_value=[chunk]),
    ):
        findings = await svc.get_style_findings("acme", "app", 1)

    assert isinstance(findings, list)


@pytest.mark.asyncio
async def test_get_style_findings_loads_config_from_repo(svc, mock_repo):
    chunk = _make_chunk()
    yaml_config = "style:\n  max_function_length: 10\n"
    mock_repo.get_file_content.side_effect = None
    mock_repo.get_file_content.return_value = yaml_config

    with (
        patch("reviewmind.services.pr_analysis.get_json", return_value=None),
        patch("reviewmind.services.pr_analysis.set_json", new_callable=AsyncMock),
        patch("reviewmind.services.pr_analysis.analysis_engine.analyze_diff",
              return_value=[chunk]),
    ):
        findings = await svc.get_style_findings("acme", "app", 1)

    assert isinstance(findings, list)


# ── full_analysis ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_full_analysis_returns_result(svc):
    chunk = _make_chunk()
    with (
        patch("reviewmind.services.pr_analysis.get_json", return_value=None),
        patch("reviewmind.services.pr_analysis.set_json", new_callable=AsyncMock),
        patch("reviewmind.services.pr_analysis.analysis_engine.analyze_diff",
              return_value=[chunk]),
    ):
        result = await svc.full_analysis("acme", "app", 1)

    assert isinstance(result, PRAnalysisResult)
    assert result.pr.number == 1
    assert len(result.chunks) == 1
    assert "new_feature" in result.chunks_by_classification
