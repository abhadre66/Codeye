"""Phase 3 tests — analysis.py (full pipeline integration)"""

from pathlib import Path
from unittest.mock import AsyncMock

import pytest

from reviewmind.engine.analysis import analyze_code, analyze_diff

FIXTURES = Path(__file__).parent / "fixtures" / "diffs"

NEW_FUNCTION_DIFF  = (FIXTURES / "new_function.diff").read_text()
CONFIG_CHANGE_DIFF = (FIXTURES / "config_change.diff").read_text()

PYTHON_SOURCE = """\
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
import jwt
from datetime import datetime, timedelta

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="token")

SECRET_KEY = "change-me-in-production"
ALGORITHM = "HS256"

def require_auth(token: str = Depends(oauth2_scheme)):
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED)
    return token

def validate_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if payload.get("exp") and datetime.utcnow().timestamp() > payload["exp"]:
            raise HTTPException(status_code=401, detail="Token expired")
        return payload
    except jwt.InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
        ) from exc
"""


@pytest.mark.asyncio
async def test_analyze_diff_full_pipeline():
    """Full pipeline: diff string -> enriched SemanticChunks."""
    fetch = AsyncMock(return_value=PYTHON_SOURCE)
    chunks = await analyze_diff(NEW_FUNCTION_DIFF, fetch_content=fetch)

    assert len(chunks) >= 1
    for chunk in chunks:
        assert chunk.classification != ""
        assert chunk.complexity >= 1


@pytest.mark.asyncio
async def test_analyze_code_paste():
    """Pasted Python string -> at least one chunk, all diff lines are 'added'."""
    code = "def hello(name: str) -> str:\n    return f'Hello {name}'\n"
    chunks = await analyze_code("snippet.py", code)

    assert len(chunks) >= 1
    for chunk in chunks:
        assert all(l.line_type == "added" for l in chunk.diff_lines)


@pytest.mark.asyncio
async def test_classify_new_feature():
    """A whole new function (change_type=added) is classified as new_feature."""
    chunks = await analyze_code("auth.py", "def login(user, pwd):\n    return True\n")
    assert len(chunks) >= 1
    assert any(c.classification == "new_feature" for c in chunks)


@pytest.mark.asyncio
async def test_classify_config():
    """A YAML config diff is classified as config."""
    chunks = await analyze_diff(CONFIG_CHANGE_DIFF)
    assert len(chunks) >= 1
    assert all(c.classification == "config" for c in chunks)


@pytest.mark.asyncio
async def test_classify_test_file():
    """Files with 'test' in the path are classified as test."""
    chunks = await analyze_code("tests/test_auth.py", "def test_login():\n    assert True\n")
    assert len(chunks) >= 1
    assert all(c.classification == "test" for c in chunks)


@pytest.mark.asyncio
async def test_classify_dep_file():
    """Dependency manifest files are classified as dep."""
    chunks = await analyze_code("requirements.txt", "fastapi>=0.110\nuvicorn>=0.29\n")
    assert len(chunks) >= 1
    assert all(c.classification == "dep" for c in chunks)


@pytest.mark.asyncio
async def test_classify_refactor():
    """Balanced add/remove ratio is classified as refactor."""
    from reviewmind.engine.classifier import classify
    from reviewmind.engine.models import DiffLine, SemanticChunk

    chunk = SemanticChunk(
        file_path="auth.py",
        start_line=1,
        end_line=5,
        chunk_type="function",
        change_type="modified",
        symbol_name="login",
        diff_lines=[
            DiffLine(line_type="added",   content="    return token", old_lineno=None, new_lineno=2),
            DiffLine(line_type="added",   content="    log(token)",   old_lineno=None, new_lineno=3),
            DiffLine(line_type="removed", content="    return True",  old_lineno=2,    new_lineno=None),
            DiffLine(line_type="removed", content="    log(True)",    old_lineno=3,    new_lineno=None),
        ],
        classification="",
        complexity=1,
        content="",
    )
    assert classify(chunk) == "refactor"


@pytest.mark.asyncio
async def test_classify_unknown():
    """More removals than additions with no special markers -> unknown."""
    from reviewmind.engine.classifier import classify
    from reviewmind.engine.models import DiffLine, SemanticChunk

    chunk = SemanticChunk(
        file_path="auth.py",
        start_line=1,
        end_line=5,
        chunk_type="function",
        change_type="modified",
        symbol_name="login",
        diff_lines=[
            DiffLine(line_type="removed", content="    x = 1", old_lineno=1, new_lineno=None),
            DiffLine(line_type="removed", content="    y = 2", old_lineno=2, new_lineno=None),
            DiffLine(line_type="removed", content="    z = 3", old_lineno=3, new_lineno=None),
        ],
        classification="",
        complexity=1,
        content="",
    )
    assert classify(chunk) == "unknown"
