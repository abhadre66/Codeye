from __future__ import annotations

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from reviewmind.api.supabase_client import get_supabase

_bearer = HTTPBearer(auto_error=False)


async def require_auth(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> dict:
    if not credentials:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    try:
        supabase = get_supabase()
        response = supabase.auth.get_user(credentials.credentials)
        if not response.user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
        return response.user
    except HTTPException:
        raise
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token")


async def get_github_token(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    user: dict = Depends(require_auth),
) -> str:
    supabase = get_supabase()

    # Try profile table first (token stored at sign-in via trigger)
    try:
        result = supabase.table("profiles").select("github_token").eq("id", user.id).single().execute()
        token = result.data.get("github_token") if result.data else None
        if token:
            return token
    except Exception:
        pass

    # Fall back: re-verify session to get live provider_token
    try:
        response = supabase.auth.get_user(credentials.credentials)
        # provider_token is in identities or session — not always available server-side
        # If we got here, token wasn't persisted at sign-in; user must re-auth
    except Exception:
        pass

    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="GitHub token not found — please sign out and sign in again with GitHub",
    )
