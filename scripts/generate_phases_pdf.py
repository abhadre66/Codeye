#!/usr/bin/env python3
"""
ReviewMind — Build Phases & Progress Guide
==========================================
Run:   python scripts/generate_phases_pdf.py
Output: ReviewMind_Build_Phases.pdf

Edit any section below and re-run to update the PDF.
"""

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import date

OUTPUT_PATH = "ReviewMind_Build_Phases.pdf"

# ─── COLORS ───────────────────────────────────────────────────────────────────
DARK_BLUE   = (10,  25,  60)
ACCENT      = (37,  99, 235)
LIGHT_BLUE  = (219, 234, 254)
LIGHT_GRAY  = (245, 247, 250)
MID_GRAY    = (150, 158, 172)
WHITE       = (255, 255, 255)
GREEN       = (22, 163,  74)
LIGHT_GREEN = (220, 252, 231)
ORANGE      = (234, 88,  12)
RED         = (220,  38,  38)
YELLOW_BG   = (254, 249, 195)
YELLOW_TEXT = (133,  77,  14)
PURPLE      = (109,  40, 217)
LIGHT_PURPLE= (237, 233, 254)

# ─── SANITIZER ────────────────────────────────────────────────────────────────
_CHAR_MAP = {
    "—": "-", "–": "-", "‘": "'", "’": "'",
    "“": '"', "”": '"', "…": "...", "•": "-",
    "→": "->", "←": "<-", "⇒": "=>", " ": " ",
    "≤": "<=", "≥": ">=", "∞": "inf", "≠": "!=",
    "✓": "[OK]", "✗": "[X]", "▶": ">",
}

def s(text: str) -> str:
    for ch, rep in _CHAR_MAP.items():
        text = text.replace(ch, rep)
    return text.encode("latin-1", errors="replace").decode("latin-1")

# ─────────────────────────────────────────────────────────────────────────────
# CONTENT  <- edit these to update the PDF
# ─────────────────────────────────────────────────────────────────────────────

TODAY = date.today().strftime("%B %d, %Y")

# ── Current project snapshot ──────────────────────────────────────────────────
# Update STATUS for each file as you build: "Done", "Pending", "In Progress"
FILE_TREE = [
    # (indent, filename, status, note)
    (0, "reviewmind/",                   "Dir",         ""),
    (1, "  __init__.py",                 "Done",        "Package init"),
    (1, "  mcp_server.py",               "Done",        "MCP server - ping tool only, 8 real tools pending"),
    (1, "  core/",                        "Dir",         ""),
    (2, "    config.py",                  "Done",        "Pydantic settings - loads from .env"),
    (2, "    logging.py",                 "Done",        "structlog JSON logging"),
    (2, "    cache.py",                   "Done",        "Redis async client + cache_aside helper"),
    (1, "  api/",                         "Dir",         ""),
    (2, "    main.py",                    "Done",        "FastAPI app, CORS, lifespan"),
    (2, "    routes.py",                  "Done",        "/health endpoint"),
    (2, "    static/index.html",          "Done",        "Dev console UI"),
    (1, "  db/",                          "Dir",         ""),
    (2, "    models.py",                  "Done",        "SQLAlchemy models - 5 tables"),
    (2, "    session.py",                 "Done",        "Async session factory"),
    (1, "  services/",                    "Dir",         ""),
    (2, "    github/",                    "Done",        "Phase 2 complete"),
    (3, "      __init__.py",              "Done",        "Package init"),
    (3, "      client.py",                "Done",        "httpx async client, auth, ETags, pagination"),
    (3, "      rate_limiter.py",          "Done",        "Rate limit awareness + exponential backoff"),
    (3, "      repository.py",            "Done",        "get_pr, get_pr_diff, get_pr_files + ETag cache"),
    (1, "  engine/",                      "Dir",         ""),
    (2, "    diff_parser.py",             "Pending",     "Phase 3 - unidiff parsing"),
    (2, "    chunker.py",                 "Pending",     "Phase 3 - AST semantic chunking"),
    (2, "    classifier.py",              "Pending",     "Phase 3 - change classification"),
    (2, "    complexity.py",              "Pending",     "Phase 3 - cyclomatic complexity"),
    (2, "    security/",                  "Pending",     "Phase 4"),
    (3, "      rules.py",                 "Pending",     "5 security rules (SEC001-005)"),
    (3, "      engine.py",                "Pending",     "Rule registry + aggregation"),
    (2, "    style/",                     "Pending",     "Phase 5"),
    (3, "      rules.py",                 "Pending",     "Style rules (STY001-006)"),
    (3, "      engine.py",                "Pending",     "reviewmind.yaml loader + runner"),
    (0, "alembic/",                       "Dir",         ""),
    (1, "  versions/",                    "Dir",         ""),
    (2, "    108d2ae2ccf2_*.py",          "Done",        "Initial migration - health check table"),
    (2, "    0002_full_schema.py",        "Done",        "5 core tables - repositories, pull_requests, diff_chunks, findings, reviews"),
    (0, "tests/",                         "Dir",         ""),
    (1, "  __init__.py",                  "Done",        ""),
    (1, "  fixtures/",                    "Dir",         ""),
    (2, "    github/",                    "Dir",         ""),
    (3, "      pr.json",                  "Done",        "PR #42 fixture - number, title, author, state"),
    (3, "      pr_files.json",            "Done",        "2-file fixture - auth.py added, routes.py modified"),
    (1, "  test_github_client.py",        "Done",        "12 tests passing - respx mocks, ETag, paginate"),
    (1, "  test_diff_parser.py",          "Pending",     "Phase 3 - fixture diffs"),
    (1, "  test_security_rules.py",       "Pending",     "Phase 4 - pos/neg/FP per rule"),
    (1, "  test_style_rules.py",          "Pending",     "Phase 5"),
    (1, "  test_e2e_golden_path.py",      "Pending",     "Phase 6 - full flow"),
    (0, "scripts/",                       "Dir",         ""),
    (1, "  generate_pdf.py",              "Done",        "Project overview PDF generator"),
    (1, "  generate_phases_pdf.py",       "Done",        "This file - build phases PDF"),
    (0, "docker-compose.yml",             "Done",        "Postgres + Redis"),
    (0, "pyproject.toml",                 "Done",        "Dependencies, build config"),
    (0, ".env / .env.example",            "Done",        "Secrets (never commit .env)"),
]

# ── Phase definitions ─────────────────────────────────────────────────────────
# Each phase: (number, name, status, color, day_range, objective, files_to_create, tasks, done_when, test_cmd)
PHASES = [
    {
        "number":    "Phase 1",
        "name":      "Foundation",
        "status":    "Done",
        "color":     GREEN,
        "days":      "Days 1-2",
        "objective": (
            "Stand up the project skeleton: Docker Compose for Postgres + Redis, "
            "FastAPI with a /health endpoint that verifies both services, "
            "SQLAlchemy async models for all 5 tables, Alembic migration, "
            "structured logging, Redis client, and a bare MCP server with a ping tool."
        ),
        "files": [
            "reviewmind/core/config.py       - Pydantic settings, loads .env",
            "reviewmind/core/logging.py      - structlog JSON logging + correlation ID",
            "reviewmind/core/cache.py        - Redis asyncio client",
            "reviewmind/db/models.py         - 5 SQLAlchemy models",
            "reviewmind/db/session.py        - AsyncSession factory",
            "reviewmind/api/main.py          - FastAPI app + lifespan",
            "reviewmind/api/routes.py        - /health route",
            "reviewmind/mcp_server.py        - MCP server + ping tool",
            "alembic/versions/0001_*.py      - Initial migration",
            "docker-compose.yml              - Postgres + Redis services",
            "pyproject.toml                  - Project deps + build config",
        ],
        "tasks": [
            "Install fpdf2, mcp, fastapi, sqlalchemy, redis, structlog, alembic",
            "Write docker-compose.yml with postgres + redis services",
            "Create core/config.py - Settings class reading from .env",
            "Create core/logging.py - configure structlog for JSON output",
            "Create core/cache.py - async Redis client with ping test",
            "Write all 5 SQLAlchemy models (repositories, pull_requests, diff_chunks, findings, reviews)",
            "Create db/session.py with AsyncSession and get_session dependency",
            "Run: alembic init alembic && alembic revision --autogenerate",
            "Run: alembic upgrade head - verify tables exist in Postgres",
            "Write FastAPI app with /health route checking DB + Redis",
            "Write mcp_server.py with ping tool - verify Claude Desktop connects",
            "Run: docker compose up && curl localhost:8000/health -> {status: ok}",
        ],
        "done_when": [
            "docker compose up starts without errors",
            "GET /health returns {status:ok, database:ok, redis:ok}",
            "alembic upgrade head creates all 5 tables",
            "MCP ping tool responds pong from Claude Desktop",
            "JSON logs appear in stdout with correlation_id field",
        ],
        "test_cmd": "docker compose up -d && curl localhost:8000/health",
    },
    {
        "number":    "Phase 2",
        "name":      "GitHub Client + Redis Cache",
        "status":    "Done",
        "color":     GREEN,
        "days":      "Days 3-4",
        "objective": (
            "Build the GitHub integration layer: a low-level HTTP client with auth/ETags, "
            "a rate-limit awareness module, and a high-level repository service. "
            "Wrap all GitHub calls with Redis cache-aside so repeated calls hit cache not GitHub."
        ),
        "files": [
            "reviewmind/services/github/__init__.py",
            "reviewmind/services/github/client.py      - httpx client, auth, ETags, pagination",
            "reviewmind/services/github/rate_limiter.py - X-RateLimit-* header tracking + backoff",
            "reviewmind/services/github/repository.py   - get_pr, get_pr_diff, get_pr_files",
            "alembic/versions/0002_full_schema.py       - add all 5 tables properly",
            "tests/fixtures/github/pr_42.json           - real response captured + sanitized",
            "tests/test_github_client.py                - mocked with respx",
        ],
        "tasks": [
            "pip install httpx respx",
            "Write GitHubClient class in client.py with base_url, default headers (auth, version)",
            "Implement get(url) -> GitHubResponse with body, status_code, rate_limit, etag fields",
            "Implement paginate(url) -> AsyncIterator that follows Link: rel=next",
            "Write RateLimiter class - reads X-RateLimit-Remaining, logs warning below threshold",
            "Implement exponential backoff for 429 / 403 rate limit responses",
            "Write GitHubRepository service: get_pr(owner, repo, number) -> PRSummary",
            "Write get_pr_diff(owner, repo, number) -> str (raw unified diff)",
            "Write get_pr_files(owner, repo, number) -> list[PRFile]",
            "Extend core/cache.py with cache_key builders and cache_aside() helper",
            "Wrap every GitHub call with cache-aside (check Redis first, store on miss)",
            "Implement ETag flow: store ETag in Redis, send If-None-Match, handle 304",
            "Capture a real PR response from your test repo, save as fixture JSON",
            "Write mocked tests using respx for all 3 repository methods",
            "Verify: second call to get_pr hits Redis not GitHub (check logs)",
        ],
        "done_when": [
            "get_pr() returns PRSummary for a real test PR",
            "get_pr_diff() returns raw unified diff string",
            "Second call for same PR shows cache_hit=True in logs",
            "Rate limit remaining is logged on every GitHub call",
            "All tests pass with respx mocks (no real GitHub calls in CI)",
        ],
        "test_cmd": "pytest tests/test_github_client.py -v",
    },
    {
        "number":    "Phase 3",
        "name":      "Semantic Diff Engine",
        "status":    "Next",
        "color":     ACCENT,
        "days":      "Days 5-6",
        "objective": (
            "Build the intellectual core of ReviewMind: parse raw unified diffs into structured "
            "SemanticChunks using the unidiff library + Python AST module. Each chunk knows its "
            "file, line range, containing function/class, change type, and complexity score."
        ),
        "files": [
            "reviewmind/engine/__init__.py",
            "reviewmind/engine/models.py        - SemanticChunk, FileDiff, Hunk Pydantic models",
            "reviewmind/engine/diff_parser.py   - unidiff-based parser -> FileDiff + Hunk objects",
            "reviewmind/engine/chunker.py       - AST mapping of hunks to functions/classes",
            "reviewmind/engine/classifier.py    - new_feature/bug_fix/refactor/test/config/dep",
            "reviewmind/engine/complexity.py    - cyclomatic complexity per function",
            "reviewmind/services/analysis/",
            "reviewmind/services/analysis/from_paste.py   - code string -> CodeInput",
            "reviewmind/services/analysis/from_upload.py  - file list -> CodeInput",
            "tests/fixtures/diffs/              - .diff fixture files",
            "tests/test_diff_parser.py",
            "tests/test_chunker.py",
        ],
        "tasks": [
            "pip install unidiff",
            "Define SemanticChunk model: file_path, start_line, end_line, chunk_type, classification, complexity, content, diff",
            "Write diff_parser.py: parse raw diff string -> list[FileDiff] using unidiff library",
            "Each FileDiff: filename, change_type (added/modified/deleted/renamed), list of Hunks",
            "Each Hunk: old_start, old_length, new_start, new_length, lines[(type, content)]",
            "Write chunker.py: for each changed file, fetch full file from GitHub, run ast.parse()",
            "Map hunk line ranges to enclosing FunctionDef / ClassDef AST nodes",
            "Merge hunks in the same function into one SemanticChunk",
            "Handle module-level code (no enclosing function) -> chunk_type='module'",
            "Write classifier.py: classify each chunk (new_feature if function didn't exist before, etc.)",
            "Write complexity.py: count if/elif/for/while/except/and/or -> complexity = 1 + count",
            "Write from_paste.py and from_upload.py adapters -> CodeInput(source, files)",
            "Collect 3 fixture .diff files: one with new function, one bug fix, one config change",
            "Write tests: given fixture diff -> correct chunk count, types, line ranges, complexity",
        ],
        "done_when": [
            "parse_diff(fixture) returns correct FileDiff list with right hunk boundaries",
            "chunker maps a multi-hunk function correctly to one SemanticChunk",
            "classifier correctly labels new function vs modified function",
            "complexity score matches manual count for 3 hand-checked examples",
            "90%+ test coverage on diff_parser.py and chunker.py",
        ],
        "test_cmd": "pytest tests/test_diff_parser.py tests/test_chunker.py -v --cov=reviewmind/engine",
    },
    {
        "number":    "Phase 4",
        "name":      "Security Analysis Engine",
        "status":    "Upcoming",
        "color":     RED,
        "days":      "Day 7",
        "objective": (
            "Implement the 5 security rules as a pluggable rule registry. Each rule is a small "
            "function taking a SemanticChunk and returning SecurityFinding objects. "
            "Rules run against all chunks from Phase 3."
        ),
        "files": [
            "reviewmind/engine/security/__init__.py",
            "reviewmind/engine/security/models.py    - SecurityFinding Pydantic model",
            "reviewmind/engine/security/rules.py     - SEC001 through SEC005 rule functions",
            "reviewmind/engine/security/engine.py    - rule registry, iterate + aggregate",
            "tests/test_security_rules.py            - 3 test cases per rule",
        ],
        "tasks": [
            "Define SecurityFinding: rule_id, severity, file_path, line, message, snippet",
            "Write rule registry: list of (rule_id, fn) pairs - engine iterates all rules per chunk",
            "SEC001 Hardcoded Secret: regex on added lines for AWS keys, api_key=, BEGIN PRIVATE KEY",
            "SEC001: allowlist for test/example/sample files (lower severity)",
            "SEC002 SQL Injection: detect f-string/format/% in cursor.execute() / .raw() args",
            "SEC002: confirm parameterized queries are NOT flagged",
            "SEC003 Insecure Dep: parse requirements.txt/pyproject.toml added lines vs vuln snapshot JSON",
            "SEC004 Missing Validation: flag route handlers using path params in open() or execute()",
            "SEC005 Unsafe Deserialization: flag pickle.load, yaml.load without SafeLoader, eval, exec",
            "Write engine.py: run all enabled rules per chunk, deduplicate, sort by severity",
            "Write test_security_rules.py: for each rule - one positive (catches it), one negative (ignores safe), one false-positive (documents known FP)",
        ],
        "done_when": [
            "Each SEC rule catches its target pattern in fixture code",
            "Parameterized SQL query is NOT flagged by SEC002",
            "yaml.safe_load() is NOT flagged by SEC005",
            "3+ test cases per rule passing",
            "90%+ coverage on rules.py",
        ],
        "test_cmd": "pytest tests/test_security_rules.py -v --cov=reviewmind/engine/security",
    },
    {
        "number":    "Phase 5",
        "name":      "Style Engine + reviewmind.yaml",
        "status":    "Upcoming",
        "color":     PURPLE,
        "days":      "Day 8",
        "objective": (
            "Build the style analysis engine driven by a per-repo reviewmind.yaml config file. "
            "Rules are togglable per project. Six built-in rules covering function length, "
            "naming conventions, forbidden imports, line length, docstrings, and TODO tickets."
        ),
        "files": [
            "reviewmind/engine/style/__init__.py",
            "reviewmind/engine/style/models.py      - StyleFinding, RuleConfig Pydantic models",
            "reviewmind/engine/style/rules.py        - STY001 through STY006 rule functions",
            "reviewmind/engine/style/engine.py       - load reviewmind.yaml, filter + run rules",
            "reviewmind.yaml                         - example config for this repo",
            "tests/test_style_rules.py",
        ],
        "tasks": [
            "Define RuleConfig Pydantic model matching reviewmind.yaml schema",
            "Write YAML loader: fetch reviewmind.yaml from repo root via GitHub client, parse with PyYAML",
            "Cache parsed config in Redis (repo config rarely changes - 1h TTL)",
            "STY001 Max Function Length: count lines in chunk.content vs config.max_function_length",
            "STY002 Missing Docstring: check AST for FunctionDef / ClassDef missing docstring node",
            "STY003 Naming Convention: regex match per identifier type (snake_case / PascalCase)",
            "STY004 Forbidden Import: check added lines for patterns in config.forbidden_imports list",
            "STY005 Max Line Length: check each added line length vs config.max_line_length",
            "STY006 TODO without ticket: regex for TODO/FIXME not followed by #123 or JIRA-456",
            "Write engine.py: load config, filter rules by enabled flag, run per chunk",
            "Write example reviewmind.yaml with all 6 rules configured",
            "Write tests: toggling a rule off in config removes findings for that rule",
        ],
        "done_when": [
            "Disabling STY001 in reviewmind.yaml removes all max_function_length findings",
            "PascalCase function name is flagged by STY003",
            "Missing docstring finding appears for public functions",
            "Rules correctly skip test files where chunk_type='test'",
        ],
        "test_cmd": "pytest tests/test_style_rules.py -v --cov=reviewmind/engine/style",
    },
    {
        "number":    "Phase 6",
        "name":      "MCP Tools + Claude API Loop",
        "status":    "Upcoming",
        "color":     (109, 40, 217),
        "days":      "Days 9-10",
        "objective": (
            "Wire all 19 MCP tools to the Service Layer. Add a /chat FastAPI endpoint "
            "that runs the Claude API tool loop: send message + tools, execute returned "
            "tool calls via MCP, send results back, repeat until Claude stops calling tools."
        ),
        "files": [
            "reviewmind/mcp_server.py              - add all 19 real tools (replace ping stub)",
            "reviewmind/api/routes.py              - add POST /chat endpoint",
            "reviewmind/services/review.py         - post_review service (GitHub Reviews API)",
            "reviewmind/services/fix.py            - apply_fix service (code patching logic)",
            "reviewmind/api/auth.py                - JWT auth middleware for gated routes",
            "tests/test_mcp_tools.py               - tools/list + tools/call per tool",
            "tests/test_e2e_golden_path.py         - full flow: fixture PR -> findings -> review",
            "claude_desktop_config.json            - (local, not committed) for manual testing",
        ],
        "tasks": [
            "pip install anthropic python-jose[cryptography]",
            "Register all 19 tools in mcp_server.py with correct inputSchema JSON schemas",
            "Each tool handler: validate args -> call service function -> format MCP result",
            "Write /chat endpoint in routes.py: accepts {message, code?, files?}",
            "/chat endpoint: get tools from MCP via tools/list, send to Claude API",
            "Implement tool loop: while stop_reason == tool_use: call tool via MCP, append result, re-send",
            "Write auth.py: JWT decode middleware, require_auth dependency for apply_fix + post_review",
            "Add /auth/login endpoint: validate credentials -> return JWT",
            "Write apply_fix service: take finding + code -> apply patch -> return modified code",
            "Write post_review service: POST to GitHub Reviews API, persist to reviews table",
            "Test each tool via tools/list and tools/call directly (no Claude Desktop needed)",
            "Write e2e golden path test: fixture diff -> analyze -> security -> style -> review draft",
            "Manually verify in Claude Desktop: 'Review PR #X on owner/repo' works end-to-end",
        ],
        "done_when": [
            "tools/list returns all 19 tools with correct schemas",
            "GET /health + POST /chat both respond correctly",
            "Full golden path works: user message -> Claude -> tools -> synthesized review",
            "apply_fix is blocked without JWT, succeeds with valid JWT",
            "e2e golden path test passes with fixture data",
        ],
        "test_cmd": "pytest tests/test_mcp_tools.py tests/test_e2e_golden_path.py -v",
    },
    {
        "number":    "Phase 7",
        "name":      "Frontend  (React / Next.js)",
        "status":    "Upcoming",
        "color":     (6, 148, 162),
        "days":      "Days 11-14",
        "objective": (
            "Build the user-facing frontend: a chat interface where users can type messages, "
            "paste code, upload files, and see findings displayed with syntax highlighting. "
            "Auth flow for apply_fix and post_review. All API calls go to the FastAPI backend."
        ),
        "files": [
            "frontend/                         - new Next.js project",
            "frontend/app/page.tsx             - main chat UI",
            "frontend/components/ChatInput.tsx  - message input + code paste + file upload",
            "frontend/components/FindingCard.tsx- individual finding with severity badge",
            "frontend/components/CodeDiff.tsx  - before/after diff viewer for apply_fix",
            "frontend/components/AuthModal.tsx  - login modal triggered by auth gate",
            "frontend/lib/api.ts               - typed API client for FastAPI backend",
        ],
        "tasks": [
            "npx create-next-app frontend --typescript --tailwind",
            "Build ChatInput: text area for messages, code paste box, file drag-drop zone",
            "Build message list: user messages + Claude responses with markdown rendering",
            "Build FindingCard: rule_id badge, severity color, file+line, message, 'Suggest Fix' button",
            "Wire 'Suggest Fix' button -> POST /chat {message: 'fix finding X'} -> shows CodeDiff",
            "Build CodeDiff: side-by-side original vs fixed code using react-diff-viewer",
            "Wire 'Apply Fix' button -> auth check -> show AuthModal if not logged in",
            "Build AuthModal: email/password form -> POST /auth/login -> store JWT in memory",
            "After auth: retry apply_fix with JWT -> show success + copy-to-clipboard button",
            "File upload: input[type=file] -> read as text -> include in POST /chat as files[]",
            "Add per-file tabs when multiple files uploaded - one FindingCard list per file",
            "Test golden path in browser: paste SQL injection code -> see SEC002 finding -> suggest fix -> login -> apply",
        ],
        "done_when": [
            "User can paste code and see findings without logging in",
            "Clicking Apply Fix triggers login modal if not authenticated",
            "After login, apply_fix returns patched code shown in CodeDiff",
            "File upload works for .py, .ts, .yaml files",
            "PR review flow works end-to-end from chat input to displayed review",
        ],
        "test_cmd": "cd frontend && npm run dev  # then test manually in browser",
    },
    {
        "number":    "Phase 8",
        "name":      "A2A Parallel Agents",
        "status":    "Future",
        "color":     MID_GRAY,
        "days":      "Post-MVP",
        "objective": (
            "Introduce Agent-to-Agent (A2A) communication so the security, style, and diff "
            "engines run as independent parallel sub-agents instead of sequentially. "
            "ReviewMind becomes an orchestrator, coordinating specialist agents and merging results."
        ),
        "files": [
            "reviewmind/agents/__init__.py",
            "reviewmind/agents/orchestrator.py   - coordinates sub-agents, merges results",
            "reviewmind/agents/security_agent.py - wraps security engine as A2A agent",
            "reviewmind/agents/style_agent.py    - wraps style engine as A2A agent",
            "reviewmind/agents/diff_agent.py     - wraps diff engine as A2A agent",
        ],
        "tasks": [
            "Define A2A agent interface: agent card (name, capabilities), task endpoint",
            "Wrap SecurityEngine as a standalone A2A agent (its own FastAPI sub-app)",
            "Wrap StyleEngine as a standalone A2A agent",
            "Write Orchestrator: dispatch tasks to all 3 agents concurrently (asyncio.gather)",
            "Merge results: combine SecurityFindings + StyleFindings + SemanticChunks",
            "Expose ReviewMind itself as an A2A agent so other systems can call it",
            "Benchmark: measure latency improvement vs sequential execution on a large PR",
        ],
        "done_when": [
            "Security, style, diff analysis run concurrently (measured via logs)",
            "Orchestrator correctly merges findings from all 3 agents",
            "ReviewMind responds to A2A agent discovery requests",
            "Latency on a 20-file PR is < 50% of sequential baseline",
        ],
        "test_cmd": "pytest tests/test_agents.py -v",
    },
]

# ─────────────────────────────────────────────────────────────────────────────
# PDF CLASS
# ─────────────────────────────────────────────────────────────────────────────

class PhasesPDF(FPDF):

    def cell(self, w=0, h=0, text="", *args, **kwargs):
        return super().cell(w, h, s(str(text)), *args, **kwargs)

    def multi_cell(self, w, h, text="", *args, **kwargs):
        return super().multi_cell(w, h, s(str(text)), *args, **kwargs)

    def header(self):
        if self.page_no() == 1:
            return
        self.set_fill_color(*DARK_BLUE)
        self.rect(0, 0, 210, 11, "F")
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*WHITE)
        self.set_y(3.5)
        self.cell(0, 4, "ReviewMind - Build Phases & Progress Guide", align="C")
        self.set_text_color(0, 0, 0)
        self.set_y(14)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-11)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 5, f"Page {self.page_no()}  |  Generated {TODAY}  |  ReviewMind Build Guide", align="C")
        self.set_text_color(0, 0, 0)

    def section_title(self, title):
        self.ln(4)
        y = self.get_y()
        self.set_fill_color(*DARK_BLUE)
        self.rect(10, y, 190, 9, "F")
        self.set_font("Helvetica", "B", 11)
        self.set_text_color(*WHITE)
        self.set_xy(14, y + 1.5)
        self.cell(0, 6, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def subsection(self, title):
        self.ln(2)
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(*ACCENT)
        self.cell(0, 6, title, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        y = self.get_y()
        self.set_draw_color(*ACCENT)
        self.line(10, y, 200, y)
        self.set_draw_color(0, 0, 0)
        self.set_text_color(0, 0, 0)
        self.ln(3)

    def body(self, text):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        self.multi_cell(190, 5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def bullet(self, text, indent=14, bold_prefix=None):
        self.set_x(indent)
        if bold_prefix:
            self.set_font("Helvetica", "B", 8)
            self.set_text_color(*ACCENT)
            self.cell(self.get_string_width(bold_prefix) + 2, 5, bold_prefix)
            self.set_font("Helvetica", "", 8)
            self.set_text_color(40, 40, 40)
            self.multi_cell(0, 5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        else:
            self.set_font("Helvetica", "", 8)
            self.set_text_color(40, 40, 40)
            self.cell(4, 5, "-")
            self.multi_cell(0, 5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)

    def tbl_header(self, cols):
        self.set_fill_color(*DARK_BLUE)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 8)
        for label, w in cols:
            self.cell(w, 7, label, border=1, fill=True, align="C")
        self.ln()
        self.set_text_color(0, 0, 0)

    def tbl_row(self, cells, shade=False):
        self.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        self.set_font("Helvetica", "", 8)
        self.set_text_color(30, 30, 30)
        for val, w in cells:
            self.cell(w, 6, str(val), border=1, fill=True)
        self.ln()
        self.set_text_color(0, 0, 0)

    def phase_badge(self, x, y, text, color, w=30, h=7):
        self.set_fill_color(*color)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 8)
        self.set_xy(x, y)
        self.cell(w, h, text, fill=True, align="C")
        self.set_text_color(0, 0, 0)

    def status_badge(self, x, y, status):
        colors = {
            "Done":        (GREEN,      WHITE),
            "Next":        (ACCENT,     WHITE),
            "Upcoming":    (ORANGE,     WHITE),
            "Future":      (MID_GRAY,   WHITE),
            "In Progress": (YELLOW_TEXT, YELLOW_BG),
        }
        bg, fg = colors.get(status, (MID_GRAY, WHITE))
        self.set_fill_color(*bg)
        self.set_text_color(*fg)
        self.set_font("Helvetica", "B", 7)
        self.set_xy(x, y)
        self.cell(22, 6, status, fill=True, align="C")
        self.set_text_color(0, 0, 0)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def cover_page(pdf: PhasesPDF):
    pdf.add_page()
    pdf.set_fill_color(*DARK_BLUE)
    pdf.rect(0, 0, 210, 297, "F")

    # Title
    pdf.set_font("Helvetica", "B", 32)
    pdf.set_text_color(*WHITE)
    pdf.set_y(60)
    pdf.cell(0, 12, "ReviewMind", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(180, 200, 240)
    pdf.cell(0, 8, "Build Phases & Progress Guide", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Accent bar
    pdf.set_fill_color(*ACCENT)
    pdf.rect(0, 90, 210, 3, "F")

    # Phase pills
    phases_summary = [
        ("Phase 1", "Foundation",       GREEN),
        ("Phase 2", "GitHub Client",    ACCENT),
        ("Phase 3", "Diff Engine",      ORANGE),
        ("Phase 4", "Security Engine",  RED),
        ("Phase 5", "Style Engine",     PURPLE),
        ("Phase 6", "MCP + Claude API", (109,40,217)),
        ("Phase 7", "Frontend",         (6,148,162)),
        ("Phase 8", "A2A Agents",       MID_GRAY),
    ]

    pill_w = 44
    pill_h = 16
    cols = 4
    start_x = (210 - cols * (pill_w + 4)) / 2
    start_y = 105

    for i, (num, name, color) in enumerate(phases_summary):
        col = i % cols
        row = i // cols
        px = start_x + col * (pill_w + 4)
        py = start_y + row * (pill_h + 6)
        pdf.set_fill_color(*color)
        pdf.rect(px, py, pill_w, pill_h, "F")
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*WHITE)
        pdf.set_xy(px, py + 2)
        pdf.cell(pill_w, 4, num, align="C")
        pdf.set_font("Helvetica", "", 6.5)
        pdf.set_xy(px, py + 7)
        pdf.cell(pill_w, 4, name, align="C")

    # Status legend
    pdf.set_y(165)
    pdf.set_font("Helvetica", "B", 9)
    pdf.set_text_color(*WHITE)
    pdf.cell(0, 6, "Current Status:  Phases 1 & 2 DONE  -  Phase 3 is NEXT", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Date
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MID_GRAY)
    pdf.set_y(270)
    pdf.cell(0, 6, f"Generated: {TODAY}", align="C")
    pdf.set_text_color(0, 0, 0)


def progress_overview_page(pdf: PhasesPDF):
    pdf.add_page()
    pdf.section_title("Project Progress Overview")

    # ── Progress timeline ─────────────────────────────────────────────────────
    pdf.subsection("Build Timeline")

    phase_rows = [
        ("Phase 1", "Foundation",           "Days 1-2",   "Done",     "docker compose up + /health + ping tool"),
        ("Phase 2", "GitHub Client + Cache","Days 3-4",   "Done",     "httpx client, Redis cache-aside, rate limiter - 12 tests green"),
        ("Phase 3", "Semantic Diff Engine", "Days 5-6",   "Next",     "unidiff parsing, AST chunking, classification"),
        ("Phase 4", "Security Engine",      "Day 7",      "Upcoming", "5 rules: SEC001-005, rule registry"),
        ("Phase 5", "Style Engine",         "Day 8",      "Upcoming", "reviewmind.yaml, 6 style rules"),
        ("Phase 6", "MCP + Claude API",     "Days 9-10",  "Upcoming", "19 tools wired, /chat endpoint, auth gate"),
        ("Phase 7", "Frontend",             "Days 11-14", "Upcoming", "Next.js chat UI, paste, upload, auth modal"),
        ("Phase 8", "A2A Agents",           "Post-MVP",   "Future",   "Parallel sub-agents, orchestrator"),
    ]

    status_colors = {
        "Done":     GREEN,
        "Next":     ACCENT,
        "Upcoming": ORANGE,
        "Future":   MID_GRAY,
    }

    cols = [("Phase", 18), ("Name", 40), ("Timeline", 22), ("Status", 22), ("Key Deliverable", 88)]
    pdf.tbl_header(cols)
    for i, (phase, name, timeline, status, deliverable) in enumerate(phase_rows):
        shade = i % 2 == 0
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*DARK_BLUE)
        pdf.cell(18, 6, phase, border=1, fill=True, align="C")
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(40, 6, name, border=1, fill=True)
        pdf.cell(22, 6, timeline, border=1, fill=True, align="C")
        pdf.set_fill_color(*status_colors[status])
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 7)
        pdf.cell(22, 6, status, border=1, fill=True, align="C")
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(88, 6, deliverable, border=1, fill=True)
        pdf.ln()
    pdf.set_text_color(0, 0, 0)

    pdf.ln(5)

    # ── Visual progress bar ───────────────────────────────────────────────────
    pdf.subsection("Visual Progress  (2 of 8 Phases Complete)")
    bar_x = 10
    bar_y = pdf.get_y() + 2
    bar_h = 10
    total_w = 190
    phase_w = total_w / 8

    for i, (_, _, _, status, _) in enumerate(phase_rows):
        x = bar_x + i * phase_w
        color = status_colors[status]
        pdf.set_fill_color(*color)
        pdf.set_draw_color(*WHITE)
        pdf.set_line_width(0.5)
        pdf.rect(x, bar_y, phase_w, bar_h, "FD")
        pdf.set_font("Helvetica", "B", 6)
        pdf.set_text_color(*WHITE)
        pdf.set_xy(x, bar_y + 3)
        pdf.cell(phase_w, 4, f"P{i+1}", align="C")

    pdf.set_draw_color(0, 0, 0)
    pdf.set_line_width(0.2)
    pdf.set_text_color(0, 0, 0)
    pdf.set_y(bar_y + bar_h + 3)

    # Legend
    pdf.set_x(10)
    legend = [("Done", GREEN), ("Next", ACCENT), ("Upcoming", ORANGE), ("Future", MID_GRAY)]
    for label, color in legend:
        pdf.set_fill_color(*color)
        pdf.rect(pdf.get_x(), pdf.get_y() + 1, 8, 4, "F")
        pdf.set_x(pdf.get_x() + 10)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(22, 6, label)
    pdf.ln(8)

    # ── What's built so far ───────────────────────────────────────────────────
    pdf.subsection("What Exists in the Repo Today")

    built = [
        ("docker-compose.yml",          "Postgres + Redis services - run with: docker compose up -d"),
        ("pyproject.toml",              "All Python dependencies declared"),
        (".env / .env.example",         "Environment config - copy .env.example to .env and fill in"),
        ("reviewmind/core/config.py",   "Pydantic Settings - reads GITHUB_TOKEN, DATABASE_URL, REDIS_URL"),
        ("reviewmind/core/logging.py",  "structlog configured for JSON output"),
        ("reviewmind/core/cache.py",    "Redis asyncio client + cache_aside helper + ETag key builders"),
        ("reviewmind/db/models.py",     "5 SQLAlchemy models: repositories, pull_requests, diff_chunks, findings, reviews"),
        ("reviewmind/db/session.py",    "AsyncSession factory + get_session FastAPI dependency"),
        ("reviewmind/api/main.py",      "FastAPI app with lifespan startup/shutdown"),
        ("reviewmind/api/routes.py",    "/health endpoint - verifies DB + Redis"),
        ("reviewmind/mcp_server.py",    "MCP server with ping tool (placeholder - real tools in Phase 6)"),
        ("alembic/versions/108d2*.py",  "First migration - health check table"),
        ("alembic/versions/0002_*.py",  "Full schema - 5 tables with indexes"),
        ("services/github/client.py",   "GitHubClient: httpx AsyncClient, auth, ETags, pagination, error mapping"),
        ("services/github/rate_limiter.py", "get_with_retry: exponential backoff on 429/403, warn < 100 remaining"),
        ("services/github/repository.py","GitHubRepository: get_pr, get_pr_diff, get_pr_files with Redis cache-aside"),
        ("tests/fixtures/github/*.json","pr.json + pr_files.json fixture data for mocked tests"),
        ("tests/test_github_client.py", "12 tests all green - client, repository, ETag, paginate"),
        ("scripts/generate_pdf.py",     "Project overview PDF generator"),
        ("scripts/generate_phases_pdf.py", "This file - build phases PDF generator"),
    ]

    cols = [("File / Item", 90), ("What It Does", 100)]
    pdf.tbl_header(cols)
    for i, (file, desc) in enumerate(built):
        pdf.set_fill_color(*((220, 252, 231) if i % 2 == 0 else WHITE))
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(*DARK_BLUE)
        pdf.cell(90, 6, file, border=1, fill=True)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(100, 6, desc, border=1, fill=True)
        pdf.ln()
    pdf.set_text_color(0, 0, 0)


def file_tree_page(pdf: PhasesPDF):
    pdf.add_page()
    pdf.section_title("Full Project File Tree  -  Status per File")

    pdf.body(
        "Every file the project will have at completion. "
        "Green = exists and working. Blue = next to build. Gray = future phases."
    )

    status_colors_fg = {
        "Done":        ((21,128,61),  (220,252,231)),
        "Pending":     (ACCENT,       LIGHT_BLUE),
        "In Progress": (YELLOW_TEXT,  YELLOW_BG),
        "Dir":         (DARK_BLUE,    LIGHT_GRAY),
    }

    for indent, filename, status, note in FILE_TREE:
        fg, bg = status_colors_fg.get(status, (MID_GRAY, WHITE))
        pdf.set_fill_color(*bg)
        # Indent
        x = 10 + indent * 4
        pdf.set_x(x)
        # Filename
        pdf.set_font("Helvetica", "B" if status == "Dir" else "", 7.5)
        pdf.set_text_color(*fg)
        name_w = 95 - indent * 4
        pdf.cell(name_w, 5.5, filename, border="LB", fill=True)
        # Status
        if status != "Dir":
            s_fg, s_bg = status_colors_fg.get(status, (MID_GRAY, WHITE))
            pdf.set_fill_color(*s_bg)
            pdf.set_font("Helvetica", "B", 6.5)
            pdf.set_text_color(*s_fg)
            pdf.cell(18, 5.5, status, border="TB", fill=True, align="C")
        else:
            pdf.set_fill_color(*LIGHT_GRAY)
            pdf.cell(18, 5.5, "", border="TB", fill=True)
        # Note
        pdf.set_fill_color(*WHITE)
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(*MID_GRAY)
        remaining = 10 + 95 + 18 + 77
        pdf.cell(77, 5.5, note, border="RB", fill=True)
        pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # Legend
    pdf.set_x(10)
    for label, (fg, bg) in [
        ("Done - exists and working",       ((21,128,61), (220,252,231))),
        ("Pending - to be built",           (ACCENT, LIGHT_BLUE)),
        ("Dir - directory",                 (DARK_BLUE, LIGHT_GRAY)),
    ]:
        pdf.set_fill_color(*bg)
        pdf.set_draw_color(*fg)
        pdf.set_line_width(0.3)
        pdf.rect(pdf.get_x(), pdf.get_y() + 1, 8, 4, "FD")
        pdf.set_x(pdf.get_x() + 10)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(50, 50, 50)
        pdf.cell(55, 6, label)
    pdf.set_line_width(0.2)
    pdf.set_draw_color(0, 0, 0)


def phase_detail_page(pdf: PhasesPDF, phase: dict):
    pdf.add_page()
    color = phase["color"]
    status = phase["status"]

    # Phase header bar
    pdf.set_fill_color(*color)
    pdf.rect(0, 14, 210, 16, "F")
    pdf.set_font("Helvetica", "B", 14)
    pdf.set_text_color(*WHITE)
    pdf.set_y(17)
    pdf.cell(0, 8, f"{phase['number']}  -  {phase['name']}  ({phase['days']})", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Status pill
    status_bg = {
        "Done": GREEN, "Next": ACCENT, "Upcoming": ORANGE, "Future": MID_GRAY
    }.get(status, MID_GRAY)
    pdf.set_fill_color(*status_bg)
    pdf.set_font("Helvetica", "B", 8)
    sw = 30
    pdf.set_xy((210 - sw) / 2, pdf.get_y() + 2)
    pdf.cell(sw, 6, status, fill=True, align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.ln(6)

    # Objective
    pdf.subsection("Objective")
    pdf.body(phase["objective"])

    # Files to create
    pdf.subsection("Files to Create")
    for f in phase["files"]:
        pdf.bullet(f)

    # Build tasks
    pdf.subsection("Step-by-Step Build Tasks")
    for i, task in enumerate(phase["tasks"]):
        pdf.set_x(14)
        pdf.set_fill_color(*LIGHT_GRAY)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(*color)
        pdf.cell(7, 5.5, str(i + 1), border=1, fill=True, align="C")
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(30, 30, 30)
        pdf.set_fill_color(*WHITE if i % 2 != 0 else LIGHT_GRAY)
        pdf.cell(169, 5.5, task, border=1, fill=True)
        pdf.ln()
    pdf.set_text_color(0, 0, 0)
    pdf.ln(3)

    # Done when
    pdf.subsection("Definition of Done")
    for criterion in phase["done_when"]:
        pdf.set_x(14)
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*GREEN)
        pdf.cell(6, 5, "[OK]")
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(30, 30, 30)
        pdf.multi_cell(0, 5, criterion, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_text_color(0, 0, 0)
    pdf.ln(2)

    # Test command
    pdf.set_fill_color(*DARK_BLUE)
    pdf.rect(10, pdf.get_y(), 190, 10, "F")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*WHITE)
    pdf.set_x(14)
    pdf.cell(30, 10, "Verify with:")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color((100, 200, 255))
    pdf.cell(0, 10, phase["test_cmd"])
    pdf.set_text_color(0, 0, 0)
    pdf.ln(14)


def what_to_build_next_page(pdf: PhasesPDF):
    pdf.add_page()
    pdf.section_title("What to Build Next  -  Phase 3 Action Plan")

    pdf.body(
        "Phases 1 and 2 are complete. Phase 3 is the intellectual core of ReviewMind: "
        "parsing raw unified diffs into structured SemanticChunks using unidiff + Python AST. "
        "Follow the tasks in order - each one builds on the last."
    )

    pdf.subsection("Before You Start Phase 3")
    prereqs = [
        "Confirm Phase 2 tests pass: pytest tests/test_github_client.py -v  ->  12 passed",
        "Install new dependency: pip install unidiff",
        "Collect 3 fixture .diff files: one new function, one bug fix, one config change",
        "Understand Python ast module: ast.parse(), ast.walk(), FunctionDef, ClassDef nodes",
        "Read unidiff docs: PatchSet, PatchedFile, Hunk, Line (is_added / is_removed / is_context)",
    ]
    for p in prereqs:
        pdf.bullet(p)

    pdf.ln(3)
    pdf.subsection("Phase 3 Task Checklist  (Days 5-6)")

    tasks_with_context = [
        ("pip install unidiff && add to pyproject.toml dependencies",
         "unidiff library parses unified diff strings into PatchSet -> PatchedFile -> Hunk -> Line objects"),
        ("Create reviewmind/engine/__init__.py",
         "Empty file - marks engine/ as a package"),
        ("Write engine/models.py - SemanticChunk Pydantic model",
         "Fields: file_path, start_line, end_line, chunk_type (function/class/module), classification, complexity, content, diff_lines"),
        ("Write engine/models.py - FileDiff + Hunk models",
         "FileDiff: filename, change_type (added/modified/deleted/renamed), hunks[]. Hunk: old_start, new_start, lines[(type, content)]"),
        ("Write engine/diff_parser.py - parse_diff(raw_diff: str) -> list[FileDiff]",
         "Use unidiff.PatchSet.from_string(raw_diff). Map PatchedFile -> FileDiff, Hunk -> Hunk model"),
        ("Detect change_type from PatchedFile.is_added_file / is_removed_file / is_rename",
         "Renamed files: PatchedFile.source_file != PatchedFile.target_file"),
        ("Write engine/chunker.py - map hunks to AST nodes",
         "For each changed .py file: fetch full source via GitHubRepository.get_file_content(), run ast.parse()"),
        ("Walk AST to find FunctionDef/AsyncFunctionDef/ClassDef per changed line range",
         "ast.walk() + node.lineno/end_lineno. If hunk lines overlap with node range -> assign chunk to that node"),
        ("Merge hunks that touch the same function into one SemanticChunk",
         "Group by (file_path, function_name). One chunk per function even if 3 separate hunks touch it"),
        ("Handle module-level code with no enclosing function",
         "chunk_type='module', name='<module>'. Use this when no FunctionDef/ClassDef contains the changed lines"),
        ("Write engine/classifier.py - classify each chunk",
         "new_feature: function did not exist in old file (added). bug_fix: modified + file has 'fix'/'bug' in name or commit msg. refactor: modified, no logic change (rename/format). test: file is in tests/. config: .yaml/.toml/.env"),
        ("Write engine/complexity.py - cyclomatic complexity per function",
         "complexity = 1 + count of: if, elif, for, while, except, and, or, with keywords in chunk.content"),
        ("Write services/analysis/from_paste.py",
         "Takes a code string + optional filename -> wraps as CodeInput(source='paste', files=[{filename, content}])"),
        ("Write services/analysis/from_upload.py",
         "Takes list of (filename, bytes) -> decodes -> returns CodeInput(source='upload', files=[...])"),
        ("Collect fixture diffs in tests/fixtures/diffs/",
         "new_function.diff, bug_fix.diff, config_change.diff - use real diffs from your GitHub test repo"),
        ("Write tests/test_diff_parser.py",
         "Given fixture diff -> assert correct FileDiff count, hunk boundaries, added/removed line counts"),
        ("Write tests/test_chunker.py",
         "Given fixture diff + mocked file content -> assert SemanticChunks with correct line ranges, function names, chunk_types"),
        ("Verify complexity score on 3 hand-checked examples",
         "Count branches manually, compare to complexity() output. Off-by-one errors are common here"),
    ]

    for i, (task, context) in enumerate(tasks_with_context):
        shade = i % 2 == 0
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        pdf.set_draw_color(*MID_GRAY)
        pdf.set_line_width(0.2)

        # Checkbox
        pdf.set_x(10)
        pdf.set_fill_color(*WHITE)
        pdf.cell(7, 10, "[ ]", border=1, fill=True, align="C")

        # Task + context
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(*DARK_BLUE)
        pdf.cell(173, 5, task, border="TR", fill=True)
        pdf.ln()
        pdf.set_x(17)
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(*MID_GRAY)
        pdf.cell(173, 5, context, border="BR", fill=True)
        pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.set_draw_color(0, 0, 0)

    # Bottom tip
    pdf.ln(3)
    pdf.set_fill_color(*LIGHT_BLUE)
    pdf.set_draw_color(*ACCENT)
    pdf.rect(10, pdf.get_y(), 190, 14, "FD")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*DARK_BLUE)
    pdf.set_xy(14, pdf.get_y() + 2)
    pdf.cell(0, 5, "Tip: non-Python files (JS, YAML, etc.) skip AST chunking - use line-range chunks only.")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(14, pdf.get_y() + 7)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 5, "Only .py files get AST mapping. For all other extensions, one SemanticChunk per hunk with chunk_type='raw'.")
    pdf.set_draw_color(0, 0, 0)
    pdf.set_text_color(0, 0, 0)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def generate():
    pdf = PhasesPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(10, 14, 10)

    cover_page(pdf)
    progress_overview_page(pdf)
    file_tree_page(pdf)

    for phase in PHASES:
        phase_detail_page(pdf, phase)

    what_to_build_next_page(pdf)

    pdf.output(OUTPUT_PATH)
    print(f"[OK]  PDF generated: {OUTPUT_PATH}  ({pdf.page} pages)")


if __name__ == "__main__":
    generate()
