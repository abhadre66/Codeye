from __future__ import annotations

from pathlib import Path

from reviewmind.engine.models import Classification, SemanticChunk

_CONFIG_EXTS  = {".yaml", ".yml", ".toml", ".json", ".env", ".cfg", ".ini", ".xml"}
_DEP_NAMES    = ("requirements", "pyproject", "package.json", "go.mod", "gemfile",
                 "cargo.toml", "pom.xml", "build.gradle")


def classify(chunk: SemanticChunk) -> Classification:
    """Assign a semantic classification to a SemanticChunk. Pure — no I/O."""
    path = chunk.file_path.lower()
    ext  = Path(path).suffix.lower()

    # Test files
    if "test" in path or "spec" in path:
        return "test"

    # Dependency manifest files
    if any(d in path for d in _DEP_NAMES):
        return "dep"

    # Config / data files
    if ext in _CONFIG_EXTS:
        return "config"

    added_count   = sum(1 for l in chunk.diff_lines if l.line_type == "added")
    removed_count = sum(1 for l in chunk.diff_lines if l.line_type == "removed")

    # Whole new function or class introduced
    if chunk.change_type == "added" and chunk.chunk_type in ("function", "class"):
        return "new_feature"

    # Only additions — definitely new code
    if added_count > 0 and removed_count == 0:
        return "new_feature"

    # Mostly replacements — likely a refactor
    if added_count > 0 and removed_count >= added_count * 0.8:
        return "refactor"

    # Mixed modifications with more additions than removals — treat as new feature
    if added_count > removed_count:
        return "new_feature"

    return "unknown"
