from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from reviewmind.api.routes import router
from reviewmind.core.logging import configure_logging, get_logger
from reviewmind.services.github.client import (
    ForbiddenError,
    GitHubError,
    NotFoundError,
    RateLimitError,
)

configure_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("app_startup")
    yield
    logger.info("app_shutdown")


app = FastAPI(title="ReviewMind", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://*.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


# GitHub errors carry a machine-readable "code" so the frontend can branch
# (e.g. show a "Reconnect GitHub" button on permission failures) without
# string-matching messages.
def _github_error_response(status: int, code: str, detail: str) -> JSONResponse:
    return JSONResponse(status_code=status, content={"detail": detail, "code": code})


@app.exception_handler(ForbiddenError)
async def forbidden_handler(request: Request, exc: ForbiddenError):
    logger.warning("github_permission_denied", path=str(request.url.path), error=str(exc))
    return _github_error_response(
        403,
        "github_permission_denied",
        "GitHub denied this action. Your GitHub connection may be missing "
        "permissions — try reconnecting GitHub.",
    )


@app.exception_handler(RateLimitError)
async def rate_limit_handler(request: Request, exc: RateLimitError):
    return _github_error_response(
        429, "github_rate_limited", "GitHub rate limit exceeded. Try again shortly."
    )


@app.exception_handler(NotFoundError)
async def not_found_handler(request: Request, exc: NotFoundError):
    return _github_error_response(
        404,
        "github_not_found",
        "Not found on GitHub. The repo or PR may not exist, or your GitHub "
        "connection can't see it — try reconnecting GitHub.",
    )


@app.exception_handler(GitHubError)
async def github_error_handler(request: Request, exc: GitHubError):
    logger.warning("github_error", path=str(request.url.path), error=str(exc))
    if exc.status_code == 422:
        msg = str(exc)
        if "must be part of the diff" in msg or "could not be resolved" in msg.lower():
            return _github_error_response(
                422,
                "comment_line_not_in_diff",
                "One or more inline comments point to lines that aren't part "
                "of this PR's diff. Try posting as a summary instead.",
            )
        if "approve your own pull request" in msg.lower():
            return _github_error_response(
                422,
                "cannot_approve_own_pr",
                "GitHub does not allow approving your own pull request. "
                "Use Comment or Request Changes instead.",
            )
        return _github_error_response(422, "github_unprocessable", msg)
    return _github_error_response(502, "github_error", str(exc))
