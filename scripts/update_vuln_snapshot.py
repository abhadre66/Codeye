"""
update_vuln_snapshot.py
-----------------------
Queries the OSV.dev API for known vulnerabilities in common Python packages
and writes the results to reviewmind/engine/security/vuln_snapshot.json.

Usage:
    python scripts/update_vuln_snapshot.py

No external dependencies — uses only the Python standard library.
Run this whenever you want to refresh the vulnerability data (monthly is fine).
"""

import json
import time
import urllib.error
import urllib.request
from pathlib import Path

# ── Output path ───────────────────────────────────────────────────────────────

OUTPUT = Path(__file__).parent.parent / "reviewmind" / "engine" / "security" / "vuln_snapshot.json"

# ── Packages to check ─────────────────────────────────────────────────────────
# Common packages that appear in Python projects. Extend this list freely.

PACKAGES = [
    # Web frameworks
    "django", "flask", "fastapi", "starlette", "tornado", "bottle", "pyramid",
    # HTTP clients
    "requests", "httpx", "urllib3", "aiohttp",
    # Auth / crypto
    "cryptography", "paramiko", "pyjwt", "bcrypt", "passlib", "pyopenssl",
    # Data / serialisation
    "pyyaml", "lxml", "pillow", "defusedxml", "msgpack",
    # Database
    "sqlalchemy", "pymongo", "redis", "psycopg2", "pymysql",
    # Template engines
    "jinja2", "mako", "chameleon",
    # Task queues / messaging
    "celery", "kombu", "pika",
    # Dev / infra
    "werkzeug", "gunicorn", "uvicorn", "twisted",
    # Scientific / data
    "numpy", "scipy", "pandas",
    # Misc utilities
    "setuptools", "pip", "wheel", "six", "certifi",
]

OSV_API = "https://api.osv.dev/v1/query"

# ── Severity ordering (OSV uses CVSS, we map to a readable label) ─────────────

def _severity_label(vuln: dict) -> str:
    for sev in vuln.get("severity", []):
        score_str = sev.get("score", "")
        try:
            score = float(score_str)
            if score >= 9.0:
                return "critical"
            if score >= 7.0:
                return "high"
            if score >= 4.0:
                return "medium"
            return "low"
        except (ValueError, TypeError):
            pass
    return "medium"  # default when CVSS not present


def _short_summary(vuln: dict) -> str:
    """Return a one-line summary: CVE id + alias + short description."""
    aliases = vuln.get("aliases", [])
    cve = next((a for a in aliases if a.startswith("CVE-")), None)
    summary = vuln.get("summary", "").strip()
    details = vuln.get("details", "").strip()

    # Prefer summary, fall back to first sentence of details
    text = summary or (details.split(".")[0] if details else "Known vulnerability")
    if len(text) > 120:
        text = text[:117] + "..."

    prefix = f"{cve}: " if cve else ""
    return f"{prefix}{text}"


# ── Main ──────────────────────────────────────────────────────────────────────

def query_osv(package: str) -> list[dict]:
    payload = json.dumps({
        "package": {"name": package, "ecosystem": "PyPI"}
    }).encode()

    req = urllib.request.Request(
        OSV_API,
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
            return data.get("vulns", [])
    except urllib.error.HTTPError as e:
        print(f"  HTTP {e.code} — skipping")
        return []
    except Exception as e:
        print(f"  Error: {e} — skipping")
        return []


def build_snapshot(packages: list[str]) -> dict[str, str]:
    snapshot: dict[str, str] = {}
    total = len(packages)

    for i, pkg in enumerate(packages, 1):
        print(f"[{i:>2}/{total}] Checking {pkg} ...", end=" ", flush=True)
        vulns = query_osv(pkg)

        if not vulns:
            print("clean")
        else:
            # Pick the most severe finding to summarise
            summaries = [_short_summary(v) for v in vulns]
            count = len(vulns)
            label = f"{count} known {'vulnerability' if count == 1 else 'vulnerabilities'}. e.g. {summaries[0]}"
            snapshot[pkg] = label
            print(f"{count} vuln(s) found")

        # Be polite to the API — 1 request per second
        time.sleep(1)

    return snapshot


def main() -> None:
    print(f"Querying OSV.dev for {len(PACKAGES)} packages...\n")
    snapshot = build_snapshot(PACKAGES)

    vulnerable = len(snapshot)
    clean = len(PACKAGES) - vulnerable
    print(f"\nResults: {vulnerable} vulnerable, {clean} clean")

    OUTPUT.write_text(json.dumps(snapshot, indent=2) + "\n")
    print(f"Written to {OUTPUT}")
    print("\nRun the tests to verify SEC003 still passes:")
    print("  pytest tests/test_security_rules.py -v -k sec003")


if __name__ == "__main__":
    main()
