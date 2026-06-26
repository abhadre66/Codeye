from __future__ import annotations

from reviewmind.engine.models import SemanticChunk
from reviewmind.engine.security.models import SecurityFinding
from reviewmind.engine.security.rules import sec001, sec002, sec003, sec004, sec005

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

RULES: list[tuple[str, object]] = [
    ("SEC001", sec001),
    ("SEC002", sec002),
    ("SEC003", sec003),
    ("SEC004", sec004),
    ("SEC005", sec005),
]


def scan(chunks: list[SemanticChunk]) -> list[SecurityFinding]:
    """Run all security rules over all chunks. Returns findings sorted by severity."""
    findings: list[SecurityFinding] = []
    seen: set[tuple[str, str, int | None]] = set()

    for chunk in chunks:
        for _rule_id, rule_fn in RULES:
            for finding in rule_fn(chunk):  # type: ignore[operator]
                key = (finding.rule_id, finding.file_path, finding.line)
                if key not in seen:
                    seen.add(key)
                    findings.append(finding)

    findings.sort(key=lambda f: _SEVERITY_ORDER.get(f.severity, 99))
    return findings
