from __future__ import annotations

import ast

# AST node types that each add one branch to the complexity count.
_BRANCH_TYPES = (
    ast.If,
    ast.For,
    ast.While,
    ast.Try,
    ast.ExceptHandler,
    ast.With,
    ast.Assert,
    ast.comprehension,
)

# Keyword strings used as fallback when ast.parse() fails (non-Python source).
_BRANCH_KEYWORDS = ("if ", "elif ", "for ", "while ", "except", " and ", " or ", "with ")


def cyclomatic_complexity(source: str) -> int:
    """Return cyclomatic complexity for a source snippet.

    Complexity = 1 + number of branching constructs.
    Falls back to keyword counting when source is not valid Python.
    """
    if not source or not source.strip():
        return 1

    try:
        tree = ast.parse(source)
    except SyntaxError:
        return _keyword_complexity(source)

    count = 1
    for node in ast.walk(tree):
        if isinstance(node, _BRANCH_TYPES):
            count += 1
        elif isinstance(node, ast.BoolOp):
            # each additional operand in `a and b and c` = 2 branches
            count += len(node.values) - 1

    return count


def _keyword_complexity(source: str) -> int:
    count = 1
    for kw in _BRANCH_KEYWORDS:
        count += source.count(kw)
    return count
