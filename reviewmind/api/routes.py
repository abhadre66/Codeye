from __future__ import annotations

import dataclasses
import json
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import AsyncSession

from reviewmind.api.auth import require_auth, get_github_token, get_optional_github_token
from reviewmind.core.cache import redis_client
from reviewmind.core.config import settings
from reviewmind.core.logging import get_logger
from reviewmind.db.models import AnalysisHistory
from reviewmind.db.session import get_session

logger = get_logger(__name__)

router = APIRouter()

# ── Stateless service imports ─────────────────────────────────────────────────
from reviewmind.services import code_analysis as _code_analysis
from reviewmind.services import fix_suggester as _fix_suggester
from reviewmind.services import snippet_compare as _snippet_compare

# ── Lazy PR services ──────────────────────────────────────────────────────────
from reviewmind.mcp_server import _to_json


def _make_services(token: str):
    """Create fresh PR service instances with a specific GitHub token."""
    from reviewmind.services.context_service import ContextService
    from reviewmind.services.github.client import GitHubClient
    from reviewmind.services.github.repository import GitHubRepository
    from reviewmind.services.pr_analysis import PRAnalysisService
    from reviewmind.services.review_service import ReviewService

    client = GitHubClient(token=token)
    repo = GitHubRepository(client)
    return PRAnalysisService(repo), ContextService(repo), ReviewService(repo)


def _asdict(obj: Any) -> Any:
    if dataclasses.is_dataclass(obj) and not isinstance(obj, type):
        return dataclasses.asdict(obj)
    if isinstance(obj, list):
        return [_asdict(i) for i in obj]
    return obj


async def _record_history(
    session: AsyncSession,
    user_id: str,
    source: str,
    label: str,
    security_count: int,
    style_count: int,
    payload: dict,
) -> None:
    """Best-effort: never let history logging break the actual analysis response."""
    try:
        session.add(AnalysisHistory(
            user_id=user_id,
            source=source,
            label=label,
            findings_count=security_count + style_count,
            security_count=security_count,
            style_count=style_count,
            payload=json.dumps(payload),
        ))
        await session.commit()
    except Exception as exc:
        logger.error("history_record_failed", user_id=user_id, source=source, error=str(exc))


# ─────────────────────────────────────────────────────────────────────────────
# Request models
# ─────────────────────────────────────────────────────────────────────────────

class PasteRequest(BaseModel):
    code: str
    filename: str = "snippet.py"

class UploadRequest(BaseModel):
    files: list[dict]  # [{name: str, content: str}]

class CompareRequest(BaseModel):
    before: str
    after: str
    filename: str = "snippet.py"

class FixRequest(BaseModel):
    code: str
    filename: str = "snippet.py"
    source: str = "paste"  # "paste" | "upload" — which Analyze tab this came from

class PRRequest(BaseModel):
    owner: str
    repo: str
    pr_number: int

class PostReviewRequest(BaseModel):
    owner: str
    repo: str
    pr_number: int
    body: str
    event: str  # APPROVE | REQUEST_CHANGES | COMMENT
    comments: list[dict] = []
    confirmed: bool = False

class ChatRequest(BaseModel):
    message: str
    code: str | None = None
    files: list[dict] | None = None   # [{name, content}]
    pr: dict | None = None            # {owner, repo, pr_number}

class SaveGitHubTokenRequest(BaseModel):
    github_token: str


# ─────────────────────────────────────────────────────────────────────────────
# Health
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/profile/github-token")
async def save_github_token(
    req: SaveGitHubTokenRequest,
    user: dict = Depends(require_auth),
) -> dict:
    from reviewmind.api.supabase_client import get_supabase
    from reviewmind.core.crypto import encrypt_token
    supabase = get_supabase()
    try:
        result = supabase.table("profiles").upsert({
            "id": user.id,
            "github_token": encrypt_token(req.github_token),
            "github_username": user.user_metadata.get("user_name", ""),
        }).execute()
        logger.info("github_token_saved", user_id=user.id, row_count=len(result.data or []))
        return {"ok": True}
    except Exception as exc:
        logger.error("github_token_save_failed", user_id=user.id, error=str(exc))
        raise HTTPException(status_code=500, detail=f"Failed to save GitHub token: {exc}")

# ─────────────────────────────────────────────────────────────────────────────
# History ("memory" of past analyses — paste, upload, and PR reviews)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/history")
async def list_history(
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> dict:
    stmt = (
        select(AnalysisHistory)
        .where(AnalysisHistory.user_id == user.id)
        .order_by(AnalysisHistory.created_at.desc())
        .limit(100)
    )
    rows = (await session.execute(stmt)).scalars().all()
    return {"ok": True, "history": [
        {
            "id": r.id,
            "source": r.source,
            "label": r.label,
            "findings_count": r.findings_count,
            "security_count": r.security_count,
            "style_count": r.style_count,
            "created_at": r.created_at.isoformat(),
        }
        for r in rows
    ]}


@router.get("/history/{history_id}")
async def get_history_entry(
    history_id: int,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> dict:
    stmt = select(AnalysisHistory).where(
        AnalysisHistory.id == history_id,
        AnalysisHistory.user_id == user.id,
    )
    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=404, detail="History entry not found")
    return {
        "ok": True,
        "id": row.id,
        "source": row.source,
        "label": row.label,
        "created_at": row.created_at.isoformat(),
        "payload": json.loads(row.payload),
    }


@router.get("/health")
async def health(session: AsyncSession = Depends(get_session)) -> dict:
    await session.execute(text("SELECT 1"))
    pong = await redis_client.ping()
    return {"status": "ok", "database": "ok", "redis": "ok" if pong else "fail"}


# ─────────────────────────────────────────────────────────────────────────────
# Code Analysis (stateless — no GitHub needed)
# ─────────────────────────────────────────────────────────────────────────────

@router.post("/analyze/paste")
async def analyze_paste(req: PasteRequest) -> dict:
    result = await _code_analysis.analyze_paste(req.code, req.filename)
    return {"ok": True, "result": _asdict(result)}


@router.post("/analyze/upload")
async def analyze_upload(req: UploadRequest) -> dict:
    results = await _code_analysis.analyze_uploads(req.files)
    return {"ok": True, "results": _asdict(results)}


@router.post("/compare")
async def compare(req: CompareRequest) -> dict:
    result = await _snippet_compare.compare_snippets(req.before, req.after, req.filename)
    return {"ok": True, "result": _asdict(result)}


@router.post("/fix")
async def fix(
    req: FixRequest,
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> dict:
    result = await _fix_suggester.suggest_fixes(req.code, req.filename)
    security_count = len(result.analysis.security_findings)
    style_count = len(result.analysis.style_findings)
    source = req.source if req.source in ("paste", "upload") else "paste"
    await _record_history(
        session, user.id, source, req.filename,
        security_count, style_count,
        {
            "code": req.code,
            "filename": req.filename,
            "result": {
                "analysis": {
                    "security_findings": _asdict(result.analysis.security_findings),
                    "style_findings": _asdict(result.analysis.style_findings),
                },
                "suggestions": _asdict(result.suggestions),
            },
        },
    )
    return {"ok": True, "result": _asdict(result)}


# ─────────────────────────────────────────────────────────────────────────────
# PR Analysis (requires GitHub token)
# ─────────────────────────────────────────────────────────────────────────────

@router.get("/pr/files/content")
async def pr_files_content(
    owner: str = Query(...),
    repo: str = Query(...),
    pr_number: int = Query(...),
    github_token: str = Depends(get_github_token),
) -> dict:
    analysis_svc, _, _ = _make_services(github_token)
    pr = await analysis_svc._repo.get_pr(owner, repo, pr_number)
    files = await analysis_svc._repo.get_pr_files(owner, repo, pr_number)

    file_contents = []
    for f in files[:5]:  # limit to 5 files
        if f.status == "removed":
            continue
        try:
            head_content = await analysis_svc._repo.get_file_content(owner, repo, f.filename, pr.head_sha)
            try:
                base_content = await analysis_svc._repo.get_file_content(owner, repo, f.filename, pr.base_sha)
            except Exception:
                base_content = ""
            file_contents.append({
                "filename": f.filename,
                "before": base_content,
                "after": head_content,
                "status": f.status,
                "additions": f.additions,
                "deletions": f.deletions,
            })
        except Exception:
            continue

    return {"ok": True, "files": file_contents}


@router.get("/pr/diff")
async def pr_diff(
    owner: str = Query(...),
    repo: str = Query(...),
    pr_number: int = Query(...),
    github_token: str = Depends(get_github_token),
) -> dict:
    analysis_svc, _, _ = _make_services(github_token)
    raw_diff = await analysis_svc._repo.get_pr_diff(owner, repo, pr_number)
    files = await analysis_svc._repo.get_pr_files(owner, repo, pr_number)
    return {
        "ok": True,
        "raw_diff": raw_diff,
        "files": [_asdict(f) for f in files],
    }


@router.post("/pr/analyze")
async def pr_analyze(
    req: PRRequest,
    github_token: str = Depends(get_github_token),
    user: dict = Depends(require_auth),
    session: AsyncSession = Depends(get_session),
) -> dict:
    analysis_svc, _, _ = _make_services(github_token)
    result = await analysis_svc.full_analysis(req.owner, req.repo, req.pr_number)
    await _record_history(
        session, user.id, "pr", f"{req.owner}/{req.repo}#{req.pr_number}",
        len(result.security_findings), len(result.style_findings),
        {
            "owner": req.owner, "repo": req.repo, "pr_number": req.pr_number,
            "result": {
                "security_findings": _asdict(result.security_findings),
                "style_findings": _asdict(result.style_findings),
                "files_changed": result.files_changed,
                "additions": result.additions,
                "deletions": result.deletions,
            },
        },
    )
    return {"ok": True, "result": _asdict(result)}


@router.get("/pr/context")
async def pr_context(
    owner: str = Query(...),
    repo: str = Query(...),
    pr_number: int = Query(...),
    github_token: str = Depends(get_github_token),
) -> dict:
    _, context_svc, _ = _make_services(github_token)
    result = await context_svc.get_pr_context(owner, repo, pr_number)
    return {"ok": True, "result": _asdict(result)}


@router.get("/pr/reviewers")
async def pr_reviewers(
    owner: str = Query(...),
    repo: str = Query(...),
    pr_number: int = Query(...),
    github_token: str = Depends(get_github_token),
) -> dict:
    _, context_svc, _ = _make_services(github_token)
    result = await context_svc.suggest_reviewers(owner, repo, pr_number)
    return {"ok": True, "result": _asdict(result)}


@router.post("/pr/review")
async def pr_review(
    req: PostReviewRequest,
    github_token: str = Depends(get_github_token),
) -> dict:
    _, _, review_svc = _make_services(github_token)
    result = await review_svc.post_review(
        req.owner, req.repo, req.pr_number,
        body=req.body,
        event=req.event,
        comments=req.comments,
        confirmed=req.confirmed,
    )
    return {"ok": True, "result": result}


# ─────────────────────────────────────────────────────────────────────────────
# Chat — Claude API tool loop with SSE streaming
# ─────────────────────────────────────────────────────────────────────────────

# Anthropic SDK tool definitions (mirrors the 14 MCP tools)
_PR_ARGS = {
    "type": "object",
    "properties": {
        "owner": {"type": "string"},
        "repo": {"type": "string"},
        "pr_number": {"type": "integer"},
    },
    "required": ["owner", "repo", "pr_number"],
}

TOOLS_SCHEMA = [
    {"name": "get_pr_summary", "description": "Return PR metadata: title, author, additions/deletions, state, URL.", "input_schema": _PR_ARGS},
    {"name": "analyze_diff", "description": "Run semantic diff pipeline on a PR. Returns chunks grouped by classification with complexity scores.", "input_schema": _PR_ARGS},
    {"name": "check_security_issues", "description": "Scan PR diff for SEC001-005: secrets, SQL injection, insecure deps, missing validation, unsafe deserialization.", "input_schema": _PR_ARGS},
    {"name": "check_style_violations", "description": "Check PR diff against repo's reviewmind.yaml conventions (STY001-006).", "input_schema": _PR_ARGS},
    {"name": "get_pr_context", "description": "Enrich PR with context: recent file contributors, related PRs, linked issues.", "input_schema": _PR_ARGS},
    {"name": "suggest_reviewers", "description": "Suggest best reviewers based on commit history and CODEOWNERS matches.", "input_schema": _PR_ARGS},
    {"name": "get_review_history", "description": "Return all existing review decisions and inline comments on a PR.", "input_schema": _PR_ARGS},
    {"name": "generate_review_comment", "description": "Format a finding as a GitHub-ready Markdown comment. Styles: concise, detailed, educational.", "input_schema": {
        "type": "object",
        "properties": {
            "finding": {"type": "object"},
            "comment_style": {"type": "string", "enum": ["concise", "detailed", "educational"]},
        },
        "required": ["finding"],
    }},
    {"name": "analyze_paste", "description": "Analyze pasted code without a PR. Runs full pipeline: chunking, security scan, style check.", "input_schema": {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "filename": {"type": "string", "default": "snippet.py"},
        },
        "required": ["code"],
    }},
    {"name": "analyze_upload", "description": "Analyze uploaded files without a PR. Returns results per file.", "input_schema": {
        "type": "object",
        "properties": {
            "files": {"type": "array", "items": {"type": "object", "properties": {"name": {"type": "string"}, "content": {"type": "string"}}, "required": ["name", "content"]}},
        },
        "required": ["files"],
    }},
    {"name": "compare_snippets", "description": "Compare two code versions: synthesizes diff, runs full analysis, returns complexity delta.", "input_schema": {
        "type": "object",
        "properties": {
            "before": {"type": "string"},
            "after": {"type": "string"},
            "filename": {"type": "string", "default": "snippet.py"},
        },
        "required": ["before", "after"],
    }},
    {"name": "suggest_fixes", "description": "Analyze code and return concrete fix suggestions per finding with code examples.", "input_schema": {
        "type": "object",
        "properties": {
            "code": {"type": "string"},
            "filename": {"type": "string", "default": "snippet.py"},
        },
        "required": ["code"],
    }},
    {"name": "post_review", "description": "Post a review to GitHub. Always call with confirmed=false first to preview, then confirmed=true to post.", "input_schema": {
        "type": "object",
        "properties": {
            "owner": {"type": "string"},
            "repo": {"type": "string"},
            "pr_number": {"type": "integer"},
            "body": {"type": "string"},
            "event": {"type": "string", "enum": ["APPROVE", "REQUEST_CHANGES", "COMMENT"]},
            "comments": {"type": "array", "items": {"type": "object"}, "default": []},
            "confirmed": {"type": "boolean", "default": False},
        },
        "required": ["owner", "repo", "pr_number", "body", "event"],
    }},
]


# Tools that call the GitHub API — every one of these must run as the
# calling user via their own linked token. No shared server-wide fallback,
# ever: if the caller has no token, the tool refuses instead of silently
# acting as someone else.
_GITHUB_TOOLS = {
    "get_pr_summary", "analyze_diff", "check_security_issues", "check_style_violations",
    "get_pr_context", "suggest_reviewers", "get_review_history", "post_review",
}


async def _run_tool(name: str, args: dict, github_token: str | None = None) -> str:
    """Execute a tool by name and return a JSON string result."""
    if name in _GITHUB_TOOLS:
        if not github_token:
            return json.dumps({
                "error": "This needs your own GitHub account — sign in with GitHub to continue.",
            })
        analysis_svc, context_svc, review_svc = _make_services(github_token)

    match name:
        case "get_pr_summary":
            return _to_json(await analysis_svc.get_pr_summary(args["owner"], args["repo"], args["pr_number"]))
        case "analyze_diff":
            return _to_json(await analysis_svc.get_chunks(args["owner"], args["repo"], args["pr_number"]))
        case "check_security_issues":
            return _to_json(await analysis_svc.get_security_findings(args["owner"], args["repo"], args["pr_number"]))
        case "check_style_violations":
            return _to_json(await analysis_svc.get_style_findings(args["owner"], args["repo"], args["pr_number"]))
        case "get_pr_context":
            return _to_json(await context_svc.get_pr_context(args["owner"], args["repo"], args["pr_number"]))
        case "suggest_reviewers":
            return _to_json(await context_svc.suggest_reviewers(args["owner"], args["repo"], args["pr_number"]))
        case "get_review_history":
            return _to_json(await review_svc.get_review_history(args["owner"], args["repo"], args["pr_number"]))
        case "generate_review_comment":
            # Pure formatting over a finding dict — no GitHub call, no token needed.
            from reviewmind.services.review_service import ReviewService
            return json.dumps(ReviewService(None).generate_review_comment(args["finding"], args.get("comment_style", "concise")))
        case "analyze_paste":
            return _to_json(await _code_analysis.analyze_paste(args["code"], args.get("filename", "snippet.py")))
        case "analyze_upload":
            return _to_json(await _code_analysis.analyze_uploads(args["files"]))
        case "compare_snippets":
            return _to_json(await _snippet_compare.compare_snippets(args["before"], args["after"], args.get("filename", "snippet.py")))
        case "suggest_fixes":
            return _to_json(await _fix_suggester.suggest_fixes(args["code"], args.get("filename", "snippet.py")))
        case "post_review":
            return _to_json(await review_svc.post_review(
                args["owner"], args["repo"], args["pr_number"],
                body=args["body"],
                event=args["event"],
                comments=args.get("comments", []),
                confirmed=args.get("confirmed", False),
            ))
        case _:
            return json.dumps({"error": f"Unknown tool: {name}"})


def _build_user_content(req: ChatRequest) -> str:
    parts = [req.message]
    if req.code:
        parts.append(f"\n\nCode to analyze:\n```\n{req.code}\n```")
    if req.files:
        for f in req.files:
            parts.append(f"\n\nFile `{f.get('name', 'unknown')}`:\n```\n{f.get('content', '')}\n```")
    if req.pr:
        parts.append(f"\n\nPR: {req.pr.get('owner')}/{req.pr.get('repo')} #{req.pr.get('pr_number')}")
    return "".join(parts)


def _sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data)}\n\n"


async def _chat_stream(req: ChatRequest, github_token: str | None = None):
    import anthropic

    if not settings.anthropic_api_key:
        yield _sse("error", {"message": "ANTHROPIC_API_KEY not set in .env"})
        return

    client = anthropic.AsyncAnthropic(api_key=settings.anthropic_api_key)
    messages = [{"role": "user", "content": _build_user_content(req)}]
    system = (
        "You are ReviewMind, an AI-powered code review assistant. "
        "You have tools to analyze GitHub PRs and raw code for security issues, "
        "style violations, and semantic changes. "
        "Be concise, direct, and actionable. Always call post_review with confirmed=false first."
    )

    try:
        while True:
            tool_uses = []
            assistant_content = []

            async with client.messages.stream(
                model=settings.anthropic_model,
                max_tokens=4096,
                system=system,
                tools=TOOLS_SCHEMA,
                messages=messages,
            ) as stream:
                current_tool: dict | None = None

                async for event in stream:
                    etype = event.type

                    if etype == "content_block_start":
                        block = event.content_block
                        if block.type == "text":
                            pass
                        elif block.type == "tool_use":
                            current_tool = {"id": block.id, "name": block.name, "input_str": ""}
                            tool_uses.append(current_tool)
                            yield _sse("tool_call", {"name": block.name, "id": block.id})

                    elif etype == "content_block_delta":
                        delta = event.delta
                        if delta.type == "text_delta":
                            yield _sse("token", {"text": delta.text})
                        elif delta.type == "input_json_delta" and current_tool is not None:
                            current_tool["input_str"] += delta.partial_json

                    elif etype == "content_block_stop":
                        current_tool = None

                final = await stream.get_final_message()
                assistant_content = final.content

            if final.stop_reason == "end_turn" or not tool_uses:
                break

            # Execute all tool calls
            tool_results = []
            for tc in tool_uses:
                try:
                    args = json.loads(tc.get("input_str") or "{}")
                    result = await _run_tool(tc["name"], args, github_token)
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tc["id"],
                        "content": result,
                    })
                    yield _sse("tool_result", {"tool_id": tc["id"], "name": tc["name"]})
                    logger.info("chat_tool_executed", tool=tc["name"])
                except Exception as exc:
                    tool_results.append({
                        "type": "tool_result",
                        "tool_use_id": tc["id"],
                        "content": json.dumps({"error": str(exc)}),
                        "is_error": True,
                    })

            messages.append({"role": "assistant", "content": assistant_content})
            messages.append({"role": "user", "content": tool_results})

        yield _sse("done", {"message": "complete"})

    except Exception as exc:
        logger.error("chat_stream_error", error=str(exc))
        yield _sse("error", {"message": str(exc)})


@router.post("/chat")
async def chat(
    req: ChatRequest,
    github_token: str | None = Depends(get_optional_github_token),
) -> StreamingResponse:
    return StreamingResponse(
        _chat_stream(req, github_token),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )
