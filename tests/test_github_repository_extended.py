"""
Tests for the 7 new GitHubRepository methods added in Phase 6.
Follows the same respx + cache_aside patching pattern as test_github_client.py.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, patch

import httpx
import pytest
import respx

from reviewmind.services.github.client import GitHubClient, NotFoundError
from reviewmind.services.github.repository import (
    CheckRun,
    CommitSummary,
    GitHubRepository,
    IssueSummary,
    ReviewComment,
    ReviewSummary,
)

FIXTURES = Path(__file__).parent / "fixtures" / "github"
COMMITS_DATA = json.loads((FIXTURES / "commits.json").read_text())
REVIEWS_DATA = json.loads((FIXTURES / "reviews.json").read_text())
REVIEW_COMMENTS_DATA = json.loads((FIXTURES / "review_comments.json").read_text())
CHECK_RUNS_DATA = json.loads((FIXTURES / "check_runs.json").read_text())

RATE_HEADERS = {
    "x-ratelimit-limit": "5000",
    "x-ratelimit-remaining": "4999",
    "x-ratelimit-reset": "1700000000",
    "x-ratelimit-used": "1",
}


@pytest.fixture
def client():
    return GitHubClient(token="test-token")


@pytest.fixture
def repo(client):
    return GitHubRepository(client)


# ── get_commits_for_files ─────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_commits_for_files_returns_dict(repo):
    with patch("reviewmind.services.github.repository.cache_aside") as mock_cache:
        mock_cache.side_effect = [
            (COMMITS_DATA, False),
            (COMMITS_DATA, False),
        ]
        result = await repo.get_commits_for_files("acme", "app", ["src/auth.py", "src/db.py"])

    assert "src/auth.py" in result
    assert "src/db.py" in result
    assert isinstance(result["src/auth.py"][0], CommitSummary)
    assert result["src/auth.py"][0].author == "sarah-c"
    assert result["src/auth.py"][0].message == "Fix auth token validation"


@pytest.mark.asyncio
async def test_get_commits_for_files_caps_at_20(repo):
    files = [f"file_{i}.py" for i in range(30)]
    with patch("reviewmind.services.github.repository.cache_aside") as mock_cache:
        mock_cache.return_value = ([], False)
        result = await repo.get_commits_for_files("acme", "app", files)

    assert len(result) == 20
    assert mock_cache.call_count == 20


# ── get_related_prs ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_related_prs_returns_list(repo):
    pr_data = {
        "number": 99,
        "title": "Add feature X",
        "user": {"login": "dev"},
        "state": "open",
        "base": {"ref": "main"},
        "head": {"sha": "abc123"},
        "additions": 10,
        "deletions": 2,
        "changed_files": 1,
        "body": "",
        "html_url": "https://github.com/acme/app/pull/99",
    }
    with patch("reviewmind.services.github.repository.cache_aside") as mock_cache:
        mock_cache.return_value = ([pr_data], False)
        result = await repo.get_related_prs("acme", "app", [])

    assert len(result) == 1
    assert result[0].number == 99
    assert result[0].title == "Add feature X"


# ── get_linked_issues ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_linked_issues_returns_list(repo):
    issue_data = {
        "number": 42,
        "title": "Bug: auth fails on timeout",
        "state": "open",
        "body": "Steps to reproduce...",
        "html_url": "https://github.com/acme/app/issues/42",
    }
    with patch("reviewmind.services.github.repository.cache_aside") as mock_cache:
        mock_cache.return_value = (issue_data, False)
        result = await repo.get_linked_issues("acme", "app", [42])

    assert len(result) == 1
    assert isinstance(result[0], IssueSummary)
    assert result[0].number == 42
    assert result[0].title == "Bug: auth fails on timeout"


@pytest.mark.asyncio
async def test_get_linked_issues_empty_list(repo):
    result = await repo.get_linked_issues("acme", "app", [])
    assert result == []


@pytest.mark.asyncio
async def test_get_linked_issues_skips_not_found(repo):
    with patch("reviewmind.services.github.repository.cache_aside") as mock_cache:
        mock_cache.side_effect = NotFoundError(404, "issue not found")
        result = await repo.get_linked_issues("acme", "app", [999])

    assert result == []


# ── get_codeowners ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_codeowners_returns_content(repo):
    codeowners = "* @org/team\nsrc/auth.py @alice"
    with (
        patch("reviewmind.services.github.repository.get_json", return_value=None),
        patch("reviewmind.services.github.repository.set_json", new_callable=AsyncMock),
        patch.object(repo, "get_file_content", new_callable=AsyncMock) as mock_get,
    ):
        mock_get.return_value = codeowners
        result = await repo.get_codeowners("acme", "app")

    assert result == codeowners
    mock_get.assert_called_once_with("acme", "app", ".github/CODEOWNERS", "HEAD")


@pytest.mark.asyncio
async def test_get_codeowners_falls_back_to_root(repo):
    codeowners = "* @org/team"
    with (
        patch("reviewmind.services.github.repository.get_json", return_value=None),
        patch("reviewmind.services.github.repository.set_json", new_callable=AsyncMock),
        patch.object(repo, "get_file_content", new_callable=AsyncMock) as mock_get,
    ):
        mock_get.side_effect = [NotFoundError(404, "not found"), codeowners]
        result = await repo.get_codeowners("acme", "app")

    assert result == codeowners


@pytest.mark.asyncio
async def test_get_codeowners_returns_empty_when_not_found(repo):
    with (
        patch("reviewmind.services.github.repository.get_json", return_value=None),
        patch("reviewmind.services.github.repository.set_json", new_callable=AsyncMock),
        patch.object(repo, "get_file_content", new_callable=AsyncMock) as mock_get,
    ):
        mock_get.side_effect = NotFoundError(404, "not found")
        result = await repo.get_codeowners("acme", "app")

    assert result == ""


@pytest.mark.asyncio
async def test_get_codeowners_returns_cached(repo):
    with patch("reviewmind.services.github.repository.get_json", return_value="cached content"):
        result = await repo.get_codeowners("acme", "app")
    assert result == "cached content"


# ── get_check_runs ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_check_runs_returns_list(repo):
    with patch("reviewmind.services.github.repository.cache_aside") as mock_cache:
        mock_cache.return_value = (CHECK_RUNS_DATA["check_runs"], False)
        result = await repo.get_check_runs("acme", "app", "abc123")

    assert len(result) == 2
    assert isinstance(result[0], CheckRun)
    assert result[0].name == "ci/pytest"
    assert result[0].conclusion == "success"
    assert result[1].conclusion == "failure"


# ── get_pr_reviews ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_pr_reviews_returns_list(repo):
    with patch("reviewmind.services.github.repository.cache_aside") as mock_cache:
        mock_cache.return_value = (REVIEWS_DATA, False)
        result = await repo.get_pr_reviews("acme", "app", 42)

    assert len(result) == 2
    assert isinstance(result[0], ReviewSummary)
    assert result[0].author == "alice"
    assert result[0].state == "CHANGES_REQUESTED"
    assert result[1].state == "APPROVED"


# ── get_pr_review_comments ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_pr_review_comments_returns_list(repo):
    with patch("reviewmind.services.github.repository.cache_aside") as mock_cache:
        mock_cache.return_value = (REVIEW_COMMENTS_DATA, False)
        result = await repo.get_pr_review_comments("acme", "app", 42)

    assert len(result) == 3
    assert isinstance(result[0], ReviewComment)
    assert result[0].path == "src/auth.py"
    assert result[0].line == 42
    assert result[2].line is None  # null in fixture


# ── invalidate_pr (updated) ───────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_invalidate_pr_clears_reviews_and_comments():
    deleted_keys = []

    async def mock_delete(key):
        deleted_keys.append(key)

    with patch("reviewmind.services.github.repository.delete", side_effect=mock_delete):
        client = GitHubClient(token="test")
        repo = GitHubRepository(client)
        await repo.invalidate_pr("acme", "app", 42)

    assert any("reviews" in k for k in deleted_keys)
    assert any("review_comments" in k for k in deleted_keys)
