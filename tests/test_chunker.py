"""Phase 3 tests — chunker.py"""

from unittest.mock import AsyncMock

import pytest

from reviewmind.engine.chunker import chunk_file_diffs
from reviewmind.engine.diff_parser import parse_diff, synthetic_diff
from reviewmind.engine.models import FileDiff, Hunk, DiffLine

# ── Helpers ───────────────────────────────────────────────────────────────────

# Post-patch source that matches NEW_FUNCTION_DIFF (validate_token starts at line 5)
PYTHON_SOURCE = """\
from fastapi import HTTPException

oauth2_scheme = None

def validate_token(token: str) -> dict:
    if not token:
        raise ValueError("empty token")
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("invalid jwt format")
    return {"sub": parts[1]}
"""

# Source for the two-hunks merge test (validate_token occupies lines 1-7)
TWO_HUNKS_SOURCE = """\
def validate_token(token: str) -> dict:
    if not token:
        raise ValueError("empty token")
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("invalid jwt format")
    return {"sub": parts[1]}
"""

NEW_FUNCTION_DIFF = """\
diff --git a/auth.py b/auth.py
--- a/auth.py
+++ b/auth.py
@@ -1,3 +1,11 @@
 from fastapi import HTTPException

 oauth2_scheme = None
+
+def validate_token(token: str) -> dict:
+    if not token:
+        raise ValueError("empty token")
+    parts = token.split(".")
+    if len(parts) != 3:
+        raise ValueError("invalid jwt format")
+    return {"sub": parts[1]}
"""

TWO_HUNKS_SAME_FN_DIFF = """\
diff --git a/auth.py b/auth.py
--- a/auth.py
+++ b/auth.py
@@ -1,3 +1,4 @@
 def validate_token(token: str) -> dict:
-    if not token:
+    if token is None or token == "":
+        raise ValueError("missing token")
     parts = token.split(".")
@@ -5,3 +6,3 @@
     if len(parts) != 3:
-        raise ValueError("invalid jwt format")
+        raise ValueError(f"expected 3 parts, got {len(parts)}")
     return {"sub": parts[1]}
"""

YAML_DIFF = """\
diff --git a/config.yaml b/config.yaml
--- a/config.yaml
+++ b/config.yaml
@@ -1,3 +1,4 @@
 app:
-  debug: true
+  debug: false
+  log_level: info
 version: "1.0"
"""


# ── Tests ─────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_chunk_python_new_function():
    fetch = AsyncMock(return_value=PYTHON_SOURCE)
    file_diffs = parse_diff(NEW_FUNCTION_DIFF)
    chunks = await chunk_file_diffs(file_diffs, fetch_content=fetch)

    fn_chunks = [c for c in chunks if c.chunk_type == "function"]
    assert len(fn_chunks) >= 1
    names = {c.symbol_name for c in fn_chunks}
    assert "validate_token" in names


@pytest.mark.asyncio
async def test_chunk_python_merges_hunks_same_function():
    fetch = AsyncMock(return_value=TWO_HUNKS_SOURCE)
    file_diffs = parse_diff(TWO_HUNKS_SAME_FN_DIFF)
    chunks = await chunk_file_diffs(file_diffs, fetch_content=fetch)

    validate_chunks = [c for c in chunks if c.symbol_name == "validate_token"]
    # Two hunks in the same function must merge into ONE chunk
    assert len(validate_chunks) == 1


@pytest.mark.asyncio
async def test_chunk_python_module_level():
    module_diff = """\
diff --git a/config.py b/config.py
--- a/config.py
+++ b/config.py
@@ -1,2 +1,3 @@
 DEBUG = False
+LOG_LEVEL = "info"
 VERSION = "1.0"
"""
    # source has 3 lines after the change is applied
    source = 'DEBUG = False\nLOG_LEVEL = "info"\nVERSION = "1.0"\n'
    fetch = AsyncMock(return_value=source)
    file_diffs = parse_diff(module_diff)
    chunks = await chunk_file_diffs(file_diffs, fetch_content=fetch)

    assert len(chunks) >= 1
    module_chunks = [c for c in chunks if c.chunk_type == "module"]
    assert len(module_chunks) >= 1
    assert module_chunks[0].symbol_name is None


@pytest.mark.asyncio
async def test_chunk_python_syntax_error_falls_back():
    fetch = AsyncMock(return_value="def broken(:\n    pass\n")  # invalid Python
    file_diffs = parse_diff(NEW_FUNCTION_DIFF)
    chunks = await chunk_file_diffs(file_diffs, fetch_content=fetch)

    # Should fall back to raw chunking — one chunk per hunk, chunk_type="raw"
    assert all(c.chunk_type == "raw" for c in chunks)


@pytest.mark.asyncio
async def test_chunk_raw_non_python():
    file_diffs = parse_diff(YAML_DIFF)
    chunks = await chunk_file_diffs(file_diffs, fetch_content=None)

    assert len(chunks) >= 1
    assert all(c.chunk_type == "raw" for c in chunks)
    assert all(c.language == "yaml" for c in chunks)


@pytest.mark.asyncio
async def test_chunk_no_fetch_content():
    """Python file with no fetch_content → falls back to raw chunking."""
    file_diffs = parse_diff(NEW_FUNCTION_DIFF)
    chunks = await chunk_file_diffs(file_diffs, fetch_content=None)

    assert len(chunks) >= 1
    assert all(c.chunk_type == "raw" for c in chunks)


@pytest.mark.asyncio
async def test_chunk_change_type_preserved():
    file_diffs = synthetic_diff("new_module.py", "x = 1\n")
    chunks = await chunk_file_diffs(file_diffs)

    assert len(chunks) == 1
    assert chunks[0].change_type == "added"
