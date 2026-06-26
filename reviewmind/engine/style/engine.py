from __future__ import annotations

from reviewmind.engine.models import SemanticChunk
from reviewmind.engine.style.models import StyleConfig, StyleFinding
from reviewmind.engine.style.rules import sty001, sty002, sty003, sty004, sty005, sty006

_SEVERITY_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}

DEFAULT_CONFIG = StyleConfig()

RULES: list[tuple[str, object]] = [
    ("STY001", sty001),
    ("STY002", sty002),
    ("STY003", sty003),
    ("STY004", sty004),
    ("STY005", sty005),
    ("STY006", sty006),
]


def scan(chunks: list[SemanticChunk], config: StyleConfig | None = None) -> list[StyleFinding]:
    """Run all enabled style rules over all chunks. Returns findings sorted by severity."""
    cfg = config or DEFAULT_CONFIG
    findings: list[StyleFinding] = []
    seen: set[tuple[str, str, int | None]] = set()

    for chunk in chunks:
        for _rule_id, rule_fn in RULES:
            for finding in rule_fn(chunk, cfg):  # type: ignore[operator]
                key = (finding.rule_id, finding.file_path, finding.line)
                if key not in seen:
                    seen.add(key)
                    findings.append(finding)

    findings.sort(key=lambda f: _SEVERITY_ORDER.get(f.severity, 99))
    return findings
