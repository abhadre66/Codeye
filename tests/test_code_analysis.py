"""
Tests for code_analysis service — paste and upload paths.
No mocking needed: these are pure in-process pipeline runs.
"""

import pytest

from reviewmind.services.code_analysis import (
    CodeAnalysisResult,
    analyze_paste,
    analyze_uploads,
)


SIMPLE_PY = """\
def greet(name):
    print("Hello, " + name)
"""

HARDCODED_SECRET = """\
def connect():
    api_key = "sk-prod-abc123secretvalue"
    return api_key
"""

WILDCARD_IMPORT = """\
from os import *

def do_stuff():
    pass
"""


# ── analyze_paste ─────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_paste_returns_result():
    result = await analyze_paste(SIMPLE_PY, "greet.py")
    assert isinstance(result, CodeAnalysisResult)
    assert result.filename == "greet.py"
    assert isinstance(result.chunks, list)
    assert isinstance(result.security_findings, list)
    assert isinstance(result.style_findings, list)


@pytest.mark.asyncio
async def test_analyze_paste_detects_security_finding():
    result = await analyze_paste(HARDCODED_SECRET, "config.py")
    rule_ids = [f.rule_id for f in result.security_findings]
    assert "SEC001" in rule_ids


@pytest.mark.asyncio
async def test_analyze_paste_detects_style_violation():
    result = await analyze_paste(WILDCARD_IMPORT, "utils.py")
    rule_ids = [f.rule_id for f in result.style_findings]
    assert "STY004" in rule_ids


@pytest.mark.asyncio
async def test_analyze_paste_default_filename():
    result = await analyze_paste(SIMPLE_PY)
    assert result.filename == "snippet.py"


@pytest.mark.asyncio
async def test_analyze_paste_groups_by_classification():
    result = await analyze_paste(SIMPLE_PY, "greet.py")
    assert isinstance(result.chunks_by_classification, dict)
    all_chunks = [c for chunks in result.chunks_by_classification.values() for c in chunks]
    assert len(all_chunks) == len(result.chunks)


@pytest.mark.asyncio
async def test_analyze_paste_non_python_file():
    yaml_content = "name: my-service\nport: 8080\n"
    result = await analyze_paste(yaml_content, "config.yaml")
    assert result.filename == "config.yaml"
    assert isinstance(result.chunks, list)


# ── analyze_uploads ───────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_analyze_uploads_returns_one_result_per_file():
    files = [
        {"name": "auth.py", "content": SIMPLE_PY},
        {"name": "config.py", "content": HARDCODED_SECRET},
    ]
    results = await analyze_uploads(files)
    assert len(results) == 2
    assert results[0].filename == "auth.py"
    assert results[1].filename == "config.py"


@pytest.mark.asyncio
async def test_analyze_uploads_security_finding_in_correct_file():
    files = [
        {"name": "clean.py", "content": SIMPLE_PY},
        {"name": "secret.py", "content": HARDCODED_SECRET},
    ]
    results = await analyze_uploads(files)
    clean = next(r for r in results if r.filename == "clean.py")
    secret = next(r for r in results if r.filename == "secret.py")
    sec_rules_clean = [f.rule_id for f in clean.security_findings]
    sec_rules_secret = [f.rule_id for f in secret.security_findings]
    assert "SEC001" not in sec_rules_clean
    assert "SEC001" in sec_rules_secret


@pytest.mark.asyncio
async def test_analyze_uploads_single_file():
    files = [{"name": "main.py", "content": SIMPLE_PY}]
    results = await analyze_uploads(files)
    assert len(results) == 1
    assert isinstance(results[0], CodeAnalysisResult)


@pytest.mark.asyncio
async def test_analyze_uploads_empty_content():
    files = [{"name": "empty.py", "content": ""}]
    results = await analyze_uploads(files)
    assert len(results) == 1
    assert isinstance(results[0], CodeAnalysisResult)
    assert results[0].security_findings == []
    assert results[0].style_findings == []
