"""Phase 3 tests — diff_parser.py"""

from pathlib import Path

import pytest

from reviewmind.engine.diff_parser import parse_diff, synthetic_diff

FIXTURES = Path(__file__).parent / "fixtures" / "diffs"

NEW_FUNCTION_DIFF  = (FIXTURES / "new_function.diff").read_text()
BUG_FIX_DIFF       = (FIXTURES / "bug_fix.diff").read_text()
CONFIG_CHANGE_DIFF = (FIXTURES / "config_change.diff").read_text()


# ── parse_diff tests ──────────────────────────────────────────────────────────

def test_parse_diff_new_file():
    result = parse_diff(NEW_FUNCTION_DIFF)
    assert len(result) == 1
    fd = result[0]
    assert fd.change_type == "modified"
    assert fd.filename == "reviewmind/api/auth.py"
    assert len(fd.hunks) == 1


def test_parse_diff_modified_file():
    result = parse_diff(BUG_FIX_DIFF)
    assert len(result) == 1
    fd = result[0]
    assert fd.change_type == "modified"
    assert len(fd.hunks) >= 1
    # Hunk should have correct new_start
    hunk = fd.hunks[0]
    assert hunk.new_start >= 1


def test_parse_diff_deleted_file():
    raw = (
        "diff --git a/old.py b/old.py\n"
        "deleted file mode 100644\n"
        "--- a/old.py\n"
        "+++ /dev/null\n"
        "@@ -1,3 +0,0 @@\n"
        "-def gone():\n"
        "-    pass\n"
        "-\n"
    )
    result = parse_diff(raw)
    assert len(result) == 1
    assert result[0].change_type == "deleted"


def test_parse_diff_multifile():
    result = parse_diff(NEW_FUNCTION_DIFF + "\n" + BUG_FIX_DIFF)
    assert len(result) == 2
    filenames = {fd.filename for fd in result}
    assert "reviewmind/api/auth.py" in filenames
    assert "reviewmind/services/github/rate_limiter.py" in filenames


def test_parse_diff_line_types():
    result = parse_diff(NEW_FUNCTION_DIFF)
    hunk = result[0].hunks[0]
    types = {line.line_type for line in hunk.lines}
    # new_function.diff has added and context lines
    assert "added" in types
    assert "context" in types


def test_parse_diff_language_detection():
    py_result   = parse_diff(NEW_FUNCTION_DIFF)
    yaml_result = parse_diff(CONFIG_CHANGE_DIFF)
    assert py_result[0].language   == "python"
    assert yaml_result[0].language == "yaml"


def test_parse_diff_empty_string():
    assert parse_diff("") == []
    assert parse_diff("   ") == []


# ── synthetic_diff tests ──────────────────────────────────────────────────────

def test_synthetic_diff_all_added():
    result = synthetic_diff("snippet.py", "def hello():\n    pass\n")
    assert len(result) == 1
    hunk = result[0].hunks[0]
    assert all(l.line_type == "added" for l in hunk.lines)


def test_synthetic_diff_line_numbers():
    code = "line1\nline2\nline3\n"
    result = synthetic_diff("code.py", code)
    hunk = result[0].hunks[0]
    assert len(hunk.lines) == 3
    assert [l.new_lineno for l in hunk.lines] == [1, 2, 3]
