"""
ReviewMind MCP Server — 9 tools, 5 resources, 5 prompts.

Tools are thin wrappers: they parse arguments, call the service layer,
and serialize results as JSON text. No business logic lives here.

All stdout is reserved for the MCP stdio protocol — never print() directly.
"""

from __future__ import annotations

import asyncio
import dataclasses
import json

import mcp.server.stdio
import mcp.types as types
from mcp.server import NotificationOptions, Server
from mcp.server.models import InitializationOptions

from reviewmind.core.logging import configure_logging, get_logger

configure_logging()
logger = get_logger(__name__)

server = Server("reviewmind")

# ── Lazy-initialized singletons ───────────────────────────────────────────────
# Initialized on first tool/resource call so imports don't fail when env vars
# are missing at module load time (e.g., during tests).

_svc_initialized = False
_analysis_svc = None
_context_svc = None
_review_svc = None
_repo = None


def _get_services():
    global _svc_initialized, _analysis_svc, _context_svc, _review_svc, _repo
    if not _svc_initialized:
        from reviewmind.services.context_service import ContextService
        from reviewmind.services.github.client import GitHubClient
        from reviewmind.services.github.repository import GitHubRepository
        from reviewmind.services.pr_analysis import PRAnalysisService
        from reviewmind.services.review_service import ReviewService

        client = GitHubClient()
        _repo = GitHubRepository(client)
        _analysis_svc = PRAnalysisService(_repo)
        _context_svc = ContextService(_repo)
        _review_svc = ReviewService(_repo)
        _svc_initialized = True
    return _analysis_svc, _context_svc, _review_svc


# stateless services — imported directly, no singleton needed
from reviewmind.services import code_analysis as _code_analysis_svc
from reviewmind.services import snippet_compare as _snippet_compare_svc
from reviewmind.services import fix_suggester as _fix_suggester_svc


def _to_json(obj) -> str:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return json.dumps(dataclasses.asdict(obj), default=str, indent=2)
    if isinstance(obj, list):
        return json.dumps(
            [dataclasses.asdict(i) if (dataclasses.is_dataclass(i) and not isinstance(i, type)) else i
             for i in obj],
            default=str, indent=2,
        )
    return json.dumps(obj, default=str, indent=2)


def _text(content: str) -> list[types.TextContent]:
    return [types.TextContent(type="text", text=content)]


# ── Tools ─────────────────────────────────────────────────────────────────────

@server.list_tools()
async def list_tools() -> list[types.Tool]:
    pr_args = {
        "type": "object",
        "properties": {
            "owner": {"type": "string", "description": "GitHub repo owner (user or org)"},
            "repo": {"type": "string", "description": "GitHub repo name"},
            "pr_number": {"type": "integer", "description": "Pull request number"},
        },
        "required": ["owner", "repo", "pr_number"],
    }
    return [
        types.Tool(
            name="ping",
            description="Health-check. Returns 'pong'.",
            inputSchema={"type": "object", "properties": {}},
        ),
        types.Tool(
            name="get_pr_summary",
            description=(
                "Return PR metadata: title, description, author, additions/deletions, "
                "state, URL, and base branch. Call this first to understand the PR scope."
            ),
            inputSchema=pr_args,
        ),
        types.Tool(
            name="analyze_diff",
            description=(
                "Run the semantic diff pipeline on a PR. Returns chunks grouped by "
                "classification (new_feature, refactor, test, dep, config, unknown) with "
                "file paths, symbol names, and complexity scores."
            ),
            inputSchema=pr_args,
        ),
        types.Tool(
            name="check_security_issues",
            description=(
                "Scan the PR diff for security issues (SEC001–005): hardcoded secrets, "
                "SQL injection, insecure dependencies, missing input validation, and "
                "unsafe deserialization. Returns findings sorted by severity."
            ),
            inputSchema=pr_args,
        ),
        types.Tool(
            name="check_style_violations",
            description=(
                "Check the PR diff against the repo's reviewmind.yaml conventions "
                "(STY001–006). Falls back to defaults if no config exists. Returns "
                "violations sorted by severity."
            ),
            inputSchema=pr_args,
        ),
        types.Tool(
            name="get_pr_context",
            description=(
                "Enrich the PR with contextual signals: who touched these files recently, "
                "related open/merged PRs on the repo, and issues linked in the PR body."
            ),
            inputSchema=pr_args,
        ),
        types.Tool(
            name="suggest_reviewers",
            description=(
                "Suggest the best reviewers for a PR based on git commit history for "
                "touched files and CODEOWNERS matches. Returns a ranked list with reasons."
            ),
            inputSchema=pr_args,
        ),
        types.Tool(
            name="get_review_history",
            description=(
                "Return all existing review decisions and inline comments on the PR. "
                "Read this before generating a new review to avoid duplicating feedback."
            ),
            inputSchema=pr_args,
        ),
        types.Tool(
            name="generate_review_comment",
            description=(
                "Format a security or style finding as a GitHub-ready Markdown comment. "
                "comment_style: 'concise' (one-liner), 'detailed' (adds snippet + badge), "
                "or 'educational' (adds why it matters and how to fix)."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "finding": {
                        "type": "object",
                        "description": "A SecurityFinding or StyleFinding dict from the scan tools",
                    },
                    "comment_style": {
                        "type": "string",
                        "enum": ["concise", "detailed", "educational"],
                        "default": "concise",
                    },
                },
                "required": ["finding"],
            },
        ),
        types.Tool(
            name="analyze_paste",
            description=(
                "Analyze a code snippet pasted directly into the conversation — no GitHub PR needed. "
                "Runs the full pipeline: semantic chunking, security scan (SEC001–005), and style "
                "check (STY001–006). Use filename to hint the language (e.g. 'auth.py', 'main.go')."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "The raw source code to analyze"},
                    "filename": {
                        "type": "string",
                        "default": "snippet.py",
                        "description": "Filename hint for language detection (e.g. 'auth.py', 'index.ts')",
                    },
                },
                "required": ["code"],
            },
        ),
        types.Tool(
            name="analyze_upload",
            description=(
                "Analyze one or more uploaded files — no GitHub PR needed. "
                "Pass file content as plain text strings. Runs the full pipeline on each file: "
                "semantic chunking, security scan, and style check. Returns results per file."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "name": {"type": "string", "description": "Filename (e.g. 'auth.py')"},
                                "content": {"type": "string", "description": "Full file content as text"},
                            },
                            "required": ["name", "content"],
                        },
                        "description": "List of files to analyze",
                        "minItems": 1,
                    },
                },
                "required": ["files"],
            },
        ),
        types.Tool(
            name="compare_snippets",
            description=(
                "Compare two versions of the same code (before and after a refactor) "
                "without needing a GitHub PR. Synthesizes a diff and runs the full pipeline: "
                "semantic chunking, security scan, style check, and complexity delta. "
                "Use filename to hint the language (e.g. 'auth.py', 'main.go')."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "before": {"type": "string", "description": "The original code"},
                    "after": {"type": "string", "description": "The revised code"},
                    "filename": {
                        "type": "string",
                        "default": "snippet.py",
                        "description": "Filename hint for language detection",
                    },
                },
                "required": ["before", "after"],
            },
        ),
        types.Tool(
            name="suggest_fixes",
            description=(
                "Analyze pasted code and return a concrete fix suggestion for every "
                "security and style finding. Each suggestion includes what's wrong, "
                "how to fix it, and a code example showing the correct pattern. "
                "Use filename to hint the language (e.g. 'auth.py', 'index.ts')."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {"type": "string", "description": "The source code to analyze"},
                    "filename": {
                        "type": "string",
                        "default": "snippet.py",
                        "description": "Filename hint for language detection",
                    },
                },
                "required": ["code"],
            },
        ),
        types.Tool(
            name="post_review",
            description=(
                "Post a review to GitHub. ALWAYS call with confirmed=false first to preview, "
                "then ask the user to confirm before setting confirmed=true. "
                "This is the only tool that mutates external state."
            ),
            inputSchema={
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "pr_number": {"type": "integer"},
                    "body": {"type": "string", "description": "Review summary body (Markdown)"},
                    "event": {
                        "type": "string",
                        "enum": ["APPROVE", "REQUEST_CHANGES", "COMMENT"],
                    },
                    "comments": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "path": {"type": "string"},
                                "line": {"type": "integer"},
                                "body": {"type": "string"},
                            },
                            "required": ["path", "line", "body"],
                        },
                        "description": "Inline review comments",
                    },
                    "confirmed": {
                        "type": "boolean",
                        "default": False,
                        "description": "Must be true to actually post. Use false first to preview.",
                    },
                },
                "required": ["owner", "repo", "pr_number", "body", "event"],
            },
        ),
    ]


@server.call_tool()
async def call_tool(name: str, arguments: dict) -> list[types.TextContent]:
    analysis_svc, context_svc, review_svc = _get_services()

    owner = arguments.get("owner", "")
    repo = arguments.get("repo", "")
    pr_number = int(arguments.get("pr_number", 0))

    match name:
        case "ping":
            logger.info("tool_called", tool="ping")
            return _text("pong")

        case "get_pr_summary":
            result = await analysis_svc.get_pr_summary(owner, repo, pr_number)
            return _text(_to_json(result))

        case "analyze_diff":
            chunks = await analysis_svc.get_chunks(owner, repo, pr_number)
            by_class: dict[str, list[dict]] = {}
            for chunk in chunks:
                entry = {
                    "file_path": chunk.file_path,
                    "symbol_name": chunk.symbol_name,
                    "chunk_type": chunk.chunk_type,
                    "complexity": chunk.complexity,
                    "start_line": chunk.start_line,
                    "end_line": chunk.end_line,
                    "change_type": chunk.change_type,
                    "language": chunk.language,
                }
                by_class.setdefault(chunk.classification, []).append(entry)
            return _text(json.dumps(
                {"total_chunks": len(chunks), "by_classification": by_class},
                indent=2,
            ))

        case "check_security_issues":
            findings = await analysis_svc.get_security_findings(owner, repo, pr_number)
            return _text(_to_json(findings))

        case "check_style_violations":
            findings = await analysis_svc.get_style_findings(owner, repo, pr_number)
            return _text(_to_json(findings))

        case "get_pr_context":
            ctx = await context_svc.get_pr_context(owner, repo, pr_number)
            return _text(_to_json(ctx))

        case "suggest_reviewers":
            suggestions = await context_svc.suggest_reviewers(owner, repo, pr_number)
            return _text(_to_json(suggestions))

        case "get_review_history":
            history = await review_svc.get_review_history(owner, repo, pr_number)
            return _text(_to_json(history))

        case "generate_review_comment":
            finding = arguments.get("finding", {})
            style = arguments.get("comment_style", "concise")
            comment = review_svc.generate_review_comment(finding, style)
            return _text(comment)

        case "compare_snippets":
            result = await _snippet_compare_svc.compare_snippets(
                before=arguments["before"],
                after=arguments["after"],
                filename=arguments.get("filename", "snippet.py"),
            )
            return _text(_to_json(result))

        case "suggest_fixes":
            report = await _fix_suggester_svc.suggest_fixes(
                code=arguments["code"],
                filename=arguments.get("filename", "snippet.py"),
            )
            return _text(_to_json(report))

        case "analyze_paste":
            result = await _code_analysis_svc.analyze_paste(
                code=arguments["code"],
                filename=arguments.get("filename", "snippet.py"),
            )
            return _text(_to_json(result))

        case "analyze_upload":
            results = await _code_analysis_svc.analyze_uploads(
                files=arguments["files"],
            )
            return _text(_to_json(results))

        case "post_review":
            result = await review_svc.post_review(
                owner, repo, pr_number,
                body=arguments.get("body", ""),
                event=arguments.get("event", "COMMENT"),
                comments=arguments.get("comments"),
                confirmed=arguments.get("confirmed", False),
            )
            return _text(_to_json(result))

        case _:
            raise ValueError(f"Unknown tool: {name}")


# ── Resources ─────────────────────────────────────────────────────────────────

@server.list_resources()
async def list_resources() -> list[types.Resource]:
    return [
        types.Resource(
            uri=types.AnyUrl("repo://owner/repo/conventions"),
            name="Repository conventions (reviewmind.yaml)",
            description="Team coding conventions loaded from reviewmind.yaml in the repo root.",
            mimeType="text/yaml",
        ),
        types.Resource(
            uri=types.AnyUrl("repo://owner/repo/recent-prs"),
            name="Recent PRs",
            description="Last 20 pull requests on the repo.",
            mimeType="application/json",
        ),
        types.Resource(
            uri=types.AnyUrl("pr://owner/repo/1/diff"),
            name="PR raw diff",
            description="Full unified diff for a pull request.",
            mimeType="text/plain",
        ),
        types.Resource(
            uri=types.AnyUrl("pr://owner/repo/1/comments"),
            name="PR review comments",
            description="All existing inline review comments on a PR.",
            mimeType="application/json",
        ),
        types.Resource(
            uri=types.AnyUrl("pr://owner/repo/1/checks"),
            name="PR CI checks",
            description="CI check run results for the PR head commit.",
            mimeType="application/json",
        ),
    ]


@server.read_resource()
async def read_resource(uri: types.AnyUrl) -> str:
    import dataclasses as dc
    import yaml

    from reviewmind.engine.style.models import StyleConfig
    from reviewmind.services.github.client import NotFoundError

    _, _, review_svc = _get_services()
    repo_svc = _repo

    uri_str = str(uri)

    if uri_str.startswith("repo://"):
        parts = uri_str.removeprefix("repo://").split("/")
        if len(parts) < 3:
            raise ValueError(f"Malformed resource URI: {uri_str}")
        owner, repo_name, resource = parts[0], parts[1], parts[2]

        if resource == "conventions":
            try:
                content = await repo_svc.get_file_content(owner, repo_name, "reviewmind.yaml", "HEAD")
                return content
            except NotFoundError:
                return yaml.dump(dc.asdict(StyleConfig()))

        if resource == "recent-prs":
            prs = await repo_svc.get_related_prs(owner, repo_name, [])
            return json.dumps([dc.asdict(p) for p in prs], default=str, indent=2)

    elif uri_str.startswith("pr://"):
        parts = uri_str.removeprefix("pr://").split("/")
        if len(parts) < 4:
            raise ValueError(f"Malformed resource URI: {uri_str}")
        owner, repo_name, pr_number_str, resource = parts[0], parts[1], parts[2], parts[3]
        pr_number = int(pr_number_str)

        if resource == "diff":
            return await repo_svc.get_pr_diff(owner, repo_name, pr_number)

        if resource == "comments":
            history = await review_svc.get_review_history(owner, repo_name, pr_number)
            return json.dumps(
                [dc.asdict(c) for c in history.inline_comments], default=str, indent=2
            )

        if resource == "checks":
            pr = await repo_svc.get_pr(owner, repo_name, pr_number)
            checks = await repo_svc.get_check_runs(owner, repo_name, pr.head_sha)
            return json.dumps([dc.asdict(c) for c in checks], default=str, indent=2)

    raise ValueError(f"Unknown resource URI: {uri_str}")


# ── Prompts ───────────────────────────────────────────────────────────────────

@server.list_prompts()
async def list_prompts() -> list[types.Prompt]:
    pr_args = [
        types.PromptArgument(name="owner", description="GitHub repo owner", required=True),
        types.PromptArgument(name="repo", description="GitHub repo name", required=True),
        types.PromptArgument(name="pr_number", description="Pull request number", required=True),
    ]
    return [
        types.Prompt(
            name="full_review",
            description=(
                "End-to-end PR review: summary → semantic analysis → security → style → "
                "reviewer suggestions → post to GitHub (with confirmation)."
            ),
            arguments=pr_args,
        ),
        types.Prompt(
            name="security_focused_review",
            description="Deep security review with educational comments for each finding.",
            arguments=pr_args,
        ),
        types.Prompt(
            name="quick_summary",
            description="3-sentence PR summary — what changed, why it matters, one risk to watch.",
            arguments=pr_args,
        ),
        types.Prompt(
            name="reviewer_briefing",
            description=(
                "Briefing for a human reviewer: what to focus on, what existing reviewers "
                "said, and who's touched this code before."
            ),
            arguments=pr_args,
        ),
        types.Prompt(
            name="suggest_pr_improvements",
            description=(
                "Author-facing feedback: actionable improvements before merging, "
                "covering logic, security, and style."
            ),
            arguments=pr_args,
        ),
    ]


@server.get_prompt()
async def get_prompt(name: str, arguments: dict | None) -> types.GetPromptResult:
    args = arguments or {}
    owner = args.get("owner", "{owner}")
    repo = args.get("repo", "{repo}")
    pr = args.get("pr_number", "{pr_number}")
    ref = f"PR #{pr} in {owner}/{repo}"

    match name:
        case "full_review":
            text = (
                f"Perform a complete code review of {ref}.\n\n"
                "Follow these steps in order:\n"
                "1. Call `get_pr_summary` to understand the scope and author.\n"
                "2. Call `analyze_diff` to see what changed semantically.\n"
                "3. Call `check_security_issues` — report all findings with severity.\n"
                "4. Call `check_style_violations` — report all violations.\n"
                "5. Call `get_review_history` to see existing feedback — avoid duplicates.\n"
                "6. Call `suggest_reviewers` to recommend who should review.\n"
                "7. Synthesize a review body covering: summary of changes, security issues, "
                "style issues, and an overall recommendation.\n"
                "8. Call `post_review` with `confirmed=false` to show the preview.\n"
                "9. Ask the user: 'Shall I post this review to GitHub?' — wait for confirmation.\n"
                "10. If confirmed, call `post_review` again with `confirmed=true`.\n"
            )

        case "security_focused_review":
            text = (
                f"Perform a security-focused review of {ref}.\n\n"
                "1. Call `check_security_issues` to find all security findings.\n"
                "2. For each critical or high finding, call `generate_review_comment` "
                "with `comment_style=educational` to explain the risk and fix.\n"
                "3. Summarize all findings with severity levels and estimated impact.\n"
                "4. Recommend APPROVE, REQUEST_CHANGES, or COMMENT based on severity.\n"
                "5. Call `post_review` with `confirmed=false` and show the preview before posting.\n"
            )

        case "quick_summary":
            text = (
                f"Provide a quick summary of {ref}.\n\n"
                "Call `get_pr_summary` and respond with exactly 3 sentences:\n"
                "1. What this PR changes.\n"
                "2. Why it matters (infer from title and description).\n"
                "3. One risk or open question to watch.\n"
            )

        case "reviewer_briefing":
            text = (
                f"Generate a reviewer briefing for {ref}.\n\n"
                "1. Call `get_pr_context` to see who touched the files and related PRs.\n"
                "2. Call `get_review_history` to summarize what existing reviewers said.\n"
                "3. Call `suggest_reviewers` to recommend who should be assigned.\n"
                "Write a briefing for the next human reviewer covering:\n"
                "- What the PR does and which files matter most.\n"
                "- What previous reviewers flagged (if anything).\n"
                "- Who has deep knowledge of the touched files.\n"
                "- What to focus on during review.\n"
            )

        case "suggest_pr_improvements":
            text = (
                f"Generate improvement suggestions for the author of {ref}.\n\n"
                "1. Call `analyze_diff` to understand what changed.\n"
                "2. Call `check_security_issues` for any security concerns.\n"
                "3. Call `check_style_violations` for style issues.\n"
                "Write friendly, actionable feedback addressed directly to the PR author. "
                "Focus on what would make this PR better before merging. "
                "Be constructive — explain why each suggestion matters.\n"
            )

        case _:
            raise ValueError(f"Unknown prompt: {name}")

    return types.GetPromptResult(
        description=f"ReviewMind: {name}",
        messages=[
            types.PromptMessage(
                role="user",
                content=types.TextContent(type="text", text=text),
            )
        ],
    )


# ── Entry point ───────────────────────────────────────────────────────────────

async def main() -> None:
    async with mcp.server.stdio.stdio_server() as (read_stream, write_stream):
        await server.run(
            read_stream,
            write_stream,
            InitializationOptions(
                server_name="reviewmind",
                server_version="0.1.0",
                capabilities=server.get_capabilities(
                    notification_options=NotificationOptions(),
                    experimental_capabilities={},
                ),
            ),
        )


if __name__ == "__main__":
    asyncio.run(main())
