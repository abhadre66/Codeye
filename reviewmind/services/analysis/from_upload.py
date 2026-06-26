from __future__ import annotations

from reviewmind.engine.analysis import analyze_code
from reviewmind.engine.models import SemanticChunk


async def analyze_upload(
    files: list[tuple[str, bytes]],
) -> list[SemanticChunk]:
    """Analyze one or more uploaded files.

    files: list of (filename, raw_bytes) — e.g., from a multipart form upload.
    Decodes bytes as UTF-8 (replacing invalid chars) and runs the full pipeline.
    """
    all_chunks: list[SemanticChunk] = []
    for filename, raw in files:
        content = raw.decode("utf-8", errors="replace")
        all_chunks.extend(await analyze_code(filename, content))
    return all_chunks
