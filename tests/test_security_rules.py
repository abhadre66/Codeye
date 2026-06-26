"""Phase 4 tests — security rules SEC001-SEC005 (positive / negative / false-positive)"""

from reviewmind.engine.models import DiffLine, SemanticChunk
from reviewmind.engine.security.engine import scan
from reviewmind.engine.security.rules import sec001, sec002, sec003, sec004, sec005


# ── Helpers ───────────────────────────────────────────────────────────────────

def _chunk(file_path: str, added_lines: list[str], change_type: str = "modified") -> SemanticChunk:
    diff_lines = [
        DiffLine(line_type="added", content=line, old_lineno=None, new_lineno=i + 1)
        for i, line in enumerate(added_lines)
    ]
    return SemanticChunk(
        file_path=file_path,
        start_line=1,
        end_line=len(added_lines),
        chunk_type="function",
        change_type=change_type,
        symbol_name="fn",
        diff_lines=diff_lines,
        classification="new_feature",
        complexity=1,
        content="\n".join(added_lines),
    )


# ── SEC001 — Hardcoded Secret ─────────────────────────────────────────────────

def test_sec001_positive():
    """Hardcoded API key is flagged."""
    chunk = _chunk("auth.py", ['api_key = "sk-abc123xyz789longkey"'])
    findings = sec001(chunk)
    assert len(findings) == 1
    assert findings[0].rule_id == "SEC001"
    assert findings[0].severity == "high"


def test_sec001_negative():
    """Environment variable reference is not flagged."""
    chunk = _chunk("auth.py", ['api_key = os.environ["API_KEY"]'])
    assert sec001(chunk) == []


def test_sec001_false_positive():
    """Known FP: test files get lower severity, not suppressed entirely."""
    chunk = _chunk("tests/test_auth.py", ['api_key = "sk-abc123xyz789longkey"'])
    findings = sec001(chunk)
    # Test files are still flagged but at lower severity
    assert all(f.severity == "low" for f in findings)


# ── SEC002 — SQL Injection ────────────────────────────────────────────────────

def test_sec002_positive():
    """f-string in execute() is flagged as critical."""
    chunk = _chunk("db.py", [f'cursor.execute(f"SELECT * FROM users WHERE id = {{user_id}}")'])
    findings = sec002(chunk)
    assert len(findings) == 1
    assert findings[0].rule_id == "SEC002"
    assert findings[0].severity == "critical"


def test_sec002_negative():
    """Parameterized query with %s is not flagged."""
    chunk = _chunk("db.py", ['cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))'])
    assert sec002(chunk) == []


def test_sec002_false_positive():
    """Known FP: .execute() with a plain string literal (no interpolation) is not flagged."""
    chunk = _chunk("db.py", ['cursor.execute("SELECT 1")'])
    assert sec002(chunk) == []


# ── SEC003 — Insecure Dependency ──────────────────────────────────────────────

def test_sec003_positive():
    """Adding a known vulnerable package is flagged."""
    chunk = _chunk("requirements.txt", ["pyyaml==5.3.1"], change_type="modified")
    findings = sec003(chunk)
    assert len(findings) == 1
    assert findings[0].rule_id == "SEC003"
    assert findings[0].severity == "medium"


def test_sec003_negative():
    """Non-dependency file is not scanned."""
    chunk = _chunk("auth.py", ["import pyyaml"])
    assert sec003(chunk) == []


def test_sec003_false_positive():
    """Known FP: package not in vuln_snapshot is not flagged."""
    chunk = _chunk("requirements.txt", ["httpx==0.27.0"])
    assert sec003(chunk) == []


# ── SEC004 — Missing Input Validation ────────────────────────────────────────

def test_sec004_positive():
    """Route param piped directly into open() without guard is flagged."""
    chunk = _chunk("routes.py", [
        "filename = Query(...)",
        "open(filename, 'r')",
    ])
    findings = sec004(chunk)
    assert len(findings) >= 1
    assert findings[0].rule_id == "SEC004"


def test_sec004_negative():
    """Route param with guard is not flagged."""
    chunk = _chunk("routes.py", [
        "filename = Query(...)",
        "if not filename.startswith('/safe/'):",
        "    raise HTTPException(400)",
        "open(filename, 'r')",
    ])
    assert sec004(chunk) == []


def test_sec004_false_positive():
    """Known FP: open() call with no route params in the chunk is not flagged."""
    chunk = _chunk("utils.py", ['open("config.yaml", "r")'])
    assert sec004(chunk) == []


# ── SEC005 — Unsafe Deserialization ──────────────────────────────────────────

def test_sec005_positive():
    """pickle.load and bare yaml.load are flagged."""
    chunk = _chunk("loader.py", [
        "data = pickle.load(f)",
        "cfg = yaml.load(stream)",
    ])
    findings = sec005(chunk)
    rule_ids = [f.rule_id for f in findings]
    assert rule_ids.count("SEC005") == 2
    assert all(f.severity == "high" for f in findings)


def test_sec005_negative():
    """yaml.safe_load is not flagged."""
    chunk = _chunk("loader.py", ["cfg = yaml.safe_load(stream)"])
    assert sec005(chunk) == []


def test_sec005_false_positive():
    """Known FP: yaml.load with explicit SafeLoader is not flagged."""
    chunk = _chunk("loader.py", ["cfg = yaml.load(stream, SafeLoader)"])
    assert sec005(chunk) == []


# ── scan() — engine aggregator ────────────────────────────────────────────────

def test_scan_aggregates_and_sorts_by_severity():
    """scan() collects findings from multiple chunks and sorts critical first."""
    chunks = [
        _chunk("db.py", [f'cursor.execute(f"SELECT * FROM users WHERE id = {{uid}}")']),
        _chunk("loader.py", ["data = pickle.load(f)"]),
    ]
    findings = scan(chunks)
    assert len(findings) == 2
    severities = [f.severity for f in findings]
    # critical (SEC002) should come before high (SEC005)
    assert severities.index("critical") < severities.index("high")


def test_scan_deduplicates_findings():
    """scan() does not emit duplicate findings for the same rule+file+line."""
    chunk = _chunk("auth.py", ['api_key = "sk-abc123xyz789longkey"'])
    findings = scan([chunk, chunk])  # same chunk twice
    sec001_findings = [f for f in findings if f.rule_id == "SEC001"]
    assert len(sec001_findings) == 1


def test_scan_empty_chunks():
    """scan() on an empty list returns empty findings."""
    assert scan([]) == []
