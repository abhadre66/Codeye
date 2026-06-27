"""
Tests for SnippetCompare service — before/after code comparison.
"""

import pytest

from reviewmind.services.snippet_compare import ComparisonResult, compare_snippets


BEFORE = """\
def get_user(user_id):
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
"""

AFTER_FIXED = """\
def get_user(user_id: int):
    \"\"\"Fetch a user by ID using a parameterized query.\"\"\"
    return db.execute("SELECT * FROM users WHERE id = %s", (user_id,))
"""

AFTER_WORSE = """\
def get_user(user_id):
    api_key = "sk-prod-hardcoded-secret"
    query = f"SELECT * FROM users WHERE id = {user_id}"
    return db.execute(query)
"""

IDENTICAL = """\
def hello():
    print("hello")
"""


@pytest.mark.asyncio
async def test_compare_returns_result():
    result = await compare_snippets(BEFORE, AFTER_FIXED, "db.py")
    assert isinstance(result, ComparisonResult)
    assert result.filename == "db.py"
    assert result.raw_diff != ""


@pytest.mark.asyncio
async def test_compare_identical_code_returns_empty():
    result = await compare_snippets(IDENTICAL, IDENTICAL, "hello.py")
    assert result.raw_diff == ""
    assert result.chunks_added == []
    assert result.chunks_removed == []
    assert result.security_findings == []
    assert result.style_findings == []
    assert result.complexity_delta == 0


@pytest.mark.asyncio
async def test_compare_detects_fix_removes_sql_injection():
    result = await compare_snippets(BEFORE, AFTER_FIXED, "db.py")
    # The AFTER code fixes the SQL injection — no findings expected in the new code
    sec_rule_ids = [f.rule_id for f in result.security_findings]
    assert "SEC002" not in sec_rule_ids


@pytest.mark.asyncio
async def test_compare_detects_new_security_issue_introduced():
    result = await compare_snippets(BEFORE, AFTER_WORSE, "db.py")
    sec_rule_ids = [f.rule_id for f in result.security_findings]
    assert "SEC001" in sec_rule_ids


@pytest.mark.asyncio
async def test_compare_complexity_delta_positive_on_added_code():
    simple = "def foo():\n    return 1\n"
    complex_ = (
        "def foo():\n"
        "    if True:\n"
        "        for i in range(10):\n"
        "            if i > 5:\n"
        "                return i\n"
        "    return 0\n"
    )
    result = await compare_snippets(simple, complex_, "foo.py")
    assert result.complexity_delta > 0


@pytest.mark.asyncio
async def test_compare_complexity_delta_negative_on_simplification():
    complex_ = (
        "def foo():\n"
        "    if True:\n"
        "        for i in range(10):\n"
        "            return i\n"
        "    return 0\n"
    )
    simple = "def foo():\n    return 1\n"
    result = await compare_snippets(complex_, simple, "foo.py")
    assert result.complexity_delta < 0


@pytest.mark.asyncio
async def test_compare_default_filename():
    result = await compare_snippets(BEFORE, AFTER_FIXED)
    assert result.filename == "snippet.py"


@pytest.mark.asyncio
async def test_compare_chunks_by_classification_populated():
    result = await compare_snippets(BEFORE, AFTER_FIXED, "db.py")
    assert isinstance(result.chunks_by_classification, dict)
