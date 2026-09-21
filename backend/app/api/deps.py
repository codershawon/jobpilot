"""
Clerk JWT যাচাইকরণ।

আগের ভার্সনে jwt.get_unverified_claims() ব্যবহার হতো — signature চেক
হতো না, তাই যে কেউ হাতে বানানো টোকেন দিয়ে অন্যের ডেটা পড়তে পারত।

এখন Clerk-এর পাবলিক JWKS দিয়ে signature, expiry আর issuer তিনটাই যাচাই হয়।
"""

import time
from typing import Any

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt

from app.config import settings

security = HTTPBearer(auto_error=False)

# ── JWKS ক্যাশ (Clerk-এর পাবলিক কী, ঘন ঘন আনার দরকার নেই) ──
_jwks_cache: dict[str, Any] = {}
_jwks_fetched_at: float = 0.0
_JWKS_TTL = 3600  # ১ ঘণ্টা


async def _get_jwks() -> dict[str, Any]:
    global _jwks_cache, _jwks_fetched_at

    if _jwks_cache and (time.time() - _jwks_fetched_at) < _JWKS_TTL:
        return _jwks_cache

    if not settings.CLERK_ISSUER:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Auth is not configured on the server.",
        )

    url = f"{settings.CLERK_ISSUER.rstrip('/')}/.well-known/jwks.json"
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(url)
            res.raise_for_status()
            _jwks_cache = res.json()
            _jwks_fetched_at = time.time()
            return _jwks_cache
    except Exception as e:  # noqa: BLE001
        # পুরনো ক্যাশ থাকলে সেটা দিয়ে চালিয়ে নাও, নইলে থামো
        if _jwks_cache:
            return _jwks_cache
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Could not reach the auth provider.",
        ) from e


def _unauthorized(detail: str = "Could not validate credentials") -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=detail,
        headers={"WWW-Authenticate": "Bearer"},
    )


async def _decode(token: str) -> dict[str, Any]:
    jwks = await _get_jwks()

    try:
        header = jwt.get_unverified_header(token)
    except JWTError as e:
        raise _unauthorized("Malformed token") from e

    kid = header.get("kid")
    key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if key is None:
        # কী ঘোরানো হয়ে থাকতে পারে — একবার রিফ্রেশ করে দেখি
        global _jwks_fetched_at
        _jwks_fetched_at = 0.0
        jwks = await _get_jwks()
        key = next((k for k in jwks.get("keys", []) if k.get("kid") == kid), None)
    if key is None:
        raise _unauthorized("Unknown signing key")

    try:
        return jwt.decode(
            token,
            key,
            algorithms=["RS256"],
            issuer=settings.CLERK_ISSUER.rstrip("/"),
            options={
                "verify_signature": True,
                "verify_exp": True,
                "verify_iss": True,
                "verify_aud": False,   # Clerk ডিফল্ট টোকেনে aud থাকে না
            },
        )
    except JWTError as e:
        raise _unauthorized(f"Invalid token: {type(e).__name__}") from e


# ──────────────────────────────────────────────────────────
# নির্ভরতা (dependencies)
# ──────────────────────────────────────────────────────────
async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str:
    """লগইন বাধ্যতামূলক। Clerk user id ফেরত দেয়।"""
    if credentials is None or not credentials.credentials:
        raise _unauthorized("Missing bearer token")

    claims = await _decode(credentials.credentials)

    sub = claims.get("sub")
    if not sub:
        raise _unauthorized("Token has no subject")

    # azp = authorized party. আমাদের নিজের ফ্রন্টএন্ড থেকেই এসেছে কিনা।
    if settings.CLERK_ALLOWED_PARTIES:
        azp = claims.get("azp")
        if azp and azp not in settings.CLERK_ALLOWED_PARTIES:
            raise _unauthorized("Token issued for a different application")

    return sub


async def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
) -> str | None:
    """লগইন ঐচ্ছিক। গেস্ট হলে None, লগইন থাকলে যাচাই করে id।"""
    if credentials is None or not credentials.credentials:
        return None
    try:
        claims = await _decode(credentials.credentials)
        return claims.get("sub")
    except HTTPException:
        return None


# পুরনো নামের সাথে সামঞ্জস্য
get_current_clerk_user = get_current_user