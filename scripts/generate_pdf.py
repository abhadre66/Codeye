#!/usr/bin/env python3
"""
ReviewMind Project Documentation Generator
═══════════════════════════════════════════
Run:  python scripts/generate_pdf.py
Output: ReviewMind_Project_Overview.pdf

To update the PDF - edit any section below and re-run.
Every constant / list / dict is a content block you can change.
"""

from fpdf import FPDF
from fpdf.enums import XPos, YPos
from datetime import date

OUTPUT_PATH = "ReviewMind_Project_Overview.pdf"

# Sanitize any string so fpdf's latin-1 Helvetica font never chokes
_CHAR_MAP = {
    "—": "-",   # em dash
    "–": "-",   # en dash
    "’": "'",   # right single quote
    "‘": "'",   # left single quote
    "“": '"',   # left double quote
    "”": '"',   # right double quote
    "…": "...", # ellipsis
    "•": "-",   # bullet
    "→": "->",  # right arrow
    "←": "<-",  # left arrow
    "⇒": "=>",  # right double arrow
    "♥": "<3",  # heart (just in case)
    " ": " ",   # non-breaking space
    "≤": "<=",
    "≥": ">=",
    "∞": "inf",
    "≠": "!=",
}

def s(text: str) -> str:
    """Return text safe for fpdf Helvetica (latin-1)."""
    for char, replacement in _CHAR_MAP.items():
        text = text.replace(char, replacement)
    return text.encode("latin-1", errors="replace").decode("latin-1")

# ─────────────────────────────────────────────────────────────────────────────
# COLORS  (R, G, B)
# ─────────────────────────────────────────────────────────────────────────────
DARK_BLUE   = (10,  25,  60)
ACCENT      = (37,  99, 235)
LIGHT_BLUE  = (219, 234, 254)
LIGHT_GRAY  = (245, 247, 250)
MID_GRAY    = (150, 158, 172)
WHITE       = (255, 255, 255)
GREEN       = (22, 163,  74)
ORANGE      = (234, 88,  12)
RED         = (220,  38,  38)
YELLOW_BG   = (254, 249, 195)
YELLOW_TEXT = (133,  77,  14)

# ─────────────────────────────────────────────────────────────────────────────
# CONTENT  <- edit this section to update the PDF
# ─────────────────────────────────────────────────────────────────────────────

PROJECT_NAME    = "ReviewMind"
PROJECT_TAGLINE = "AI-Native Code Review Platform"
PROJECT_VERSION = "v0.1  -  MVP Phase"

PROBLEM_STATEMENT = (
    "Code review is one of the highest-leverage, highest-friction activities in "
    "software engineering. Reviewers must understand the intent of a change, spot "
    "security issues, enforce style conventions, and do all of this repeatedly across "
    "many PRs - often under time pressure. Most existing tools (linters, CI bots) "
    "operate in isolation and don't understand context."
)

SOLUTION_STATEMENT = (
    "ReviewMind is an AI-native code review co-pilot. It connects to GitHub, "
    "understands the semantic structure of a diff, runs security and style checks, "
    "and drafts high-quality review comments - all accessible from your own frontend "
    "via the Claude API and the Model Context Protocol (MCP)."
)

TECH_STACK = [
    # (Component, Technology, Purpose)
    ("AI Brain",       "Claude API (claude-sonnet-4-6)", "Decides which tools to call, synthesizes final review"),
    ("Tool Protocol",  "MCP (HTTP/SSE transport)",       "Standard interface between Claude and ReviewMind tools"),
    ("API Layer",      "FastAPI + Uvicorn",              "HTTP endpoints, webhook receiver, MCP client loop"),
    ("Frontend",       "React / Next.js (planned)",      "Chat UI, code paste box, file upload, findings display"),
    ("GitHub",         "GitHub REST API + httpx",        "Fetch PRs, diffs, blame, post review comments"),
    ("Cache",          "Redis",                          "Cache GitHub responses, avoid rate limits"),
    ("Database",       "PostgreSQL + SQLAlchemy async",  "Store PRs, findings, review history"),
    ("Migrations",     "Alembic",                        "Schema versioning"),
    ("Agent Protocol", "A2A (planned)",                  "Parallel sub-agents: security, style, diff"),
]

MCP_TOOLS = [
    # (Tool Name, Input, Purpose, Auth Required, Status)
    # ── GitHub PR tools ───────────────────────────────────────────────────────
    ("get_pr_summary",          "owner, repo, pr_number",           "PR metadata: title, author, state, files changed",      "No",  "Planned"),
    ("get_pr_context",          "owner, repo, pr_number",           "Related files, commit history, linked issues",           "No",  "Planned"),
    ("analyze_diff",            "owner, repo, pr_number",           "Parse diff into semantic chunks (functions/classes)",    "No",  "Planned"),
    ("check_security_issues",   "owner, repo, pr_number",           "Scan for secrets, SQL injection, unsafe patterns",      "No",  "Planned"),
    ("check_style_violations",  "owner, repo, pr_number",           "Enforce reviewmind.yaml project conventions",           "No",  "Planned"),
    ("check_dependency_changes","owner, repo, pr_number",           "Cross-check added packages against OSV vuln DB",        "No",  "Planned"),
    ("get_pr_diff_file",        "owner, repo, pr_number, path",     "Full file content for deep context on a specific file", "No",  "Planned"),
    ("suggest_reviewers",       "owner, repo, pr_number",           "Blame-based reviewer suggestions + CODEOWNERS",         "No",  "Planned"),
    ("generate_review_comment", "owner, repo, pr_number",           "Assemble findings into structured draft review",        "No",  "Planned"),
    ("post_review",             "owner, repo, pr_number, body ...", "Post review to GitHub (APPROVE / REQUEST_CHANGES)",     "Yes", "Planned"),
    # ── Paste / Upload tools (no auth for read, auth for write) ──────────────
    ("detect_language",         "code, filename?",                  "Detect programming language - runs before all analysis","No",  "Planned"),
    ("explain_code",            "code, filename",                   "Plain-English explanation of what the code does",       "No",  "Planned"),
    ("review_code",             "code: str, filename?: str",        "Full security+style analysis on pasted code snippet",   "No",  "Planned"),
    ("review_file",             "files: [{filename, content}]",     "Analyse one or more uploaded files, results per file",  "No",  "Planned"),
    ("suggest_fix",             "finding_id, code, language",       "Suggest a concrete fix for one specific finding",       "No",  "Planned"),
    ("apply_fix",               "finding_id, code, confirmed:bool", "Apply a suggested fix - requires user confirmation",    "Yes", "Planned"),
    # ── Utility tools ─────────────────────────────────────────────────────────
    ("explain_finding",         "rule_id",                          "Detailed explanation + examples for a specific rule",   "No",  "Planned"),
    ("get_analysis_history",    "owner, repo",                      "Past findings for this repo - track regressions",      "No",  "Planned"),
    ("ping",                    "-",                                "Health-check: verify MCP server is reachable",          "No",  "Done [DONE]"),
]

DB_TABLES = [
    # (Table, Key Columns, Purpose)
    ("repositories", "id, owner, name, default_branch, config_yaml",                  "Anchor entity - every repo ReviewMind has seen"),
    ("pull_requests", "id, repository_id, pr_number, title, author, state, head_sha", "Cached PR metadata + invalidation key (head_sha)"),
    ("diff_chunks",   "id, pull_request_id, file_path, chunk_type, content",          "Semantic chunks from Diff Engine - reused by scanners"),
    ("findings",      "id, pull_request_id, category, rule_id, severity, file, line", "All security + style findings (audit trail)"),
    ("reviews",       "id, pull_request_id, github_review_id, event, html_url",       "Every review ReviewMind has posted to GitHub"),
]

BUILD_STATUS = [
    # (Item, Status, Notes)
    ("Docker Compose (Postgres + Redis)",    "Done [DONE]",    "docker compose up starts both services"),
    ("Core config + structured logging",     "Done [DONE]",    "core/config.py, core/logging.py"),
    ("FastAPI app + /health endpoint",       "Done [DONE]",    "Checks DB + Redis connectivity"),
    ("SQLAlchemy async models + Alembic",    "Done [DONE]",    "5 tables designed, migration created"),
    ("Redis cache client",                   "Done [DONE]",    "core/cache.py wired to FastAPI"),
    ("MCP server (ping tool)",               "Done [DONE]",    "mcp_server.py - placeholder tool working"),
    ("GitHub HTTP client",                   "Pending",   "Phase 2 - httpx client with auth + ETags"),
    ("Redis cache-aside for GitHub calls",   "Pending",   "Phase 2 - TTL strategy per Section 10"),
    ("Semantic Diff Engine",                 "Pending",   "Phase 3 - unidiff + AST chunking"),
    ("Security Analysis Engine",             "Pending",   "Phase 4 - 5 rules (secrets, SQLi, etc.)"),
    ("Style Analysis Engine",                "Pending",   "Phase 5 - reviewmind.yaml rule engine"),
    ("All 16 MCP tools wired",              "Pending",   "Phase 6 - tools call Service Layer"),
    ("Claude API tool loop in FastAPI",      "Pending",   "Phase 6 - /chat endpoint"),
    ("Frontend (React/Next.js)",             "Pending",   "Phase 7 - chat UI + code paste + upload"),
    ("A2A parallel sub-agents",             "Pending",   "Phase 8 - security/style agents in parallel"),
]

SECURITY_RULES = [
    ("SEC001", "Hardcoded Secret",        "High",     "Regex scan added lines for API keys, tokens, private key headers"),
    ("SEC002", "SQL Injection",           "Critical", "f-string / .format() / % used in DB execute() calls"),
    ("SEC003", "Insecure Dependency",     "Medium",   "Added package versions cross-checked against OSV.dev snapshot"),
    ("SEC004", "Missing Input Validation","Low",      "Request handler params used in file/DB/subprocess without guard"),
    ("SEC005", "Unsafe Deserialization",  "High",     "pickle.load, yaml.load (no SafeLoader), eval, exec, shell=True"),
]

STYLE_RULES = [
    ("STY001", "Max Function Length",  "Configurable", "Function exceeds max_function_length lines in reviewmind.yaml"),
    ("STY002", "Missing Docstring",    "Configurable", "Public function/class has no docstring"),
    ("STY003", "Naming Convention",    "Configurable", "Identifier doesn't match snake_case / PascalCase regex"),
    ("STY004", "Forbidden Import",     "Configurable", "Import matches a forbidden pattern (e.g. 'from x import *')"),
    ("STY005", "Max Line Length",      "Configurable", "Line exceeds max_line_length characters"),
    ("STY006", "TODO without ticket",  "Info",         "TODO/FIXME comment has no issue reference"),
]

ROADMAP = [
    ("Phase 1", "Foundation",           "Done [DONE]",  "Docker, DB, Redis, FastAPI, MCP skeleton"),
    ("Phase 2", "GitHub Client",        "Next",    "httpx client, rate limiting, Redis caching, pagination"),
    ("Phase 3", "Diff Engine",          "Upcoming","unidiff parsing, AST chunking, classification, complexity"),
    ("Phase 4", "Security Engine",      "Upcoming","5 security rules, rule registry pattern"),
    ("Phase 5", "Style Engine",         "Upcoming","reviewmind.yaml, built-in style rules"),
    ("Phase 6", "MCP + Claude API",     "Upcoming","All 16 tools wired, /chat endpoint with tool loop"),
    ("Phase 7", "Frontend",             "Upcoming","React/Next.js chat UI, paste box, file upload"),
    ("Phase 8", "A2A Agents",           "Future",  "Parallel sub-agents for security/style/diff"),
    ("Month 2", "GitHub App + PyPI",    "Future",  "OAuth, GitHub App install, pip install reviewmind"),
    ("Month 3", "SaaS Platform",        "Future",  "Multi-tenant, billing, web dashboard, Redis Cluster"),
]

# ─────────────────────────────────────────────────────────────────────────────
# PDF CLASS
# ─────────────────────────────────────────────────────────────────────────────

class ReviewMindPDF(FPDF):

    # Override cell/multi_cell to auto-sanitize every string passed in
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
        self.cell(0, 4, f"{PROJECT_NAME} - {PROJECT_TAGLINE}", align="C")
        self.set_text_color(0, 0, 0)
        self.set_y(14)

    def footer(self):
        if self.page_no() == 1:
            return
        self.set_y(-11)
        self.set_font("Helvetica", "", 7)
        self.set_text_color(*MID_GRAY)
        self.cell(0, 5, f"Page {self.page_no()}  |  Generated {date.today().strftime('%B %d, %Y')}  |  Confidential", align="C")
        self.set_text_color(0, 0, 0)

    # ── Typography helpers ────────────────────────────────────────────────────

    def section_title(self, title: str):
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

    def subsection(self, title: str):
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

    def body(self, text: str):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(40, 40, 40)
        self.multi_cell(190, 5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)
        self.ln(1)

    def bullet(self, text: str, indent: int = 14, color=None):
        self.set_font("Helvetica", "", 9)
        self.set_text_color(*(color or (40, 40, 40)))
        self.set_x(indent)
        self.cell(5, 5, "-")
        self.set_x(indent + 5)
        self.multi_cell(185 - indent, 5, text, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.set_text_color(0, 0, 0)

    def badge(self, x: float, y: float, text: str, bg: tuple, fg: tuple = WHITE):
        self.set_fill_color(*bg)
        self.set_text_color(*fg)
        self.set_font("Helvetica", "B", 7)
        self.set_xy(x, y)
        self.cell(26, 5, text, fill=True, align="C")
        self.set_text_color(0, 0, 0)

    # ── Table helpers ────────────────────────────────────────────────────────

    def tbl_header(self, cols: list):
        self.set_fill_color(*DARK_BLUE)
        self.set_text_color(*WHITE)
        self.set_font("Helvetica", "B", 8)
        for label, w in cols:
            self.cell(w, 7, label, border=1, fill=True, align="C")
        self.ln()
        self.set_text_color(0, 0, 0)

    def tbl_row(self, cells: list, shade: bool = False):
        if shade:
            self.set_fill_color(*LIGHT_GRAY)
        else:
            self.set_fill_color(*WHITE)
        self.set_font("Helvetica", "", 8)
        for val, w in cells:
            self.cell(w, 6, str(val), border=1, fill=True)
        self.ln()

    # ── Flowchart primitives ─────────────────────────────────────────────────

    def flow_box(self, x, y, w, h, text, fill=LIGHT_BLUE, txt_color=DARK_BLUE, bold=False):
        self.set_fill_color(*fill)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.3)
        self.rect(x, y, w, h, "FD")
        self.set_font("Helvetica", "B" if bold else "", 8)
        self.set_text_color(*txt_color)
        lines = text.split("\n")
        line_h = h / len(lines)
        for i, line in enumerate(lines):
            self.set_xy(x, y + i * line_h + (line_h - 4) / 2)
            self.cell(w, 4, line, align="C")
        self.set_text_color(0, 0, 0)
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.2)

    def flow_diamond(self, x, y, w, h, text):
        cx, cy = x + w / 2, y + h / 2
        self.set_fill_color(*YELLOW_BG)
        self.set_draw_color(*ACCENT)
        self.set_line_width(0.3)
        self.polygon(
            [(cx, y), (x + w, cy), (cx, y + h), (x, cy)], style="FD"
        )
        self.set_font("Helvetica", "B", 7)
        self.set_text_color(*YELLOW_TEXT)
        self.set_xy(x, cy - 3)
        self.cell(w, 6, text, align="C")
        self.set_text_color(0, 0, 0)
        self.set_draw_color(0, 0, 0)
        self.set_line_width(0.2)

    def flow_arrow(self, x, y, length=6, label=""):
        self.set_draw_color(*MID_GRAY)
        self.set_line_width(0.3)
        self.line(x, y, x, y + length - 2)
        self.line(x, y + length, x - 2, y + length - 3)
        self.line(x, y + length, x + 2, y + length - 3)
        if label:
            self.set_font("Helvetica", "I", 7)
            self.set_text_color(*MID_GRAY)
            self.set_xy(x + 3, y + length / 2 - 2)
            self.cell(30, 4, label)
        self.set_draw_color(0, 0, 0)
        self.set_text_color(0, 0, 0)
        self.set_line_width(0.2)

    def flow_arrow_right(self, x, y, length=10, label=""):
        self.set_draw_color(*MID_GRAY)
        self.set_line_width(0.3)
        self.line(x, y, x + length - 2, y)
        self.line(x + length, y, x + length - 3, y - 2)
        self.line(x + length, y, x + length - 3, y + 2)
        if label:
            self.set_font("Helvetica", "I", 7)
            self.set_text_color(*MID_GRAY)
            self.set_xy(x, y - 5)
            self.cell(length, 4, label, align="C")
        self.set_draw_color(0, 0, 0)
        self.set_text_color(0, 0, 0)
        self.set_line_width(0.2)

    def flow_label(self, x, y, text, color=MID_GRAY):
        self.set_font("Helvetica", "I", 7)
        self.set_text_color(*color)
        self.set_xy(x, y)
        self.cell(40, 4, text)
        self.set_text_color(0, 0, 0)


# ─────────────────────────────────────────────────────────────────────────────
# PAGE BUILDERS
# ─────────────────────────────────────────────────────────────────────────────

def cover_page(pdf: ReviewMindPDF):
    pdf.add_page()
    # Full dark background
    pdf.set_fill_color(*DARK_BLUE)
    pdf.rect(0, 0, 210, 297, "F")

    # Accent bar
    pdf.set_fill_color(*ACCENT)
    pdf.rect(0, 110, 210, 4, "F")

    # Project name
    pdf.set_font("Helvetica", "B", 36)
    pdf.set_text_color(*WHITE)
    pdf.set_y(68)
    pdf.cell(0, 14, PROJECT_NAME, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Tagline
    pdf.set_font("Helvetica", "", 14)
    pdf.set_text_color(180, 200, 240)
    pdf.set_y(86)
    pdf.cell(0, 8, PROJECT_TAGLINE, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Version
    pdf.set_font("Helvetica", "", 10)
    pdf.set_text_color(*MID_GRAY)
    pdf.set_y(119)
    pdf.cell(0, 6, PROJECT_VERSION, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

    # Key pills
    pills = ["MCP Protocol", "Claude API", "FastAPI", "PostgreSQL", "Redis", "A2A Agents", "GitHub API"]
    pill_w = 26
    total = len(pills) * (pill_w + 3) - 3
    start_x = (210 - total) / 2
    py = 140
    for i, pill in enumerate(pills):
        px = start_x + i * (pill_w + 3)
        pdf.set_fill_color(*ACCENT)
        pdf.set_draw_color(*ACCENT)
        pdf.rect(px, py, pill_w, 7, "FD")
        pdf.set_font("Helvetica", "B", 6)
        pdf.set_text_color(*WHITE)
        pdf.set_xy(px, py + 1.5)
        pdf.cell(pill_w, 4, pill, align="C")

    # Date
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(*MID_GRAY)
    pdf.set_y(270)
    pdf.cell(0, 6, f"Generated: {date.today().strftime('%B %d, %Y')}", align="C")

    pdf.set_text_color(0, 0, 0)


def overview_page(pdf: ReviewMindPDF):
    pdf.add_page()
    pdf.section_title("1.  Project Overview")

    pdf.subsection("Problem")
    pdf.body(PROBLEM_STATEMENT)

    pdf.subsection("Solution")
    pdf.body(SOLUTION_STATEMENT)

    pdf.subsection("Why This Architecture?")
    points = [
        "MCP (Model Context Protocol) decouples the AI interface from the business logic - the same tools work in Claude Desktop, your own frontend, or any future MCP-compatible client.",
        "Claude API handles the reasoning: it decides which tools to call and in what order based on the user's natural-language input.",
        "FastAPI acts as both the MCP client (executing tool calls) and the HTTP API (webhooks, future SaaS endpoints).",
        "A2A (Agent-to-Agent) enables parallel sub-agents - security, style, and diff engines can run concurrently, reducing review time on large PRs.",
        "Redis + Postgres separation: Redis caches volatile GitHub API responses (short TTL), Postgres stores canonical audit data (findings, reviews, history).",
    ]
    for p in points:
        pdf.bullet(p)

    pdf.subsection("Core User Workflow")
    steps = [
        '1.  User opens your frontend and types: "Review PR #42 on abhishek/my-repo"',
        "2.  Frontend sends the message to FastAPI backend  ->  backend passes it to Claude API with tool definitions",
        "3.  Claude decides: call get_pr_summary -> analyze_diff -> check_security_issues + check_style_violations (parallel)",
        "4.  Backend executes each tool via MCP  ->  MCP server calls GitHub API, runs engines, returns findings",
        "5.  Claude synthesizes all findings into a structured natural-language review",
        '6.  User: "Post this as a review"  ->  Claude calls post_review  ->  comment appears on GitHub PR',
    ]
    for s in steps:
        pdf.bullet(s)

    pdf.ln(3)
    pdf.subsection("Tech Stack")
    cols = [("Component", 38), ("Technology", 70), ("Purpose", 82)]
    pdf.tbl_header(cols)
    for i, (comp, tech, purpose) in enumerate(TECH_STACK):
        pdf.tbl_row([(comp, 38), (tech, 70), (purpose, 82)], shade=i % 2 == 0)


def architecture_flow_page(pdf: ReviewMindPDF):
    pdf.add_page()
    pdf.section_title("2.  Architecture - System Layers")

    pdf.body(
        "Five layers, each with one job. No layer knows about the internals of another - "
        "they communicate only through declared interfaces. This is the 'ports & adapters' "
        "pattern that makes every layer independently testable and replaceable."
    )

    # Draw system layer diagram
    # Centered column
    cx = 105
    bw = 90    # box width
    bh = 11    # box height
    bx = cx - bw / 2
    gap = 7    # arrow gap

    layers = [
        ("Your Frontend  (React / Next.js)",                  LIGHT_BLUE,   DARK_BLUE),
        ("FastAPI Backend  (MCP Client + Claude API loop)",   (219,234,254),DARK_BLUE),
        ("MCP Server  (Tool Registry + HTTP/SSE transport)",  (220,252,231),(21,128,61)),
        ("Service Layer  (GitHub Client, Diff, Security, Style)", (254,249,195), YELLOW_TEXT),
        ("Data Layer  (PostgreSQL  +  Redis Cache)",           (254,226,226),(185,28,28)),
    ]

    start_y = pdf.get_y() + 4
    arrow_labels = [
        "POST /chat",
        "tools/list  +  tools/call",
        "calls service functions",
        "reads / writes",
    ]

    for i, (name, fill, txtc) in enumerate(layers):
        y = start_y + i * (bh + gap)
        pdf.flow_box(bx, y, bw, bh, name, fill=fill, txt_color=txtc, bold=True)
        if i < len(layers) - 1:
            ay = y + bh
            pdf.flow_arrow(cx, ay, gap, label=arrow_labels[i])

    # Side annotations
    ann_x = bx + bw + 4
    ann_y = start_y
    annotations = [
        "Chat UI, code paste, file upload",
        "Orchestrates Claude <-> MCP tool loop",
        "Executes tools, shields Service Layer from protocol",
        "Pure business logic - no MCP / HTTP types",
        "Cache-aside pattern, short TTL for open PRs",
    ]
    for i, ann in enumerate(annotations):
        ay = ann_y + i * (bh + gap) + 3
        pdf.set_font("Helvetica", "I", 7)
        pdf.set_text_color(*MID_GRAY)
        pdf.set_xy(ann_x, ay)
        pdf.cell(55, 4, ann)

    pdf.set_text_color(0, 0, 0)
    pdf.set_y(start_y + len(layers) * (bh + gap) + 4)

    pdf.subsection("External Systems")
    ext = [
        ("GitHub REST API",    "Source of truth for PRs, diffs, files, blame, reviews"),
        ("Claude API",         "AI reasoning - decides tool call order, synthesizes review"),
        ("OSV.dev (planned)",  "Live vulnerability database for dependency scanning"),
    ]
    cols = [("System", 50), ("Role", 140)]
    pdf.tbl_header(cols)
    for i, (sys, role) in enumerate(ext):
        pdf.tbl_row([(sys, 50), (role, 140)], shade=i % 2 == 0)


def pr_review_flow_page(pdf: ReviewMindPDF):
    pdf.add_page()
    pdf.section_title("3.  Flow: Reviewing a GitHub PR")

    pdf.body(
        'Triggered when the user types something like "Review PR #42 on abhishek/my-repo". '
        "Claude decides the tool sequence autonomously - ReviewMind just executes what Claude asks for."
    )

    # ── Swimlane headers ─────────────────────────────────────────────────────
    lanes = ["User /\nFrontend", "FastAPI\nBackend", "Claude\nAPI", "MCP\nServer", "GitHub\n/ Redis"]
    lw = 36
    lh = 12
    lx = 12
    ly = pdf.get_y() + 2

    for i, lane in enumerate(lanes):
        x = lx + i * lw
        pdf.set_fill_color(*DARK_BLUE)
        pdf.set_draw_color(*ACCENT)
        pdf.set_line_width(0.3)
        pdf.rect(x, ly, lw, lh, "FD")
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*WHITE)
        lines = lane.split("\n")
        for j, ln in enumerate(lines):
            pdf.set_xy(x, ly + 1.5 + j * 4.5)
            pdf.cell(lw, 4, ln, align="C")
        pdf.set_text_color(0, 0, 0)
        pdf.set_draw_color(0, 0, 0)
        pdf.set_line_width(0.2)

    # ── Vertical lane dividers (light) ───────────────────────────────────────
    total_h = 168
    for i in range(len(lanes) + 1):
        x = lx + i * lw
        pdf.set_draw_color(220, 225, 235)
        pdf.set_line_width(0.1)
        pdf.line(x, ly + lh, x, ly + lh + total_h)
    pdf.set_line_width(0.2)
    pdf.set_draw_color(0, 0, 0)

    # ── Steps ─────────────────────────────────────────────────────────────────
    # Each step: (row_offset, from_lane, to_lane, label, detail, arrow_color)
    row_h = 16
    base_y = ly + lh + 4

    def lane_cx(idx): return lx + idx * lw + lw / 2  # center x of lane idx

    steps = [
        # (y_offset, x1_lane, x2_lane, msg, note)
        (0,   0, 1, "POST /chat  { message, repo, pr_number }",   "HTTP request"),
        (1,   1, 2, "messages.create(tools=[...], messages=[...])", "Claude API call"),
        (2,   2, 1, 'tool_use: "get_pr_summary"',                  "Claude decides first tool"),
        (3,   1, 3, "tools/call  get_pr_summary",                   "MCP call"),
        (4,   3, 4, "GET /repos/.../pulls/42",                      "GitHub API + Redis cache"),
        (5,   4, 3, "{ title, author, state, files_changed }",      "PR metadata returned"),
        (6,   3, 1, "tool_result: pr_summary",                      "MCP result"),
        (7,   1, 2, "messages with tool_result",                    "send result back to Claude"),
        (8,   2, 1, 'tool_use: "analyze_diff"',                     "Claude picks next tool"),
        (9,   1, 3, "tools/call  analyze_diff",                     "MCP call"),
        (10,  3, 4, "GET diff  ->  AST parse  ->  SemanticChunks",    "Diff Engine runs"),
    ]

    for y_off, l1, l2, msg, note in steps:
        y = base_y + y_off * row_h
        x1 = lane_cx(l1)
        x2 = lane_cx(l2)
        mid_y = y + 5

        # Horizontal arrow
        pdf.set_draw_color(*ACCENT)
        pdf.set_line_width(0.4)
        if x1 < x2:
            pdf.line(x1, mid_y, x2 - 2, mid_y)
            pdf.line(x2, mid_y, x2 - 3, mid_y - 2)
            pdf.line(x2, mid_y, x2 - 3, mid_y + 2)
        else:
            pdf.line(x1, mid_y, x2 + 2, mid_y)
            pdf.line(x2, mid_y, x2 + 3, mid_y - 2)
            pdf.line(x2, mid_y, x2 + 3, mid_y + 2)
        pdf.set_draw_color(0, 0, 0)
        pdf.set_line_width(0.2)

        # Message label
        pdf.set_font("Helvetica", "B", 6)
        pdf.set_text_color(*DARK_BLUE)
        mx = min(x1, x2) + 1
        mw = abs(x2 - x1) - 2
        pdf.set_xy(mx, mid_y - 5)
        pdf.cell(mw, 4, msg, align="C")

        # Note
        pdf.set_font("Helvetica", "I", 6)
        pdf.set_text_color(*MID_GRAY)
        pdf.set_xy(mx, mid_y + 1)
        pdf.cell(mw, 3, note, align="C")

    pdf.set_text_color(0, 0, 0)

    # ── Continuation note ────────────────────────────────────────────────────
    cont_y = base_y + len(steps) * row_h + 2
    pdf.set_fill_color(*YELLOW_BG)
    pdf.set_draw_color(*ACCENT)
    pdf.rect(lx, cont_y, lw * len(lanes), 10, "FD")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*YELLOW_TEXT)
    pdf.set_xy(lx, cont_y + 2)
    pdf.cell(lw * len(lanes), 6,
             "->  check_security_issues + check_style_violations called IN PARALLEL  ->  Claude synthesizes  ->  response to frontend",
             align="C")
    pdf.set_text_color(0, 0, 0)
    pdf.set_draw_color(0, 0, 0)


def paste_flow_page(pdf: ReviewMindPDF):
    pdf.add_page()
    pdf.section_title("4.  Flow: Reviewing Pasted Code")

    pdf.body(
        "Triggered when the user pastes a code snippet directly into the frontend. "
        "No GitHub API calls - everything happens locally. One MCP tool call does the full analysis."
    )

    pdf.subsection("Comparison: PR Review vs Pasted Code")
    cols = [("Aspect", 55), ("PR Review", 67), ("Pasted Code", 68)]
    pdf.tbl_header(cols)
    rows = [
        ("Input source",      "GitHub PR number",                "Raw code string + optional filename"),
        ("GitHub API calls",  "Yes (PR metadata, diff, files)",  "None"),
        ("Redis caching",     "Yes - saves GitHub rate limits",  "None (stateless, one-off)"),
        ("Postgres storage",  "Yes - PR, chunks, findings",      "None - ephemeral result"),
        ("MCP tools called",  "4–6 tools per review",            "1 tool: review_code"),
        ("Diff parsing",      "Yes - only changed lines",        "No - whole file in scope"),
        ("Speed",             "Slower (network round-trips)",    "Fast (pure local analysis)"),
        ("Use case",          "Team code review workflow",       "Quick one-off snippet check"),
    ]
    for i, row in enumerate(rows):
        pdf.tbl_row([(v, [55,67,68][j]) for j,v in enumerate(row)], shade=i%2==0)

    pdf.ln(4)
    pdf.subsection("Step-by-Step Flow")

    flow_steps = [
        ("User",        "Pastes code in text area  +  clicks Review",              LIGHT_BLUE,   DARK_BLUE),
        ("Frontend",    'POST /chat  { message, code, filename }',                  LIGHT_BLUE,   DARK_BLUE),
        ("Claude API",  "Sees pasted code in message -> decides: call review_code",  (220,252,231),(21,128,61)),
        ("MCP Server",  "tools/call  review_code({ code, filename })",              (220,252,231),(21,128,61)),
        ("Engine",      "Wrap -> CodeInput(source='pasted', diff=None)",             YELLOW_BG,    YELLOW_TEXT),
        ("Engine",      "AST chunking on full file (whole file = in scope)",        YELLOW_BG,    YELLOW_TEXT),
        ("Engine",      "Security Engine  +  Style Engine  (run in parallel)",      YELLOW_BG,    YELLOW_TEXT),
        ("MCP Server",  "Returns AnalysisResult { chunks, security_findings, style_findings }", (220,252,231),(21,128,61)),
        ("Claude API",  "Synthesizes findings into natural-language review",        (219,234,254),DARK_BLUE),
        ("Frontend",    "Displays review with highlighted findings",                LIGHT_BLUE,   DARK_BLUE),
    ]

    bw = 120
    bh = 9
    bx = 105 - bw / 2
    gap = 5

    y = pdf.get_y() + 2
    for i, (actor, label, fill, txtc) in enumerate(flow_steps):
        by = y + i * (bh + gap)
        # Actor badge on left
        pdf.set_fill_color(*DARK_BLUE)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.set_xy(bx - 28, by + 2)
        pdf.cell(26, 5, actor, fill=True, align="C")
        # Step box
        pdf.flow_box(bx, by, bw, bh, label, fill=fill, txt_color=txtc)
        # Arrow (except last)
        if i < len(flow_steps) - 1:
            pdf.flow_arrow(bx + bw / 2, by + bh, gap)
        pdf.set_text_color(0, 0, 0)

    # Key insight callout
    ci_y = y + len(flow_steps) * (bh + gap) + 4
    pdf.set_fill_color(*LIGHT_BLUE)
    pdf.set_draw_color(*ACCENT)
    pdf.rect(10, ci_y, 190, 14, "FD")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*DARK_BLUE)
    pdf.set_xy(14, ci_y + 2)
    pdf.cell(0, 5, "Key Insight: review_code is 100% stateless.")
    pdf.set_font("Helvetica", "", 8)
    pdf.set_xy(14, ci_y + 7)
    pdf.cell(0, 5, "No DB write, no GitHub call, no cache. Wrap -> Chunk -> Scan -> Return. Fast and simple.")
    pdf.set_draw_color(0, 0, 0)
    pdf.set_text_color(0, 0, 0)


def mcp_tools_page(pdf: ReviewMindPDF):
    pdf.add_page()
    pdf.section_title("6.  MCP Tools Registry  (19 Tools)")

    pdf.body(
        "All tools are registered on the MCP server. Claude reads their names and descriptions "
        "at startup (tools/list) and decides which to call based on the user's message. "
        "Tools marked Auth=Yes require the user to be authenticated before the backend executes them."
    )

    # Section label helper
    def section_label(text):
        pdf.set_fill_color(*LIGHT_GRAY)
        pdf.set_font("Helvetica", "B", 7)
        pdf.set_text_color(*ACCENT)
        pdf.cell(190, 5, f"  {text}", border=1, fill=True, new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_text_color(0, 0, 0)

    cols = [("Tool Name", 46), ("Input", 44), ("Purpose", 72), ("Auth", 12), ("Status", 16)]
    pdf.tbl_header(cols)

    prev_group = None
    group_labels = {
        "get_pr_summary":   "GitHub PR Tools  (no auth required to read)",
        "detect_language":  "Paste + Upload Tools  (review = no auth  |  apply = auth required)",
        "explain_finding":  "Utility Tools",
    }

    for i, (name, inp, purpose, auth, status) in enumerate(MCP_TOOLS):
        if name in group_labels:
            section_label(group_labels[name])

        shade = i % 2 == 0
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        pdf.set_font("Helvetica", "B" if "Done" in status else "", 7.5)
        pdf.set_text_color(*DARK_BLUE)
        pdf.cell(46, 6, name, border=1, fill=True)
        pdf.set_font("Helvetica", "", 7)
        pdf.set_text_color(40, 40, 40)
        pdf.cell(44, 6, inp, border=1, fill=True)
        pdf.cell(72, 6, purpose, border=1, fill=True)
        # Auth badge
        if auth == "Yes":
            pdf.set_fill_color(*ORANGE)
            pdf.set_text_color(*WHITE)
        else:
            pdf.set_fill_color((220, 252, 231))
            pdf.set_text_color((21, 128, 61))
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.cell(12, 6, auth, border=1, fill=True, align="C")
        # Status badge
        if "Done" in status:
            pdf.set_fill_color(*GREEN)
            pdf.set_text_color(*WHITE)
        else:
            pdf.set_fill_color((239, 246, 255))
            pdf.set_text_color(*ACCENT)
        pdf.set_font("Helvetica", "B", 6.5)
        pdf.cell(16, 6, status, border=1, fill=True, align="C")
        pdf.ln()
        pdf.set_text_color(0, 0, 0)

    pdf.ln(4)
    pdf.subsection("How Claude Uses These Tools")
    pdf.body(
        "Claude never calls tools in a hardcoded sequence - it assembles the right sequence "
        "dynamically based on user intent. The auth gate only blocks execution, not discovery: "
        "Claude can still describe what apply_fix would do before the user logs in."
    )
    examples = [
        '"What does this code do?" -> detect_language -> explain_code',
        '"Review my pasted code" -> detect_language -> review_code -> suggest_fix (per finding)',
        '"Apply the SQL fix" -> auth check -> apply_fix (after user confirms)',
        '"Review this file" -> detect_language -> review_file -> suggest_fix (per finding)',
        '"Just check for secrets on this PR" -> check_security_issues only',
        '"Post the review" -> auth check -> post_review',
    ]
    for ex in examples:
        pdf.bullet(ex)


def security_style_page(pdf: ReviewMindPDF):
    pdf.add_page()
    pdf.section_title("6.  Analysis Engines")

    pdf.subsection("Security Rules  (SEC001 – SEC005)")
    pdf.body(
        "Heuristic, pattern-based static analysis - fast, explainable, PR-scoped. "
        "Not a replacement for Semgrep/CodeQL, but a high-signal first pass."
    )
    cols = [("Rule ID", 18), ("Name", 42), ("Severity", 22), ("Detection Logic", 108)]
    pdf.tbl_header(cols)
    sev_colors = {"Critical": RED, "High": ORANGE, "Medium": (202,138,4), "Low": GREEN, "Info": ACCENT}
    for i, (rid, name, sev, logic) in enumerate(SECURITY_RULES):
        shade = i % 2 == 0
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(*ACCENT)
        pdf.cell(18, 6, rid, border=1, fill=True)
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.cell(42, 6, name, border=1, fill=True)
        pdf.set_fill_color(*sev_colors.get(sev, MID_GRAY))
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 7)
        pdf.cell(22, 6, sev, border=1, fill=True, align="C")
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        pdf.set_text_color(40, 40, 40)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.cell(108, 6, logic, border=1, fill=True)
        pdf.ln()
    pdf.set_text_color(0, 0, 0)

    pdf.ln(3)
    pdf.subsection("Style Rules  (STY001 – STY006)")
    pdf.body(
        "Loaded from reviewmind.yaml in the repo root - every rule is togglable per project. "
        "Severity is configurable; defaults shown below."
    )
    cols = [("Rule ID", 18), ("Name", 42), ("Default Severity", 32), ("Trigger Condition", 98)]
    pdf.tbl_header(cols)
    for i, (rid, name, sev, cond) in enumerate(STYLE_RULES):
        shade = i % 2 == 0
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(*ACCENT)
        pdf.cell(18, 6, rid, border=1, fill=True)
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.cell(42, 6, name, border=1, fill=True)
        pdf.cell(32, 6, sev, border=1, fill=True, align="C")
        pdf.cell(98, 6, cond, border=1, fill=True)
        pdf.ln()
    pdf.set_text_color(0, 0, 0)

    pdf.ln(3)
    pdf.subsection("Diff Engine Pipeline")
    steps = [
        "Raw unified diff  ->  parse files + hunks  (unidiff library)",
        "Fetch full post-change file content from GitHub Contents API",
        "AST parse with Python ast module  ->  map hunks to functions / classes",
        "Merge hunks in same function into one SemanticChunk",
        "Classify: new_feature / bug_fix / refactor / test_change / config_change / dependency_change",
        "Estimate cyclomatic complexity per function; flag complexity_delta > threshold",
        "Extract called functions (ast.Call nodes) for intra-PR dependency detection",
        "Return AnalysisResult { chunks: SemanticChunk[] }  ->  consumed by Security + Style engines",
    ]
    for s in steps:
        pdf.bullet(s)


def database_page(pdf: ReviewMindPDF):
    pdf.add_page()
    pdf.section_title("7.  Database Schema")

    pdf.body(
        "Five tables, designed around the 'repositories are the anchor' pattern. "
        "Redis caches derived/volatile data; Postgres stores canonical records."
    )

    cols = [("Table", 38), ("Key Columns", 80), ("Purpose", 72)]
    pdf.tbl_header(cols)
    for i, (tbl, cols_str, purpose) in enumerate(DB_TABLES):
        pdf.tbl_row([(tbl, 38), (cols_str, 80), (purpose, 72)], shade=i % 2 == 0)

    pdf.ln(4)
    pdf.subsection("Entity Relationships")
    rels = [
        "repositories  1 -> many  pull_requests        (one repo has many PRs)",
        "pull_requests  1 -> many  diff_chunks          (one PR produces many semantic chunks)",
        "pull_requests  1 -> many  findings             (one PR has many security/style findings)",
        "pull_requests  1 -> many  reviews              (one PR may have multiple posted reviews)",
        "diff_chunks    1 -> many  findings  (optional) (a finding may reference a specific chunk)",
    ]
    for r in rels:
        pdf.bullet(r)

    pdf.ln(4)
    pdf.subsection("Redis Cache Keys  &  TTL Strategy")
    cols = [("Key Pattern", 90), ("Data", 50), ("TTL", 50)]
    pdf.tbl_header(cols)
    cache_keys = [
        ("pr:{owner}:{repo}:{n}:summary",  "PR metadata",          "5 min (open)  /  24h (closed)"),
        ("pr:{owner}:{repo}:{n}:diff",     "Raw unified diff",     "1h (open)  /  7d (closed)"),
        ("pr:{owner}:{repo}:{n}:files",    "Files changed list",   "Same as diff"),
        ("pr:{owner}:{repo}:{n}:analysis", "Full AnalysisResult",  "Invalidated on new head_sha"),
        ("repo:{owner}:{repo}:config",     "reviewmind.yaml",      "1h (rarely changes)"),
        ("github:etag:{endpoint_hash}",    "Last ETag header",     "No TTL (overwritten on update)"),
    ]
    for i, (key, data, ttl) in enumerate(cache_keys):
        pdf.tbl_row([(key, 90), (data, 50), (ttl, 50)], shade=i % 2 == 0)

    pdf.ln(4)
    pdf.subsection("Indexing Strategy")
    indexes = [
        "repositories:  UNIQUE (owner, name)",
        "pull_requests:  UNIQUE (repository_id, pr_number)  |  INDEX on head_sha (cache invalidation)",
        "diff_chunks:    INDEX on (pull_request_id, file_path)",
        "findings:       INDEX on (pull_request_id, category)  |  INDEX on rule_id (analytics)",
        "reviews:        INDEX on pull_request_id",
    ]
    for idx in indexes:
        pdf.bullet(idx)


def status_roadmap_page(pdf: ReviewMindPDF):
    pdf.add_page()
    pdf.section_title("8.  Build Status  &  Roadmap")

    pdf.subsection("What's Built vs Pending")
    cols = [("Item", 100), ("Status", 28), ("Notes", 62)]
    pdf.tbl_header(cols)
    for i, (item, status, notes) in enumerate(BUILD_STATUS):
        shade = i % 2 == 0
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        pdf.set_font("Helvetica", "", 7.5)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(100, 6, item, border=1, fill=True)
        if "Done" in status:
            pdf.set_fill_color(*GREEN)
            pdf.set_text_color(*WHITE)
            pdf.set_font("Helvetica", "B", 7)
        else:
            pdf.set_fill_color(239, 246, 255)
            pdf.set_text_color(*ACCENT)
            pdf.set_font("Helvetica", "", 7)
        pdf.cell(28, 6, status, border=1, fill=True, align="C")
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        pdf.set_text_color(80, 80, 80)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.cell(62, 6, notes, border=1, fill=True)
        pdf.ln()
    pdf.set_text_color(0, 0, 0)

    pdf.ln(5)
    pdf.subsection("Phase Roadmap")
    cols = [("Phase", 18), ("Name", 36), ("Status", 24), ("Deliverables", 112)]
    pdf.tbl_header(cols)
    phase_colors = {
        "Done [DONE]": GREEN,
        "Next":   ACCENT,
        "Upcoming": ORANGE,
        "Future": MID_GRAY,
    }
    for i, (phase, name, status, delivs) in enumerate(ROADMAP):
        shade = i % 2 == 0
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.set_text_color(*DARK_BLUE)
        pdf.cell(18, 6, phase, border=1, fill=True, align="C")
        pdf.set_text_color(30, 30, 30)
        pdf.cell(36, 6, name, border=1, fill=True)
        col = phase_colors.get(status, MID_GRAY)
        pdf.set_fill_color(*col)
        pdf.set_text_color(*WHITE)
        pdf.set_font("Helvetica", "B", 7)
        pdf.cell(24, 6, status, border=1, fill=True, align="C")
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        pdf.set_text_color(50, 50, 50)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.cell(112, 6, delivs, border=1, fill=True)
        pdf.ln()
    pdf.set_text_color(0, 0, 0)

    # Footer callout
    pdf.ln(6)
    pdf.set_fill_color(*DARK_BLUE)
    pdf.rect(10, pdf.get_y(), 190, 18, "F")
    pdf.set_font("Helvetica", "B", 10)
    pdf.set_text_color(*WHITE)
    pdf.set_y(pdf.get_y() + 3)
    pdf.cell(0, 6, "To update this PDF - edit scripts/generate_pdf.py and re-run:", align="C",
             new_x=XPos.LMARGIN, new_y=YPos.NEXT)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_text_color(180, 200, 240)
    pdf.cell(0, 6, "python scripts/generate_pdf.py", align="C")
    pdf.set_text_color(0, 0, 0)


def upload_flow_page(pdf: ReviewMindPDF):
    pdf.add_page()
    pdf.section_title("5b.  Flow: Reviewing an Uploaded File")

    pdf.body(
        "Users can drag-and-drop or select one or more files directly in the frontend. "
        "ReviewMind reads the file content in the browser, sends it to the backend, and runs "
        "the full security + style pipeline on each file. No GitHub needed - works completely offline."
    )

    # ── Three-source comparison table ─────────────────────────────────────────
    pdf.subsection("Three Ways to Submit Code for Review")
    cols = [("Aspect", 44), ("GitHub PR", 48), ("Paste Code", 48), ("Upload File", 50)]
    pdf.tbl_header(cols)
    rows = [
        ("Input method",         "PR number + repo name",    "Type/paste in text area",   "Drag-drop or file picker"),
        ("GitHub API needed",    "Yes",                      "No",                        "No"),
        ("Filename known",       "Yes (from diff)",          "Optional (user types it)",  "Yes (from file system)"),
        ("Multiple files",       "Yes (all PR files)",       "No (one snippet)",          "Yes (batch upload)"),
        ("Diff available",       "Yes",                      "No",                        "No"),
        ("Results stored in DB", "Yes",                      "No",                        "No (stateless)"),
        ("MCP tool called",      "4-6 tools",                "review_code",               "review_file"),
        ("Best for",             "Team PR workflow",         "Quick snippet check",       "Reviewing local files"),
    ]
    for i, row in enumerate(rows):
        pdf.tbl_row([(v, [44, 48, 48, 50][j]) for j, v in enumerate(row)], shade=i % 2 == 0)

    pdf.ln(4)

    # ── Step-by-step flow as numbered rows ────────────────────────────────────
    pdf.subsection("Step-by-Step: Upload File Flow")

    steps = [
        (DARK_BLUE,       WHITE,         "Frontend",    "User drops file(s) onto upload zone (or clicks file picker)"),
        (DARK_BLUE,       WHITE,         "Frontend",    "Browser reads content -> builds: [{filename, content}, ...]"),
        (DARK_BLUE,       WHITE,         "Frontend",    'POST /chat  { message: "Review these files", files: [...] }'),
        ((21,128,61),     WHITE,         "Claude API",  "Reads file list in message -> decides: call review_file"),
        ((21,128,61),     WHITE,         "MCP Server",  "tools/call  review_file({ files: [{filename, content}] })"),
        (YELLOW_TEXT,     YELLOW_BG,     "Engine",      "For each file: wrap -> CodeInput(source='uploaded', diff=None)"),
        (YELLOW_TEXT,     YELLOW_BG,     "Engine",      "Detect language from filename  (.py / .ts / .go / .yaml)"),
        (YELLOW_TEXT,     YELLOW_BG,     "Engine",      "AST chunking per file  (whole file in scope - no diff)"),
        (YELLOW_TEXT,     YELLOW_BG,     "Engine",      "Security Engine + Style Engine run in parallel per file"),
        ((21,128,61),     WHITE,         "MCP Server",  "Returns findings grouped by file: [{file, chunks, findings}]"),
        (ACCENT,          WHITE,         "Claude API",  "Synthesizes per-file review + overall summary across files"),
        (DARK_BLUE,       WHITE,         "Frontend",    "Displays one findings tab per file + inline highlights"),
    ]

    col_widths = [28, 32, 130]   # badge | actor | step description
    row_h = 7

    for i, (badge_bg, badge_fg, actor, step) in enumerate(steps):
        shade = i % 2 == 0
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        # Step number
        pdf.set_font("Helvetica", "B", 8)
        pdf.set_text_color(*WHITE)
        pdf.set_fill_color(*ACCENT)
        pdf.cell(col_widths[0], row_h, f"Step {i+1}", border=1, fill=True, align="C")
        # Actor badge
        pdf.set_fill_color(*badge_bg)
        pdf.set_text_color(*badge_fg)
        pdf.set_font("Helvetica", "B", 7.5)
        pdf.cell(col_widths[1], row_h, actor, border=1, fill=True, align="C")
        # Description
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(col_widths[2], row_h, step, border=1, fill=True)
        pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.ln(5)

    # ── Side-by-side info panels ──────────────────────────────────────────────
    # Draw two panels as tables (no absolute positioning)
    pdf.subsection("Supported File Types  &  Key Design Decisions")

    col_l = 95
    col_r = 95

    # Headers
    pdf.set_fill_color(*ACCENT)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(col_l, 7, "  Supported File Types (MVP)", border=1, fill=True)
    pdf.cell(col_r, 7, "  Key Design Decisions", border=1, fill=True)
    pdf.ln()

    panel_data = [
        (".py          - Python (full AST analysis)",          "No DB write - upload reviews are stateless"),
        (".js / .ts    - JavaScript / TypeScript (regex)",     "Results per file, not one merged blob"),
        (".go          - Go (regex-based for MVP)",            "diff=None -> whole file is in scope"),
        (".yaml/.json/.toml  - Config files",                  "Same engine as PR review - zero code duplication"),
        (".txt         - Plain text (style rules only)",       "File size limit enforced in frontend (2 MB max)"),
    ]
    for i, (left, right) in enumerate(panel_data):
        shade = i % 2 == 0
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 7.5)
        pdf.cell(col_l, 6, f"  {left}", border=1, fill=True)
        pdf.set_fill_color(*(YELLOW_BG if shade else WHITE))
        pdf.cell(col_r, 6, f"  {right}", border=1, fill=True)
        pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # ── Bottom insight banner ─────────────────────────────────────────────────
    pdf.set_fill_color(*DARK_BLUE)
    pdf.set_draw_color(*DARK_BLUE)
    h = 12
    pdf.rect(10, pdf.get_y(), 190, h, "F")
    pdf.set_font("Helvetica", "B", 8)
    pdf.set_text_color(*WHITE)
    pdf.set_x(14)
    pdf.cell(0, h / 2, "review_file  =  review_code  but for multiple files.")
    pdf.set_xy(14, pdf.get_y() + h / 2)
    pdf.set_font("Helvetica", "", 8)
    pdf.set_text_color(180, 200, 240)
    pdf.cell(0, h / 2, "Same CodeInput -> Chunk -> Scan pipeline. Only the adapter layer differs.")
    pdf.set_text_color(0, 0, 0)
    pdf.set_draw_color(0, 0, 0)


def authenticated_fix_flow_page(pdf: ReviewMindPDF):
    pdf.add_page()
    pdf.section_title("5c.  Flow: Review -> Suggest Fix -> Auth Gate -> Apply Fix")

    pdf.body(
        "The core principle: READING is free and open, WRITING requires identity. "
        "A user can review any code without logging in. The moment they want to apply a fix "
        "to their code, ReviewMind triggers an auth gate. After login the exact fix they "
        "approved is applied - nothing else."
    )

    # ── Auth rule table ───────────────────────────────────────────────────────
    pdf.subsection("Auth Rule: What Requires Login?")
    cols = [("Action", 80), ("Auth Required?", 30), ("Why"), ]
    # Manual table
    pdf.set_fill_color(*DARK_BLUE)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 8)
    pdf.cell(80, 7, "Action", border=1, fill=True, align="C")
    pdf.cell(30, 7, "Auth Required?", border=1, fill=True, align="C")
    pdf.cell(80, 7, "Reason", border=1, fill=True, align="C")
    pdf.ln()
    auth_rows = [
        ("detect_language, explain_code",     "No",  "Read-only - just understanding the code"),
        ("review_code, review_file",           "No",  "Read-only - analysis produces no side effects"),
        ("suggest_fix  (per finding)",         "No",  "Read-only - just a suggestion, nothing applied yet"),
        ("apply_fix  (write the change)",      "YES", "Mutates code - must know WHO made this change"),
        ("post_review  (write to GitHub)",     "YES", "Mutates GitHub PR - requires GitHub identity"),
    ]
    for i, (action, auth, reason) in enumerate(auth_rows):
        shade = i % 2 == 0
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        pdf.set_font("Helvetica", "", 8)
        pdf.set_text_color(30, 30, 30)
        pdf.cell(80, 6, action, border=1, fill=True)
        if auth == "YES":
            pdf.set_fill_color(*ORANGE)
            pdf.set_text_color(*WHITE)
            pdf.set_font("Helvetica", "B", 8)
        else:
            pdf.set_fill_color((220, 252, 231))
            pdf.set_text_color((21, 128, 61))
            pdf.set_font("Helvetica", "", 8)
        pdf.cell(30, 6, auth, border=1, fill=True, align="C")
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(80, 6, reason, border=1, fill=True)
        pdf.ln()
    pdf.set_text_color(0, 0, 0)

    pdf.ln(4)

    # ── Full step flow ────────────────────────────────────────────────────────
    pdf.subsection("Complete Step-by-Step Flow")

    steps = [
        # (phase, auth_needed, actor_color, actor, step_text)
        ("REVIEW",  False, DARK_BLUE,      WHITE,       "Frontend",   "User pastes code or uploads file(s)"),
        ("REVIEW",  False, DARK_BLUE,      WHITE,       "MCP Server", "detect_language -> identifies .py / .ts / .go"),
        ("REVIEW",  False, DARK_BLUE,      WHITE,       "MCP Server", "explain_code -> plain-English summary of what the code does"),
        ("REVIEW",  False, (21,128,61),    WHITE,       "MCP Server", "review_code / review_file -> Security + Style findings"),
        ("REVIEW",  False, (21,128,61),    WHITE,       "Claude API", "Presents findings to user: 3 issues found (1 critical, 2 medium)"),
        ("FIX",     False, YELLOW_TEXT,    YELLOW_BG,   "Claude API", "suggest_fix for each finding -> shows diff of what would change"),
        ("FIX",     False, YELLOW_TEXT,    YELLOW_BG,   "Frontend",   "User reviews suggested fixes, clicks 'Apply Fix' on one"),
        ("AUTH",    True,  (185, 28, 28),  WHITE,       "Backend",    "Auth check: is this user authenticated?  ->  NO"),
        ("AUTH",    True,  (185, 28, 28),  WHITE,       "Frontend",   "Show login modal  (email/password or GitHub OAuth)"),
        ("AUTH",    True,  (185, 28, 28),  WHITE,       "Backend",    "User logs in -> JWT token issued -> session created"),
        ("APPLY",   True,  ACCENT,         WHITE,       "Backend",    "Auth check passes -> confirmed=True passed to apply_fix"),
        ("APPLY",   True,  ACCENT,         WHITE,       "MCP Server", "apply_fix(finding_id, code, confirmed=True) executes"),
        ("APPLY",   True,  ACCENT,         WHITE,       "MCP Server", "Returns patched code with only the approved fix applied"),
        ("APPLY",   True,  ACCENT,         WHITE,       "Frontend",   "Displays diff: original vs fixed. User can copy or download."),
    ]

    phase_colors = {
        "REVIEW": (220, 252, 231),
        "FIX":    YELLOW_BG,
        "AUTH":   (254, 226, 226),
        "APPLY":  (219, 234, 254),
    }
    phase_text_colors = {
        "REVIEW": (21, 128, 61),
        "FIX":    YELLOW_TEXT,
        "AUTH":   (185, 28, 28),
        "APPLY":  DARK_BLUE,
    }

    col_w = [18, 10, 28, 134]  # phase | auth | actor | step

    # Column headers
    pdf.set_fill_color(*DARK_BLUE)
    pdf.set_text_color(*WHITE)
    pdf.set_font("Helvetica", "B", 8)
    for label, w in [("Phase", 18), ("Auth", 10), ("Actor", 28), ("What Happens", 134)]:
        pdf.cell(w, 7, label, border=1, fill=True, align="C")
    pdf.ln()

    prev_phase = None
    for i, (phase, auth_needed, actor_bg, actor_fg, actor, step) in enumerate(steps):
        shade = i % 2 == 0

        # Phase cell
        if phase != prev_phase:
            pdf.set_fill_color(*phase_colors[phase])
            pdf.set_text_color(*phase_text_colors[phase])
            pdf.set_font("Helvetica", "B", 7)
        else:
            pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
            pdf.set_text_color(*MID_GRAY)
            pdf.set_font("Helvetica", "", 7)
        pdf.cell(18, 6, phase if phase != prev_phase else "", border=1, fill=True, align="C")
        prev_phase = phase

        # Auth cell
        if auth_needed:
            pdf.set_fill_color(*ORANGE)
            pdf.set_text_color(*WHITE)
            pdf.set_font("Helvetica", "B", 6)
            pdf.cell(10, 6, "YES", border=1, fill=True, align="C")
        else:
            pdf.set_fill_color((220, 252, 231))
            pdf.set_text_color((21,128,61))
            pdf.set_font("Helvetica", "", 6)
            pdf.cell(10, 6, "No", border=1, fill=True, align="C")

        # Actor cell
        pdf.set_fill_color(*actor_bg)
        pdf.set_text_color(*actor_fg)
        pdf.set_font("Helvetica", "B", 7)
        pdf.cell(28, 6, actor, border=1, fill=True, align="C")

        # Step cell
        pdf.set_fill_color(*(LIGHT_GRAY if shade else WHITE))
        pdf.set_text_color(30, 30, 30)
        pdf.set_font("Helvetica", "", 8)
        pdf.cell(134, 6, step, border=1, fill=True)
        pdf.ln()

    pdf.set_text_color(0, 0, 0)
    pdf.ln(4)

    # ── Key design rules ──────────────────────────────────────────────────────
    pdf.subsection("Key Design Rules for apply_fix")
    rules = [
        "One fix at a time - apply_fix takes a single finding_id, not a list. User must confirm each fix individually.",
        "confirmed flag is required - Claude always passes confirmed=True only AFTER the user explicitly clicks 'Apply'. No silent auto-apply.",
        "apply_fix never calls GitHub - it returns patched code to the frontend. The user decides what to do with it (copy, download, or paste back).",
        "The fix is scoped exactly - only the lines from the finding are changed. Nothing else in the file is touched.",
        "Audit trail - every apply_fix call is logged with user_id + finding_id + timestamp even though the result is not stored in DB.",
    ]
    for r in rules:
        pdf.bullet(r)


# ─────────────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────────────

def generate():
    pdf = ReviewMindPDF()
    pdf.set_auto_page_break(auto=True, margin=14)
    pdf.set_margins(10, 14, 10)

    cover_page(pdf)
    overview_page(pdf)
    architecture_flow_page(pdf)
    pr_review_flow_page(pdf)
    paste_flow_page(pdf)
    upload_flow_page(pdf)
    authenticated_fix_flow_page(pdf)
    mcp_tools_page(pdf)
    security_style_page(pdf)
    database_page(pdf)
    status_roadmap_page(pdf)

    pdf.output(OUTPUT_PATH)
    print(f"[DONE]  PDF generated: {OUTPUT_PATH}  ({pdf.page} pages)")


if __name__ == "__main__":
    generate()
