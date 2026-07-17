"""
Tests for ReviewService — history fetching, comment formatting, and post gate.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from reviewmind.services.github.repository import ReviewComment, ReviewSummary
from reviewmind.services.review_service import ReviewHistory, ReviewService


def _make_review(**kwargs) -> ReviewSummary:
    defaults = dict(id=1, author="alice", state="APPROVED", body="LGTM", submitted_at="2024-01-01T00:00:00Z")
    defaults.update(kwargs)
    return ReviewSummary(**defaults)


def _make_comment(**kwargs) -> ReviewComment:
    defaults = dict(id=1, path="src/auth.py", line=42, body="Add docstring", author="alice", created_at="2024-01-01T00:00:00Z")
    defaults.update(kwargs)
    return ReviewComment(**defaults)


@pytest.fixture
def mock_repo():
    repo = MagicMock()
    repo.get_pr_reviews = AsyncMock(return_value=[_make_review()])
    repo.get_pr_review_comments = AsyncMock(return_value=[_make_comment()])
    repo.post_review = AsyncMock(return_value={"id": 9001, "html_url": "https://github.com/x/pull/1/reviews/9001"})
    return repo


@pytest.fixture
def svc(mock_repo):
    return ReviewService(mock_repo)


# ── get_review_history ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_review_history_returns_history(svc):
    history = await svc.get_review_history("acme", "app", 1)
    assert isinstance(history, ReviewHistory)
    assert len(history.reviews) == 1
    assert len(history.inline_comments) == 1
    assert history.reviews[0].author == "alice"
    assert history.inline_comments[0].path == "src/auth.py"


@pytest.mark.asyncio
async def test_get_review_history_fetches_concurrently(svc, mock_repo):
    await svc.get_review_history("acme", "app", 1)
    mock_repo.get_pr_reviews.assert_called_once_with("acme", "app", 1)
    mock_repo.get_pr_review_comments.assert_called_once_with("acme", "app", 1)


# ── generate_review_comment ───────────────────────────────────────────────────

def test_generate_concise_comment(svc):
    finding = {"rule_id": "SEC001", "severity": "high", "message": "Hardcoded secret", "snippet": "password = 'abc'"}
    result = svc.generate_review_comment(finding, "concise")
    assert "SEC001" in result
    assert "high" in result
    assert "Hardcoded secret" in result


def test_generate_detailed_comment_includes_snippet(svc):
    finding = {"rule_id": "SEC001", "severity": "critical", "message": "Hardcoded secret", "snippet": "api_key = 'abc'"}
    result = svc.generate_review_comment(finding, "detailed")
    assert "api_key" in result
    assert "🔴" in result


def test_generate_educational_comment_includes_why(svc):
    finding = {"rule_id": "SEC001", "severity": "high", "message": "Hardcoded secret", "snippet": ""}
    result = svc.generate_review_comment(finding, "educational")
    assert "Why this matters" in result
    assert "Rotate" in result or "environment variable" in result


def test_generate_educational_unknown_rule(svc):
    finding = {"rule_id": "UNKNOWN", "severity": "info", "message": "Something", "snippet": ""}
    result = svc.generate_review_comment(finding, "educational")
    assert "Something" in result


def test_generate_style_finding_detailed(svc):
    finding = {"rule_id": "STY002", "severity": "info", "message": "Missing docstring", "snippet": "def foo():"}
    result = svc.generate_review_comment(finding, "detailed")
    assert "STY002" in result
    assert "⚪" in result


# ── post_review ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_post_review_returns_preview_when_not_confirmed(svc, mock_repo):
    result = await svc.post_review(
        "acme", "app", 1,
        body="LGTM",
        event="COMMENT",
        confirmed=False,
    )
    assert result["preview"] is True
    assert "confirmed=true" in result["warning"]
    mock_repo.post_review.assert_not_called()


@pytest.mark.asyncio
async def test_post_review_calls_github_when_confirmed(svc, mock_repo):
    result = await svc.post_review(
        "acme", "app", 1,
        body="Looks good!",
        event="APPROVE",
        confirmed=True,
    )
    mock_repo.post_review.assert_called_once()
    assert result["id"] == 9001


@pytest.mark.asyncio
async def test_post_review_invalid_event_raises(svc):
    with pytest.raises(ValueError, match="event must be one of"):
        await svc.post_review("acme", "app", 1, body="x", event="MERGE", confirmed=True)


@pytest.mark.asyncio
async def test_post_review_empty_body_raises(svc):
    with pytest.raises(ValueError, match="body must not be empty"):
        await svc.post_review("acme", "app", 1, body="   ", event="COMMENT", confirmed=True)


@pytest.mark.asyncio
async def test_post_review_passes_inline_comments(svc, mock_repo):
    comments = [{"path": "src/auth.py", "line": 10, "body": "Add validation"}]
    await svc.post_review(
        "acme", "app", 1,
        body="Review body",
        event="REQUEST_CHANGES",
        comments=comments,
        confirmed=True,
    )
    call_kwargs = mock_repo.post_review.call_args[1]
    # Comments are normalized to GitHub's modern review-comment shape
    assert call_kwargs["comments"] == [
        {"path": "src/auth.py", "body": "Add validation", "line": 10, "side": "RIGHT"}
    ]


@pytest.mark.asyncio
async def test_post_review_folds_unanchored_comments_into_body(svc, mock_repo):
    comments = [
        {"path": "src/auth.py", "line": 10, "body": "Add validation"},
        {"path": "src/db.py", "body": "No line for this one"},
    ]
    await svc.post_review(
        "acme", "app", 1,
        body="Review body",
        event="COMMENT",
        comments=comments,
        confirmed=True,
    )
    call_kwargs = mock_repo.post_review.call_args[1]
    assert len(call_kwargs["comments"]) == 1
    assert "Other findings" in call_kwargs["body"]
    assert "No line for this one" in call_kwargs["body"]
