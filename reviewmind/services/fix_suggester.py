"""
Fix Suggester Service — turns analysis findings into actionable code fixes.

For each security or style finding, produces a concrete suggestion showing
what the fixed code should look like. Makes analyze_paste/analyze_upload
output immediately actionable rather than just diagnostic.
"""

from __future__ import annotations

import re
from dataclasses import dataclass

from reviewmind.core.logging import get_logger
from reviewmind.engine.security.models import SecurityFinding
from reviewmind.engine.style.models import StyleFinding
from reviewmind.services.code_analysis import CodeAnalysisResult, analyze_paste

logger = get_logger(__name__)


@dataclass
class FixSuggestion:
    rule_id: str
    severity: str
    file_path: str
    line: int | None
    problem: str          # original message from the finding
    fix_description: str  # what to do
    fix_example: str      # concrete code showing the fix pattern


@dataclass
class FixReport:
    filename: str
    analysis: CodeAnalysisResult
    suggestions: list[FixSuggestion]
    total_issues: int
    fixable_count: int    # how many have a concrete example


async def suggest_fixes(
    code: str,
    filename: str = "snippet.py",
) -> FixReport:
    """
    Analyze pasted code and return fix suggestions for every finding.

    Runs the same pipeline as analyze_paste, then enriches each finding
    with a description of the fix and a concrete code example.
    """
    result = await analyze_paste(code, filename)

    suggestions: list[FixSuggestion] = []

    for finding in result.security_findings:
        suggestion = _fix_for_security(finding, code)
        suggestions.append(suggestion)

    for finding in result.style_findings:
        suggestion = _fix_for_style(finding, code)
        suggestions.append(suggestion)

    # Sort: critical first, then by line number
    _SORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "info": 4}
    suggestions.sort(key=lambda s: (_SORDER.get(s.severity, 5), s.line or 0))

    fixable = sum(1 for s in suggestions if s.fix_example)

    logger.info(
        "fix_suggestions_generated",
        filename=filename,
        total=len(suggestions),
        fixable=fixable,
    )
    return FixReport(
        filename=filename,
        analysis=result,
        suggestions=suggestions,
        total_issues=len(suggestions),
        fixable_count=fixable,
    )


# ── Security fix templates ────────────────────────────────────────────────────

def _fix_for_security(finding: SecurityFinding, code: str) -> FixSuggestion:
    rule = finding.rule_id
    snippet = finding.snippet.strip()

    if rule == "SEC001":
        var_name = _extract_var_name(snippet) or "SECRET"
        env_name = var_name.upper()
        return FixSuggestion(
            rule_id=rule,
            severity=finding.severity,
            file_path=finding.file_path,
            line=finding.line,
            problem=finding.message,
            fix_description=(
                "Move the secret to an environment variable. "
                "Never commit credentials to version control."
            ),
            fix_example=(
                f"import os\n"
                f'{var_name} = os.environ.get("{env_name}")\n'
                f'if not {var_name}:\n'
                f'    raise RuntimeError("{env_name} environment variable is not set")'
            ),
        )

    if rule == "SEC002":
        return FixSuggestion(
            rule_id=rule,
            severity=finding.severity,
            file_path=finding.file_path,
            line=finding.line,
            problem=finding.message,
            fix_description=(
                "Use parameterized queries instead of string interpolation. "
                "Pass values as a separate tuple, never inline them into the SQL string."
            ),
            fix_example=(
                "# Instead of:\n"
                '#   cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")\n'
                "\n"
                "# Use:\n"
                'cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))\n'
                "\n"
                "# Or with SQLAlchemy:\n"
                "session.execute(select(User).where(User.id == user_id))"
            ),
        )

    if rule == "SEC003":
        pkg = _extract_package_name(snippet) or "the dependency"
        return FixSuggestion(
            rule_id=rule,
            severity=finding.severity,
            file_path=finding.file_path,
            line=finding.line,
            problem=finding.message,
            fix_description=(
                f"Upgrade {pkg} to a patched version. "
                "Check the OSV advisory for the minimum safe version."
            ),
            fix_example=(
                f"# Check the latest safe version:\n"
                f"#   pip index versions {pkg}\n"
                f"#   or visit https://osv.dev\n"
                f"\n"
                f"# Then pin to the patched version in your requirements:\n"
                f"{pkg}>=<patched_version>"
            ),
        )

    if rule == "SEC004":
        return FixSuggestion(
            rule_id=rule,
            severity=finding.severity,
            file_path=finding.file_path,
            line=finding.line,
            problem=finding.message,
            fix_description=(
                "Validate and sanitize user input before passing it to "
                "file operations, subprocesses, or database calls."
            ),
            fix_example=(
                "import os\n"
                "from pathlib import Path\n"
                "\n"
                "def safe_read(user_path: str) -> str:\n"
                "    # Resolve and confine to allowed directory\n"
                "    base = Path('/safe/base/dir').resolve()\n"
                "    target = (base / user_path).resolve()\n"
                "    if not str(target).startswith(str(base)):\n"
                "        raise ValueError('Path traversal attempt detected')\n"
                "    return target.read_text()"
            ),
        )

    if rule == "SEC005":
        if "pickle" in snippet:
            return FixSuggestion(
                rule_id=rule,
                severity=finding.severity,
                file_path=finding.file_path,
                line=finding.line,
                problem=finding.message,
                fix_description=(
                    "Avoid pickle for untrusted data — it can execute arbitrary code. "
                    "Use JSON, msgpack, or a schema-validated format instead."
                ),
                fix_example=(
                    "import json\n"
                    "\n"
                    "# Instead of:\n"
                    "#   data = pickle.loads(raw)\n"
                    "\n"
                    "# Use:\n"
                    "data = json.loads(raw)  # safe, no code execution"
                ),
            )
        return FixSuggestion(
            rule_id=rule,
            severity=finding.severity,
            file_path=finding.file_path,
            line=finding.line,
            problem=finding.message,
            fix_description=(
                "Use yaml.safe_load instead of yaml.load — "
                "safe_load disables Python object deserialization."
            ),
            fix_example=(
                "import yaml\n"
                "\n"
                "# Instead of:\n"
                "#   data = yaml.load(stream)\n"
                "\n"
                "# Use:\n"
                "data = yaml.safe_load(stream)"
            ),
        )

    # Generic security fallback
    return FixSuggestion(
        rule_id=rule,
        severity=finding.severity,
        file_path=finding.file_path,
        line=finding.line,
        problem=finding.message,
        fix_description="Review and remediate the flagged code.",
        fix_example="",
    )


# ── Style fix templates ───────────────────────────────────────────────────────

def _fix_for_style(finding: StyleFinding, code: str) -> FixSuggestion:
    rule = finding.rule_id
    snippet = finding.snippet.strip()

    if rule == "STY001":
        return FixSuggestion(
            rule_id=rule,
            severity=finding.severity,
            file_path=finding.file_path,
            line=finding.line,
            problem=finding.message,
            fix_description=(
                "Extract part of this function into a smaller helper. "
                "Aim for functions that do one thing and fit on one screen."
            ),
            fix_example=(
                "# Instead of one large function:\n"
                "def process_order(order):\n"
                "    # 80 lines of mixed validation + DB + email logic\n"
                "    ...\n"
                "\n"
                "# Split into focused helpers:\n"
                "def process_order(order):\n"
                "    _validate_order(order)\n"
                "    _save_order(order)\n"
                "    _send_confirmation(order)\n"
                "\n"
                "def _validate_order(order): ...\n"
                "def _save_order(order): ...\n"
                "def _send_confirmation(order): ..."
            ),
        )

    if rule == "STY002":
        fn_name = _extract_fn_name(snippet) or "my_function"
        return FixSuggestion(
            rule_id=rule,
            severity=finding.severity,
            file_path=finding.file_path,
            line=finding.line,
            problem=finding.message,
            fix_description="Add a one-line docstring describing what the function does.",
            fix_example=(
                f'def {fn_name}(...):\n'
                f'    """Brief description of what this function does."""\n'
                f'    ...'
            ),
        )

    if rule == "STY003":
        bad_name = _extract_fn_name(snippet) or "badName"
        good_name = _to_snake_case(bad_name)
        if snippet.strip().startswith("class"):
            bad_name = _extract_class_name(snippet) or "myclass"
            good_name = _to_pascal_case(bad_name)
            return FixSuggestion(
                rule_id=rule,
                severity=finding.severity,
                file_path=finding.file_path,
                line=finding.line,
                problem=finding.message,
                fix_description="Class names must be PascalCase.",
                fix_example=f"class {good_name}:  # was: class {bad_name}",
            )
        return FixSuggestion(
            rule_id=rule,
            severity=finding.severity,
            file_path=finding.file_path,
            line=finding.line,
            problem=finding.message,
            fix_description="Function names must be snake_case.",
            fix_example=f"def {good_name}(...):  # was: def {bad_name}(...)",
        )

    if rule == "STY004":
        module = _extract_wildcard_module(snippet) or "module"
        return FixSuggestion(
            rule_id=rule,
            severity=finding.severity,
            file_path=finding.file_path,
            line=finding.line,
            problem=finding.message,
            fix_description=(
                "Replace wildcard imports with explicit names. "
                "This makes it clear where each name comes from."
            ),
            fix_example=(
                f"# Instead of:\n"
                f"#   from {module} import *\n"
                f"\n"
                f"# Use explicit imports:\n"
                f"from {module} import SpecificClass, specific_function"
            ),
        )

    if rule == "STY005":
        return FixSuggestion(
            rule_id=rule,
            severity=finding.severity,
            file_path=finding.file_path,
            line=finding.line,
            problem=finding.message,
            fix_description="Break the long line using implicit continuation or a local variable.",
            fix_example=(
                "# Instead of one long line:\n"
                "# result = some_function(argument_one, argument_two, argument_three, argument_four)\n"
                "\n"
                "# Use implicit continuation inside brackets:\n"
                "result = some_function(\n"
                "    argument_one,\n"
                "    argument_two,\n"
                "    argument_three,\n"
                "    argument_four,\n"
                ")\n"
                "\n"
                "# Or extract a variable:\n"
                "args = (argument_one, argument_two, argument_three, argument_four)\n"
                "result = some_function(*args)"
            ),
        )

    if rule == "STY006":
        todo_line = snippet if snippet else "# TODO: fix this"
        return FixSuggestion(
            rule_id=rule,
            severity=finding.severity,
            file_path=finding.file_path,
            line=finding.line,
            problem=finding.message,
            fix_description=(
                "Link the TODO/FIXME to a tracker ticket so it gets scheduled."
            ),
            fix_example=(
                f"# Instead of:\n"
                f"#   {todo_line}\n"
                f"\n"
                f"# Add a ticket reference:\n"
                f"# TODO(PROJ-123): fix this\n"
                f"# FIXME(#456): fix this"
            ),
        )

    # Generic style fallback
    return FixSuggestion(
        rule_id=rule,
        severity=finding.severity,
        file_path=finding.file_path,
        line=finding.line,
        problem=finding.message,
        fix_description="Address the style violation noted above.",
        fix_example="",
    )


# ── Extraction helpers ────────────────────────────────────────────────────────

def _extract_var_name(snippet: str) -> str | None:
    m = re.search(r"(\w+)\s*=", snippet)
    return m.group(1) if m else None


def _extract_package_name(snippet: str) -> str | None:
    m = re.search(r"(?:^|\s)([\w-]+)(?:[>=<!]=?[\d.]+)?", snippet)
    return m.group(1) if m else None


def _extract_fn_name(snippet: str) -> str | None:
    m = re.search(r"def\s+(\w+)", snippet)
    return m.group(1) if m else None


def _extract_class_name(snippet: str) -> str | None:
    m = re.search(r"class\s+(\w+)", snippet)
    return m.group(1) if m else None


def _extract_wildcard_module(snippet: str) -> str | None:
    m = re.search(r"from\s+(\S+)\s+import\s+\*", snippet)
    return m.group(1) if m else None


def _to_snake_case(name: str) -> str:
    s = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1_\2", name)
    s = re.sub(r"([a-z\d])([A-Z])", r"\1_\2", s)
    return s.lower()


def _to_pascal_case(name: str) -> str:
    return "".join(word.capitalize() for word in re.split(r"[_\s]+", name))
