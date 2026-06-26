from __future__ import annotations

import re

from reviewmind.engine.models import SemanticChunk
from reviewmind.engine.style.models import StyleConfig, StyleFinding

# ── Helpers ───────────────────────────────────────────────────────────────────

def _added_lines(chunk: SemanticChunk) -> list[tuple[int | None, str]]:
    return [
        (dl.new_lineno, dl.content)
        for dl in chunk.diff_lines
        if dl.line_type == "added"
    ]


def _is_test_file(path: str) -> bool:
    p = path.lower()
    return any(k in p for k in ("test", "spec", "example", "sample", "fixture"))


# ── STY005 — Max Line Length ──────────────────────────────────────────────────

def sty005(chunk: SemanticChunk, config: StyleConfig) -> list[StyleFinding]:
    """Flag added lines exceeding max_line_length."""
    if "STY005" not in config.enabled_rules:
        return []
    findings: list[StyleFinding] = []
    for lineno, text in _added_lines(chunk):
        if len(text.rstrip("\n")) > config.max_line_length:
            findings.append(StyleFinding(
                rule_id="STY005",
                severity="info",
                file_path=chunk.file_path,
                line=lineno,
                message=f"Line length {len(text.rstrip())} exceeds max {config.max_line_length}",
                snippet=text.strip()[:80],
            ))
    return findings


# ── STY006 — TODO without ticket ──────────────────────────────────────────────

_TODO_RE    = re.compile(r"(TODO|FIXME)", re.IGNORECASE)
_TICKET_RE  = re.compile(r"#\d+|[A-Z]+-\d+")


def sty006(chunk: SemanticChunk, config: StyleConfig) -> list[StyleFinding]:
    """Flag TODO/FIXME comments not linked to a ticket reference."""
    if "STY006" not in config.enabled_rules:
        return []
    findings: list[StyleFinding] = []
    for lineno, text in _added_lines(chunk):
        if _TODO_RE.search(text) and not _TICKET_RE.search(text):
            findings.append(StyleFinding(
                rule_id="STY006",
                severity="info",
                file_path=chunk.file_path,
                line=lineno,
                message="TODO/FIXME comment has no ticket reference (e.g. #123 or JIRA-456)",
                snippet=text.strip(),
            ))
    return findings


# ── STY004 — Forbidden Import ─────────────────────────────────────────────────

_IMPORT_RE = re.compile(r"^\s*(import |from .+ import )")


def sty004(chunk: SemanticChunk, config: StyleConfig) -> list[StyleFinding]:
    """Flag import lines matching patterns in config.forbidden_imports."""
    if "STY004" not in config.enabled_rules:
        return []
    patterns = [re.compile(p) for p in config.forbidden_imports]
    findings: list[StyleFinding] = []
    for lineno, text in _added_lines(chunk):
        if not _IMPORT_RE.match(text):
            continue
        for pat in patterns:
            if pat.search(text):
                findings.append(StyleFinding(
                    rule_id="STY004",
                    severity="medium",
                    file_path=chunk.file_path,
                    line=lineno,
                    message=f"Forbidden import pattern: {pat.pattern}",
                    snippet=text.strip(),
                ))
                break
    return findings


# ── STY001 — Max Function Length ──────────────────────────────────────────────

def sty001(chunk: SemanticChunk, config: StyleConfig) -> list[StyleFinding]:
    """Flag functions exceeding max_function_length lines."""
    if "STY001" not in config.enabled_rules:
        return []
    if chunk.chunk_type != "function":
        return []
    length = chunk.end_line - chunk.start_line + 1
    if length <= config.max_function_length:
        return []
    name = chunk.symbol_name or "<unknown>"
    return [StyleFinding(
        rule_id="STY001",
        severity="info",
        file_path=chunk.file_path,
        line=chunk.start_line,
        message=f"Function '{name}' is {length} lines (max {config.max_function_length})",
        snippet=f"def {name}(...)",
    )]


# ── STY002 — Missing Docstring ────────────────────────────────────────────────

_DOCSTRING_RE = re.compile(r'"""|\'\'\' ')


def sty002(chunk: SemanticChunk, config: StyleConfig) -> list[StyleFinding]:
    """Flag newly added functions/classes with no docstring."""
    if "STY002" not in config.enabled_rules:
        return []
    if not config.require_docstrings:
        return []
    if chunk.change_type != "added":
        return []
    if chunk.chunk_type not in ("function", "class"):
        return []
    if _is_test_file(chunk.file_path):
        return []

    first_lines = "\n".join(chunk.content.splitlines()[:5])
    if '"""' in first_lines or "'''" in first_lines:
        return []

    name = chunk.symbol_name or "<unknown>"
    kind = "Function" if chunk.chunk_type == "function" else "Class"
    return [StyleFinding(
        rule_id="STY002",
        severity="info",
        file_path=chunk.file_path,
        line=chunk.start_line,
        message=f"{kind} '{name}' is missing a docstring",
        snippet=f"def {name}(...)" if chunk.chunk_type == "function" else f"class {name}:",
    )]


# ── STY003 — Naming Convention ────────────────────────────────────────────────

_FUNC_DEF_RE   = re.compile(r"^\s*(?:async\s+)?def\s+([A-Za-z_][A-Za-z0-9_]*)\s*\(")
_CLASS_DEF_RE  = re.compile(r"^\s*class\s+([A-Za-z_][A-Za-z0-9_]*)\s*[:(]")
_SNAKE_CASE_RE = re.compile(r"^[a-z_][a-z0-9_]*$")
_PASCAL_CASE_RE = re.compile(r"^[A-Z][a-zA-Z0-9]*$")
_DUNDER_RE     = re.compile(r"^__[a-z]+__$")


def sty003(chunk: SemanticChunk, config: StyleConfig) -> list[StyleFinding]:
    """Flag functions not in snake_case and classes not in PascalCase."""
    if "STY003" not in config.enabled_rules:
        return []
    if not config.check_naming:
        return []
    findings: list[StyleFinding] = []
    for lineno, text in _added_lines(chunk):
        m = _FUNC_DEF_RE.match(text)
        if m:
            name = m.group(1)
            if not _DUNDER_RE.match(name) and not _SNAKE_CASE_RE.match(name):
                findings.append(StyleFinding(
                    rule_id="STY003",
                    severity="low",
                    file_path=chunk.file_path,
                    line=lineno,
                    message=f"Function '{name}' should be snake_case",
                    snippet=text.strip(),
                ))
            continue
        m = _CLASS_DEF_RE.match(text)
        if m:
            name = m.group(1)
            if not _PASCAL_CASE_RE.match(name):
                findings.append(StyleFinding(
                    rule_id="STY003",
                    severity="low",
                    file_path=chunk.file_path,
                    line=lineno,
                    message=f"Class '{name}' should be PascalCase",
                    snippet=text.strip(),
                ))
    return findings
