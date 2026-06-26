from __future__ import annotations

import json
import re
from pathlib import Path

from reviewmind.engine.models import SemanticChunk
from reviewmind.engine.security.models import SecurityFinding

# ── Helpers ───────────────────────────────────────────────────────────────────

def _added_lines(chunk: SemanticChunk) -> list[tuple[int | None, str]]:
    """Return (lineno, text) for every added line in the chunk."""
    return [
        (dl.new_lineno, dl.content)
        for dl in chunk.diff_lines
        if dl.line_type == "added"
    ]


def _is_test_file(path: str) -> bool:
    p = path.lower()
    return any(k in p for k in ("test", "spec", "example", "sample", "fixture"))


# ── SEC001 — Hardcoded Secret ─────────────────────────────────────────────────

_SECRET_PATTERNS = re.compile(
    r'(api_key|secret|password|passwd|token|private_key|access_key|auth_key)'
    r'\s*=\s*["\'][^"\']{6,}["\']'
    r'|BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY'
    r'|AKIA[0-9A-Z]{16}'           # AWS access key id
    r'|[A-Za-z0-9+/]{40}',         # generic 40-char base64 secret
    re.IGNORECASE,
)

# Patterns that are clearly safe (env-var references, placeholder values)
_SECRET_ALLOWLIST = re.compile(
    r'os\.environ|os\.getenv|getenv|settings\.|config\.|'
    r'your[_-]?(key|token|secret)|<[^>]+>|\$\{[^}]+\}|'
    r'(fake|dummy|example|placeholder|changeme|replace|todo)',
    re.IGNORECASE,
)


def sec001(chunk: SemanticChunk) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    severity = "low" if _is_test_file(chunk.file_path) else "high"
    for lineno, text in _added_lines(chunk):
        if _SECRET_PATTERNS.search(text) and not _SECRET_ALLOWLIST.search(text):
            findings.append(SecurityFinding(
                rule_id="SEC001",
                severity=severity,
                file_path=chunk.file_path,
                line=lineno,
                message="Possible hardcoded secret detected",
                snippet=text.strip(),
            ))
    return findings


# ── SEC002 — SQL Injection ────────────────────────────────────────────────────

# Matches execute/raw/filter calls that build the query via f-string, .format(), or %
_SQL_CALL = re.compile(r'\.(execute|raw|filter)\s*\(')
_SQL_INTERP = re.compile(
    r'f["\'].*\{.*\}.*["\']'       # f-string
    r'|["\'].*["\']\.format\s*\('  # .format()
    r'|%\s*\(',                     # % interpolation
)
# Safe: literal %s / ? placeholders (parameterized)
_SQL_SAFE = re.compile(r'%s|%d|\?')


def sec002(chunk: SemanticChunk) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    for lineno, text in _added_lines(chunk):
        if _SQL_CALL.search(text) and _SQL_INTERP.search(text) and not _SQL_SAFE.search(text):
            findings.append(SecurityFinding(
                rule_id="SEC002",
                severity="critical",
                file_path=chunk.file_path,
                line=lineno,
                message="Possible SQL injection: string interpolation in DB call",
                snippet=text.strip(),
            ))
    return findings


# ── SEC003 — Insecure Dependency ──────────────────────────────────────────────

_VULN_SNAPSHOT_PATH = Path(__file__).parent / "vuln_snapshot.json"
_DEP_FILE_NAMES = ("requirements.txt", "pyproject.toml", "package.json",
                   "go.mod", "gemfile", "cargo.toml")

# Lazy-loaded so tests can patch the path
_vuln_db: dict[str, str] | None = None


def _load_vuln_db() -> dict[str, str]:
    global _vuln_db
    if _vuln_db is None:
        _vuln_db = json.loads(_VULN_SNAPSHOT_PATH.read_text())
    return _vuln_db


# Parses "package==1.2.3", "package>=1.0", "package" lines
_DEP_LINE = re.compile(r'^([A-Za-z0-9_\-\.]+)\s*[=><!]?', re.MULTILINE)


def sec003(chunk: SemanticChunk) -> list[SecurityFinding]:
    if not any(name in chunk.file_path.lower() for name in _DEP_FILE_NAMES):
        return []
    vuln_db = _load_vuln_db()
    findings: list[SecurityFinding] = []
    for lineno, text in _added_lines(chunk):
        m = _DEP_LINE.match(text.strip())
        if m:
            pkg = m.group(1).lower().replace("-", "_").replace(".", "_")
            if pkg in vuln_db:
                findings.append(SecurityFinding(
                    rule_id="SEC003",
                    severity="medium",
                    file_path=chunk.file_path,
                    line=lineno,
                    message=f"Known vulnerable package: {m.group(1)} — {vuln_db[pkg]}",
                    snippet=text.strip(),
                ))
    return findings


# ── SEC004 — Missing Input Validation ────────────────────────────────────────

# Dangerous sinks
_DANGEROUS_SINKS = re.compile(
    r'open\s*\('
    r'|subprocess\.'
    r'|os\.system\s*\('
    r'|\.execute\s*\('
    r'|eval\s*\('
)
# FastAPI / route param sources
_ROUTE_PARAMS = re.compile(
    r'=\s*(Path|Query|Header|Cookie|Body|Form)\s*\('
    r'|request\.(query_params|path_params|form|json|body)'
    r'|\brequest\b'
)
# Guard keywords that indicate the param is checked before use
_GUARD = re.compile(r'\bif\b|\bassert\b|validate|sanitize|escape|clean')


def sec004(chunk: SemanticChunk) -> list[SecurityFinding]:
    added = [text for _, text in _added_lines(chunk)]
    combined = "\n".join(added)

    # Only flag if the chunk uses route params AND dangerous sinks AND no guard
    if not (_ROUTE_PARAMS.search(combined) and _DANGEROUS_SINKS.search(combined)):
        return []
    if _GUARD.search(combined):
        return []

    # Find the specific sink line to report
    findings: list[SecurityFinding] = []
    for lineno, text in _added_lines(chunk):
        if _DANGEROUS_SINKS.search(text):
            findings.append(SecurityFinding(
                rule_id="SEC004",
                severity="low",
                file_path=chunk.file_path,
                line=lineno,
                message="Route parameter used in dangerous sink without input validation",
                snippet=text.strip(),
            ))
    return findings


# ── SEC005 — Unsafe Deserialization ──────────────────────────────────────────

# Dangerous patterns
_UNSAFE_DESER = re.compile(
    r'pickle\.load'
    r'|pickle\.loads'
    r'|yaml\.load\s*\('         # yaml.load without SafeLoader
    r'|\beval\s*\('
    r'|\bexec\s*\('
    r'|shell\s*=\s*True'
)
# Safe exceptions
_SAFE_DESER = re.compile(
    r'yaml\.safe_load'
    r'|SafeLoader'
    r'|yaml\.load\s*\([^)]*SafeLoader'
)


def sec005(chunk: SemanticChunk) -> list[SecurityFinding]:
    findings: list[SecurityFinding] = []
    for lineno, text in _added_lines(chunk):
        if _UNSAFE_DESER.search(text) and not _SAFE_DESER.search(text):
            findings.append(SecurityFinding(
                rule_id="SEC005",
                severity="high",
                file_path=chunk.file_path,
                line=lineno,
                message="Unsafe deserialization or code execution pattern detected",
                snippet=text.strip(),
            ))
    return findings
