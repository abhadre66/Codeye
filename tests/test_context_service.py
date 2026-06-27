"""
Tests for ContextService — PR context enrichment and reviewer suggestion.
GitHubRepository is fully mocked.
"""

from unittest.mock import AsyncMock, MagicMock

import pytest

from reviewmind.services.context_service import (
    ContextService,
    FileContributor,
    PRContext,
    ReviewerSuggestion,
)
from reviewmind.services.github.repository import (
    CommitSummary,
    GitHubRepository,
    IssueSummary,
    PRFile,
    PRSummary,
)


def _make_pr(author="dev-author", body="Fixes #5") -> PRSummary:
    return PRSummary(
        number=1, title="Test PR", author=author, state="open",
        base_branch="main", head_sha="abc123", additions=10,
        deletions=2, changed_files=1, body=body, url="https://github.com/x",
        owner="acme", repo="app",
    )


def _make_file(filename: str) -> PRFile:
    return PRFile(filename=filename, status="modified", additions=5, deletions=1, patch="")


def _make_commit(author: str, message: str = "update something") -> CommitSummary:
    return CommitSummary(sha="abc", message=message, author=author, authored_at="2024-01-01T00:00:00Z")


@pytest.fixture
def mock_repo():
    repo = MagicMock(spec=GitHubRepository)
    repo.get_pr = AsyncMock(return_value=_make_pr())
    repo.get_pr_files = AsyncMock(return_value=[
        _make_file("src/auth.py"),
        _make_file("src/db.py"),
    ])
    repo.get_commits_for_files = AsyncMock(return_value={
        "src/auth.py": [
            _make_commit("sarah-c", "Fix auth token validation"),
            _make_commit("jmiles", "Add rate limiting"),
            _make_commit("sarah-c", "Refactor auth module"),
        ],
        "src/db.py": [
            _make_commit("jmiles", "Add connection pooling"),
        ],
    })
    repo.get_related_prs = AsyncMock(return_value=[])
    repo.get_linked_issues = AsyncMock(return_value=[])
    repo.get_codeowners = AsyncMock(return_value="")
    return repo


@pytest.fixture
def svc(mock_repo):
    return ContextService(mock_repo)


# ── _parse_issue_numbers ──────────────────────────────────────────────────────

def test_parse_issue_numbers_fixes_syntax(svc):
    body = "Fixes #42 and closes #100"
    result = svc._parse_issue_numbers(body)
    assert 42 in result
    assert 100 in result


def test_parse_issue_numbers_bare_hash(svc):
    body = "See #7 for context"
    result = svc._parse_issue_numbers(body)
    assert 7 in result


def test_parse_issue_numbers_deduplicates(svc):
    body = "Fixes #5, see also #5"
    result = svc._parse_issue_numbers(body)
    assert result.count(5) == 1


def test_parse_issue_numbers_empty_body(svc):
    assert svc._parse_issue_numbers("") == []


# ── _build_contributors ───────────────────────────────────────────────────────

def test_build_contributors_aggregates_counts(svc):
    commits_by_file = {
        "src/auth.py": [
            _make_commit("sarah-c", "fix auth"),
            _make_commit("jmiles", "add rate limiting"),
            _make_commit("sarah-c", "refactor"),
        ]
    }
    result = svc._build_contributors(commits_by_file)
    contributors = result["src/auth.py"]
    sarah = next(c for c in contributors if c.username == "sarah-c")
    jmiles = next(c for c in contributors if c.username == "jmiles")
    assert sarah.commit_count == 2
    assert jmiles.commit_count == 1
    assert contributors[0].username == "sarah-c"  # sorted by count desc


# ── _rank_reviewers ───────────────────────────────────────────────────────────

def test_rank_reviewers_excludes_pr_author(svc):
    commits = {"src/auth.py": [_make_commit("dev-author")]}
    result = svc._rank_reviewers("dev-author", commits, "", ["src/auth.py"])
    usernames = [r.username for r in result]
    assert "dev-author" not in usernames


def test_rank_reviewers_scores_by_commit_count(svc):
    commits = {
        "src/auth.py": [
            _make_commit("alice"),
            _make_commit("alice"),
            _make_commit("bob"),
        ]
    }
    result = svc._rank_reviewers("dev", commits, "", ["src/auth.py"])
    assert result[0].username == "alice"
    assert result[0].score >= result[1].score


def test_rank_reviewers_codeowners_score_higher(svc):
    commits = {"src/auth.py": [_make_commit("alice"), _make_commit("bob")]}
    codeowners = "src/auth.py @charlie"
    result = svc._rank_reviewers("dev", commits, codeowners, ["src/auth.py"])
    charlie = next((r for r in result if r.username == "charlie"), None)
    assert charlie is not None
    assert charlie.score >= 3  # CODEOWNERS bonus


def test_rank_reviewers_returns_at_most_5(svc):
    commits = {"f.py": [_make_commit(f"user{i}") for i in range(10)]}
    result = svc._rank_reviewers("dev", commits, "", ["f.py"])
    assert len(result) <= 5


# ── get_pr_context ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_pr_context_returns_structure(svc, mock_repo):
    mock_repo.get_pr.return_value = _make_pr(body="Fixes #42")
    mock_repo.get_linked_issues.return_value = [
        IssueSummary(number=42, title="Bug", state="open", body="", url="")
    ]
    ctx = await svc.get_pr_context("acme", "app", 1)

    assert isinstance(ctx, PRContext)
    assert ctx.pr.number == 1
    assert "src/auth.py" in ctx.file_contributors
    assert len(ctx.linked_issues) == 1
    assert ctx.linked_issues[0].number == 42


@pytest.mark.asyncio
async def test_get_pr_context_passes_file_paths_to_commits(svc, mock_repo):
    await svc.get_pr_context("acme", "app", 1)
    call_args = mock_repo.get_commits_for_files.call_args
    files_arg = call_args[0][2]
    assert "src/auth.py" in files_arg
    assert "src/db.py" in files_arg


# ── suggest_reviewers ─────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_suggest_reviewers_returns_list(svc):
    result = await svc.suggest_reviewers("acme", "app", 1)
    assert isinstance(result, list)
    for r in result:
        assert isinstance(r, ReviewerSuggestion)


@pytest.mark.asyncio
async def test_suggest_reviewers_excludes_author(svc, mock_repo):
    mock_repo.get_commits_for_files.return_value = {
        "src/auth.py": [_make_commit("dev-author")]
    }
    result = await svc.suggest_reviewers("acme", "app", 1)
    assert all(r.username != "dev-author" for r in result)
