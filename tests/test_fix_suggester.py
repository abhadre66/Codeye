"""
Tests for FixSuggester service — concrete fix suggestions per finding.
"""

import pytest

from reviewmind.services.fix_suggester import FixReport, FixSuggestion, suggest_fixes


HARDCODED_SECRET = 'api_key = "sk-prod-abc123secretvalue"\n'

SQL_INJECTION = (
    'def get_user(uid):\n'
    '    db.execute(f"SELECT * FROM users WHERE id = {uid}")\n'
)

WILDCARD_IMPORT = "from os import *\n\ndef do_stuff():\n    pass\n"

MISSING_DOCSTRING = "def my_function():\n    return 42\n"

TODO_NO_TICKET = "# TODO: fix this later\ndef foo():\n    pass\n"

LONG_LINE = "x = " + "a" * 130 + "\n"

CLEAN_CODE = "def greet(name: str) -> str:\n    \"\"\"Return a greeting.\"\"\"\n    return f'Hello, {name}'\n"


@pytest.mark.asyncio
async def test_suggest_fixes_returns_report():
    report = await suggest_fixes(HARDCODED_SECRET, "config.py")
    assert isinstance(report, FixReport)
    assert report.filename == "config.py"
    assert isinstance(report.suggestions, list)
    assert report.total_issues == len(report.suggestions)


@pytest.mark.asyncio
async def test_suggest_fixes_sec001_has_env_var_example():
    report = await suggest_fixes(HARDCODED_SECRET, "config.py")
    sec001 = next((s for s in report.suggestions if s.rule_id == "SEC001"), None)
    assert sec001 is not None
    assert "os.environ" in sec001.fix_example
    assert sec001.fix_description != ""


@pytest.mark.asyncio
async def test_suggest_fixes_sec002_has_parameterized_example():
    report = await suggest_fixes(SQL_INJECTION, "db.py")
    sec002 = next((s for s in report.suggestions if s.rule_id == "SEC002"), None)
    assert sec002 is not None
    assert "%s" in sec002.fix_example or "parameterized" in sec002.fix_description.lower()


@pytest.mark.asyncio
async def test_suggest_fixes_sty004_has_explicit_import_example():
    report = await suggest_fixes(WILDCARD_IMPORT, "utils.py")
    sty004 = next((s for s in report.suggestions if s.rule_id == "STY004"), None)
    assert sty004 is not None
    assert "import *" in sty004.fix_example or "wildcard" in sty004.fix_description.lower()


@pytest.mark.asyncio
async def test_suggest_fixes_sty002_has_docstring_example():
    report = await suggest_fixes(MISSING_DOCSTRING, "utils.py")
    sty002 = next((s for s in report.suggestions if s.rule_id == "STY002"), None)
    assert sty002 is not None
    assert '"""' in sty002.fix_example


@pytest.mark.asyncio
async def test_suggest_fixes_sty006_has_ticket_example():
    report = await suggest_fixes(TODO_NO_TICKET, "utils.py")
    sty006 = next((s for s in report.suggestions if s.rule_id == "STY006"), None)
    assert sty006 is not None
    assert "PROJ-" in sty006.fix_example or "#" in sty006.fix_example


@pytest.mark.asyncio
async def test_suggest_fixes_clean_code_returns_no_suggestions():
    report = await suggest_fixes(CLEAN_CODE, "clean.py")
    assert report.total_issues == 0
    assert report.suggestions == []


@pytest.mark.asyncio
async def test_suggest_fixes_sorted_by_severity():
    # Combine secret (high) + TODO (info)
    code = HARDCODED_SECRET + "\n" + TODO_NO_TICKET
    report = await suggest_fixes(code, "mixed.py")
    severities = [s.severity for s in report.suggestions]
    order = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    assert severities == sorted(severities, key=lambda s: order.get(s, 5))


@pytest.mark.asyncio
async def test_suggest_fixes_fixable_count_accurate():
    report = await suggest_fixes(HARDCODED_SECRET, "config.py")
    fixable = sum(1 for s in report.suggestions if s.fix_example)
    assert report.fixable_count == fixable


@pytest.mark.asyncio
async def test_suggest_fixes_default_filename():
    report = await suggest_fixes(HARDCODED_SECRET)
    assert report.filename == "snippet.py"


@pytest.mark.asyncio
async def test_fix_suggestion_has_required_fields():
    report = await suggest_fixes(HARDCODED_SECRET, "config.py")
    for s in report.suggestions:
        assert isinstance(s, FixSuggestion)
        assert s.rule_id
        assert s.severity
        assert s.problem
        assert s.fix_description
