"""
সিকিউরিটি হেল্পার: রেট লিমিট, আপলোড যাচাই, সিকিউরিটি হেডার।

রেট লিমিটার আপাতত ইন-মেমরি। একাধিক worker চালালে (প্রোডাকশনে) এটা
Redis-ভিত্তিক করতে হবে — নিচে TODO দেওয়া আছে।
"""

import time
from collections import defaultdict, deque

from fastapi import HTTPException, Request, UploadFile, status

from app.config import settings

# ──────────────────────────────────────────────────────────
# ১. রেট লিমিটার
# ──────────────────────────────────────────────────────────
_hits: dict[str, deque[float]] = defaultdict(deque)


def _client_id(request: Request, user_id: str | None = None) -> str:
    """লগইন থাকলে user id, নইলে IP। প্রক্সির পেছনে হলে X-Forwarded-For।"""
    if user_id:
        return f"user:{user_id}"
    fwd = request.headers.get("x-forwarded-for")
    ip = fwd.split(",")[0].strip() if fwd else (
        request.client.host if request.client else "unknown"
    )
    return f"ip:{ip}"


class RateLimiter:
    """
    ব্যবহার:
        @router.post("/run", dependencies=[Depends(RateLimiter("run", 5, 3600))])
    """

    def __init__(self, name: str, limit: int, window_seconds: int):
        self.name = name
        self.limit = limit
        self.window = window_seconds

    async def __call__(self, request: Request) -> None:
        # ইউজার আইডি থাকলে সেটাই ব্যবহার করি (মিডলওয়্যার বসিয়ে দেয়)
        user_id = getattr(request.state, "user_id", None)
        key = f"{self.name}:{_client_id(request, user_id)}"

        now = time.time()
        bucket = _hits[key]

        while bucket and now - bucket[0] > self.window:
            bucket.popleft()

        if len(bucket) >= self.limit:
            retry_after = int(self.window - (now - bucket[0])) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"অনেক বেশি অনুরোধ। {retry_after} সেকেন্ড পরে আবার চেষ্টা করুন।",
                headers={"Retry-After": str(retry_after)},
            )

        bucket.append(now)

        # মেমরি বাড়তে না দেওয়ার জন্য মাঝে মাঝে পরিষ্কার
        if len(_hits) > 10_000:
            stale = [k for k, v in _hits.items() if not v or now - v[-1] > 3600]
            for k in stale:
                _hits.pop(k, None)


# TODO (প্রোডাকশন): একাধিক worker হলে Redis-এ সরাও —
#   INCR key / EXPIRE key window


# ──────────────────────────────────────────────────────────
# ২. আপলোড যাচাই
# ──────────────────────────────────────────────────────────
ALLOWED_CV_EXTENSIONS = (".pdf", ".docx")
ALLOWED_CV_MIMETYPES = {
    "application/pdf",
    "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "application/octet-stream",  # কিছু ব্রাউজার এটা পাঠায়
}

# ফাইলের আসল শুরুর বাইট (এক্সটেনশন বদলে দিলেও ধরা পড়বে)
_MAGIC = {
    b"%PDF": ".pdf",
    b"PK\x03\x04": ".docx",   # docx আসলে একটা zip
}


async def read_validated_cv(file: UploadFile) -> bytes:
    """
    CV ফাইল নিরাপদে পড়ে। সাইজ, এক্সটেনশন আর আসল ফাইল টাইপ তিনটাই যাচাই করে।
    """
    filename = (file.filename or "").lower()

    if not filename.endswith(ALLOWED_CV_EXTENSIONS):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="শুধু .pdf এবং .docx ফাইল সাপোর্ট করা হয়।",
        )

    if file.content_type and file.content_type not in ALLOWED_CV_MIMETYPES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ফাইলের ধরন সমর্থিত নয়।",
        )

    max_bytes = settings.MAX_UPLOAD_MB * 1024 * 1024
    chunks: list[bytes] = []
    total = 0

    # একবারে পুরো ফাইল মেমোরিতে না নিয়ে টুকরো টুকরো পড়া
    while chunk := await file.read(64 * 1024):
        total += len(chunk)
        if total > max_bytes:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail=f"ফাইল {settings.MAX_UPLOAD_MB} MB-এর বেশি হতে পারবে না।",
            )
        chunks.append(chunk)

    contents = b"".join(chunks)

    if not contents:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ফাইলটি খালি।",
        )

    # magic bytes — .exe কে .pdf নাম দিয়ে পাঠালে এখানে ধরা পড়বে
    if not any(contents.startswith(sig) for sig in _MAGIC):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="ফাইলটি বৈধ PDF বা DOCX নয়।",
        )

    return contents


# ──────────────────────────────────────────────────────────
# ৩. সিকিউরিটি হেডার মিডলওয়্যার
# ──────────────────────────────────────────────────────────
async def security_headers_middleware(request: Request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
    if settings.APP_ENV == "production":
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains"
        )
    return response