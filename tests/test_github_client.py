"""
Phase 2 tests — GitHub client + repository service.
All GitHub HTTP calls are mocked with respx. No real network traffic.
"""

import json
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
import respx

from reviewmind.services.github.client import (
    ForbiddenError,
    GitHubClient,
    GitHubError,
    NotFoundError,
    RateLimitError,
)
from reviewmind.services.github.repository import GitHubRepository, PRSummary

# ── Fixtures ──────────────────────────────────────────────────────────────────

FIXTURES = Path(__file__).parent / "fixtures" / "github"
PR_DATA = json.loads((FIXTURES / "pr.json").read_text())
PR_FILES_DATA = json.loads((FIXTURES / "pr_files.json").read_text())

RATE_HEADERS = {
    "x-ratelimit-limit": "5000",
    "x-ratelimit-remaining": "4999",
    "x-ratelimit-reset": "1700000000",
    "x-ratelimit-used": "1",
}

RAW_DIFF = (
    "diff --git a/auth.py b/auth.py\n"
    "--- a/auth.py\n"
    "+++ b/auth.py\n"
    "@@ -1,3 +1,5 @@\n"
    "+import jwt\n"
    "+\n"
    " def login():\n"
    "     pass\n"
)


@pytest.fixture
def client():
    return GitHubClient(token="test-token-abc")


@pytest.fixture
def repo(client):
    return GitHubRepository(client)


# ── GitHubClient tests ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_returns_parsed_json(client):
    with respx.mock:
        respx.get("https://api.github.com/repos/acme/app/pulls/42").mock(
            return_value=httpx.Response(200, json=PR_DATA, headers=RATE_HEADERS)
        )
        resp = await client.get("/repos/acme/app/pulls/42")

    assert resp.status_code == 200
    assert resp.body["number"] == 42
    assert resp.rate_limit.remaining == 4999


@pytest.mark.asyncio
async def test_get_returns_raw_text_for_diff(client):
    with respx.mock:
        respx.get("https://api.github.com/repos/acme/app/pulls/42").mock(
            return_value=httpx.Response(
                200,
                text=RAW_DIFF,
                headers={**RATE_HEADERS, "content-type": "text/x-diff"},
            )
        )
        resp = await client.get(
            "/repos/acme/app/pulls/42",
            accept="application/vnd.github.v3.diff",
        )

    assert "diff --git" in resp.body


@pytest.mark.asyncio
async def test_get_raises_not_found(client):
    with respx.mock:
        respx.get("https://api.github.com/repos/acme/app/pulls/999").mock(
            return_value=httpx.Response(404, json={"message": "Not Found"})
        )
        with pytest.raises(NotFoundError):
            await client.get("/repos/acme/app/pulls/999")


@pytest.mark.asyncio
async def test_get_raises_rate_limit_on_403(client):
    with respx.mock:
        respx.get("https://api.github.com/repos/acme/app/pulls/1").mock(
            return_value=httpx.Response(
                403,
                json={"message": "rate limit exceeded"},
                headers={"x-ratelimit-remaining": "0"},
            )
        )
        with pytest.raises(RateLimitError):
            await client.get("/repos/acme/app/pulls/1")


@pytest.mark.asyncio
async def test_get_raises_forbidden_on_403_with_quota_left(client):
    """A 403 that is NOT rate limiting (e.g. missing OAuth scope) must raise
    ForbiddenError so it isn't retried or misreported as a rate limit."""
    with respx.mock:
        respx.get("https://api.github.com/repos/acme/app/pulls/1").mock(
            return_value=httpx.Response(
                403,
                json={"message": "Resource not accessible by personal access token"},
                headers=RATE_HEADERS,
            )
        )
        with pytest.raises(ForbiddenError):
            await client.get("/repos/acme/app/pulls/1")


@pytest.mark.asyncio
async def test_etag_304_returns_not_modified(client):
    with respx.mock:
        respx.get("https://api.github.com/repos/acme/app/pulls/42").mock(
            return_value=httpx.Response(304, headers=RATE_HEADERS)
        )
        resp = await client.get("/repos/acme/app/pulls/42", if_none_match='"abc123"')

    assert resp.not_modified is True
    assert resp.body is None


@pytest.mark.asyncio
async def test_paginate_follows_link_header(client):
    """paginate() follows Link: rel=next across two pages."""
    base = "https://api.github.com"
    p2 = f"{base}/repos/acme/app/pulls/42/files?page=2"

    page1 = httpx.Response(
        200,
        json=[PR_FILES_DATA[0]],
        headers={**RATE_HEADERS, "link": f'<{p2}>; rel="next"'},
    )
    page2 = httpx.Response(200, json=[PR_FILES_DATA[1]], headers=RATE_HEADERS)

    responses = [page1, page2]
    idx = 0

    async def fake_get(url, **kwargs):
        nonlocal idx
        r = responses[idx]
        idx += 1
        return r

    with patch.object(client._http, "get", side_effect=fake_get):
        items = []
        async for item in client.paginate("/repos/acme/app/pulls/42/files"):
            items.append(item)

    assert len(items) == 2
    assert items[0]["filename"] == PR_FILES_DATA[0]["filename"]
    assert items[1]["filename"] == PR_FILES_DATA[1]["filename"]


@pytest.mark.asyncio
async def test_next_url_parses_link_header():
    link = '<https://api.github.com/foo?page=2>; rel="next", <https://api.github.com/foo?page=5>; rel="last"'
    url = GitHubClient._next_url(link)
    assert url == "https://api.github.com/foo?page=2"


@pytest.mark.asyncio
async def test_next_url_returns_none_when_no_next():
    link = '<https://api.github.com/foo?page=1>; rel="prev"'
    assert GitHubClient._next_url(link) is None


# ── GitHubRepository tests ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_get_pr_returns_pr_summary(repo):
    with respx.mock:
        respx.get("https://api.github.com/repos/acme/app/pulls/42").mock(
            return_value=httpx.Response(
                200,
                json=PR_DATA,
                headers={**RATE_HEADERS, "etag": '"etag-v1"'},
            )
        )
        with patch("reviewmind.services.github.repository.get_json", new=AsyncMock(return_value=None)), \
             patch("reviewmind.services.github.repository.set_json", new=AsyncMock()):
            pr = await repo.get_pr("acme", "app", 42)

    assert isinstance(pr, PRSummary)
    assert pr.number == 42
    assert pr.title == "Add JWT auth middleware"
    assert pr.author == "abhishek"
    assert pr.state == "open"
    assert pr.additions == 120
    assert pr.deletions == 30


@pytest.mark.asyncio
async def test_get_pr_diff_returns_string(repo):
    with patch("reviewmind.services.github.repository.cache_aside") as mock_cache:
        mock_cache.return_value = (RAW_DIFF, False)
        diff = await repo.get_pr_diff("acme", "app", 42)

    assert "diff --git" in diff


@pytest.mark.asyncio
async def test_get_pr_files_returns_list(repo):
    with patch("reviewmind.services.github.repository.cache_aside") as mock_cache:
        mock_cache.return_value = (PR_FILES_DATA, False)
        files = await repo.get_pr_files("acme", "app", 42)

    assert len(files) == 2
    assert files[0].filename == "reviewmind/api/auth.py"
    assert files[0].status == "added"
    assert files[1].status == "modified"


@pytest.mark.asyncio
async def test_get_pr_cache_hit_on_304(repo):
    """On 304 Not Modified the repo serves from Redis without re-parsing."""
    with respx.mock:
        respx.get("https://api.github.com/repos/acme/app/pulls/42").mock(
            return_value=httpx.Response(304, headers=RATE_HEADERS)
        )
        with patch("reviewmind.services.github.repository.get_json") as mock_get, \
             patch("reviewmind.services.github.repository.set_json", new=AsyncMock()):
            mock_get.side_effect = ['"etag-v1"', PR_DATA]
            pr = await repo.get_pr("acme", "app", 42)

    assert pr.number == 42
