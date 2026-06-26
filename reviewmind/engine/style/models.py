from __future__ import annotations

from dataclasses import dataclass, field

import yaml

Severity = str  # "critical" | "high" | "medium" | "low" | "info"


@dataclass
class StyleFinding:
    rule_id:   str
    severity:  Severity
    file_path: str
    line:      int | None
    message:   str
    snippet:   str


@dataclass
class StyleConfig:
    max_function_length: int       = 50
    max_line_length:     int       = 120
    forbidden_imports:   list[str] = field(default_factory=lambda: [r"from .* import \*"])
    require_docstrings:  bool      = True
    check_naming:        bool      = True
    enabled_rules:       set[str]  = field(
        default_factory=lambda: {"STY001", "STY002", "STY003", "STY004", "STY005", "STY006"}
    )


def load_config(yaml_str: str) -> StyleConfig:
    """Parse a reviewmind.yaml string and return a StyleConfig."""
    data = yaml.safe_load(yaml_str) or {}
    style = data.get("style", {})
    enabled = style.get("enabled_rules")
    return StyleConfig(
        max_function_length=style.get("max_function_length", 50),
        max_line_length=style.get("max_line_length", 120),
        forbidden_imports=style.get("forbidden_imports", [r"from .* import \*"]),
        require_docstrings=style.get("require_docstrings", True),
        check_naming=style.get("check_naming", True),
        enabled_rules=set(enabled) if enabled is not None else {"STY001", "STY002", "STY003", "STY004", "STY005", "STY006"},
    )
