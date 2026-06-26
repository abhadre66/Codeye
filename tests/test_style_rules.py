"""Phase 5 tests — style rules STY001-STY006 (positive / negative / edge case)"""

import pytest

from reviewmind.engine.models import DiffLine, SemanticChunk
from reviewmind.engine.style.engine import scan
from reviewmind.engine.style.models import StyleConfig
from reviewmind.engine.style.rules import sty001, sty002, sty003, sty004, sty005, sty006


# ── Helpers ───────────────────────────────────────────────────────────────────

DEFAULT = StyleConfig()


def _chunk(
    file_path: str,
    added_lines: list[str],
    change_type: str = "modified",
    chunk_type: str = "function",
    symbol_name: str = "fn",
    start_line: int = 1,
    end_line: int | None = None,
) -> SemanticChunk:
    diff_lines = [
        DiffLine(line_type="added", content=line, old_lineno=None, new_lineno=i + start_line)
        for i, line in enumerate(added_lines)
    ]
    return SemanticChunk(
        file_path=file_path,
        start_line=start_line,
        end_line=end_line if end_line is not None else start_line + len(added_lines) - 1,
        chunk_type=chunk_type,
        change_type=change_type,
        symbol_name=symbol_name,
        diff_lines=diff_lines,
        classification="new_feature",
        complexity=1,
        content="\n".join(added_lines),
    )


# ── STY005 — Max Line Length ──────────────────────────────────────────────────

def test_sty005_positive():
    """Line exceeding max_line_length is flagged."""
    long_line = "x = " + "a" * 120  # 124 chars
    chunk = _chunk("utils.py", [long_line])
    findings = sty005(chunk, DEFAULT)
    assert len(findings) == 1
    assert findings[0].rule_id == "STY005"
    assert findings[0].severity == "info"


def test_sty005_negative():
    """Line within limit is not flagged."""
    chunk = _chunk("utils.py", ["x = 1"])
    assert sty005(chunk, DEFAULT) == []


def test_sty005_disabled():
    """Rule is skipped when not in enabled_rules."""
    long_line = "x = " + "a" * 120
    chunk = _chunk("utils.py", [long_line])
    cfg = StyleConfig(enabled_rules=set())
    assert sty005(chunk, cfg) == []


# ── STY006 — TODO without ticket ─────────────────────────────────────────────

def test_sty006_positive():
    """TODO without ticket reference is flagged."""
    chunk = _chunk("app.py", ["# TODO: fix this later"])
    findings = sty006(chunk, DEFAULT)
    assert len(findings) == 1
    assert findings[0].rule_id == "STY006"


def test_sty006_negative():
    """TODO with ticket reference is not flagged."""
    chunk = _chunk("app.py", ["# TODO: fix this #123"])
    assert sty006(chunk, DEFAULT) == []


def test_sty006_jira_ticket():
    """FIXME with JIRA reference is not flagged."""
    chunk = _chunk("app.py", ["# FIXME: remove this JIRA-456"])
    assert sty006(chunk, DEFAULT) == []


# ── STY004 — Forbidden Import ─────────────────────────────────────────────────

def test_sty004_positive():
    """Wildcard import is flagged."""
    chunk = _chunk("app.py", ["from os.path import *"])
    findings = sty004(chunk, DEFAULT)
    assert len(findings) == 1
    assert findings[0].rule_id == "STY004"
    assert findings[0].severity == "medium"


def test_sty004_negative():
    """Normal import is not flagged."""
    chunk = _chunk("app.py", ["import os"])
    assert sty004(chunk, DEFAULT) == []


def test_sty004_specific_import():
    """Specific named import is not flagged."""
    chunk = _chunk("app.py", ["from os.path import join, exists"])
    assert sty004(chunk, DEFAULT) == []


# ── STY001 — Max Function Length ──────────────────────────────────────────────

def test_sty001_positive():
    """Function exceeding max length is flagged."""
    chunk = _chunk(
        "app.py", ["pass"],
        chunk_type="function", symbol_name="big_fn",
        start_line=1, end_line=60,
    )
    findings = sty001(chunk, DEFAULT)
    assert len(findings) == 1
    assert findings[0].rule_id == "STY001"


def test_sty001_negative():
    """Short function is not flagged."""
    chunk = _chunk(
        "app.py", ["pass"],
        chunk_type="function", symbol_name="fn",
        start_line=1, end_line=10,
    )
    assert sty001(chunk, DEFAULT) == []


def test_sty001_non_function():
    """Module-level chunk is not checked for length."""
    chunk = _chunk(
        "app.py", ["pass"],
        chunk_type="module",
        start_line=1, end_line=60,
    )
    assert sty001(chunk, DEFAULT) == []


# ── STY002 — Missing Docstring ────────────────────────────────────────────────

def test_sty002_positive():
    """Newly added function with no docstring is flagged."""
    chunk = _chunk(
        "app.py",
        ["def process(data):", "    return data"],
        change_type="added", chunk_type="function", symbol_name="process",
    )
    findings = sty002(chunk, DEFAULT)
    assert len(findings) == 1
    assert findings[0].rule_id == "STY002"


def test_sty002_negative():
    """Function with docstring is not flagged."""
    chunk = _chunk(
        "app.py",
        ['def process(data):', '    """Process the data."""', "    return data"],
        change_type="added", chunk_type="function", symbol_name="process",
    )
    assert sty002(chunk, DEFAULT) == []


def test_sty002_test_file_skipped():
    """Newly added function in test file is not flagged."""
    chunk = _chunk(
        "tests/test_app.py",
        ["def test_process():", "    pass"],
        change_type="added", chunk_type="function", symbol_name="test_process",
    )
    assert sty002(chunk, DEFAULT) == []


# ── STY003 — Naming Convention ────────────────────────────────────────────────

def test_sty003_function_positive():
    """PascalCase function name is flagged."""
    chunk = _chunk("app.py", ["def ProcessData(x):"])
    findings = sty003(chunk, DEFAULT)
    assert len(findings) == 1
    assert findings[0].rule_id == "STY003"
    assert "snake_case" in findings[0].message


def test_sty003_function_negative():
    """snake_case function name is not flagged."""
    chunk = _chunk("app.py", ["def process_data(x):"])
    assert sty003(chunk, DEFAULT) == []


def test_sty003_dunder_skipped():
    """Dunder methods are not flagged."""
    chunk = _chunk("app.py", ["def __init__(self):"])
    assert sty003(chunk, DEFAULT) == []


# ── scan() — engine aggregator ────────────────────────────────────────────────

def test_scan_aggregates_multiple_rules():
    """scan() collects findings from multiple rules across chunks."""
    chunks = [
        _chunk("app.py", ["from os import *"]),           # STY004
        _chunk("app.py", ["# TODO fix this"]),            # STY006
    ]
    findings = scan(chunks)
    rule_ids = {f.rule_id for f in findings}
    assert "STY004" in rule_ids
    assert "STY006" in rule_ids


def test_scan_deduplicates():
    """scan() does not emit duplicate findings for the same rule+file+line."""
    chunk = _chunk("app.py", ["from os import *"])
    findings = scan([chunk, chunk])
    sty004_findings = [f for f in findings if f.rule_id == "STY004"]
    assert len(sty004_findings) == 1


def test_scan_respects_enabled_rules():
    """scan() skips rules not in config.enabled_rules."""
    chunk = _chunk("app.py", ["from os import *"])
    cfg = StyleConfig(enabled_rules={"STY005"})  # STY004 disabled
    findings = scan([chunk], config=cfg)
    assert all(f.rule_id != "STY004" for f in findings)
