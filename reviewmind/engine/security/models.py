from __future__ import annotations

from dataclasses import dataclass

Severity = str  # "critical" | "high" | "medium" | "low" | "info"


@dataclass
class SecurityFinding:
    rule_id:   str            # e.g. "SEC001"
    severity:  Severity       # "critical" | "high" | "medium" | "low" | "info"
    file_path: str
    line:      int | None     # new-file line number; None when unknown
    message:   str
    snippet:   str            # the offending line text
