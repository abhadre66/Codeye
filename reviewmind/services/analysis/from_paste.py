from __future__ import annotations

from reviewmind.engine.analysis import analyze_code
from reviewmind.engine.models import SemanticChunk


async def analyze_paste(
    code: str,
    filename: str = "snippet.py",
) -> list[SemanticChunk]:
    """Analyze code pasted directly into the chat UI.

    filename: hint for language detection (default: snippet.py).
    """
    return await analyze_code(filename, code)
