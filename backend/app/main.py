"""
JobPilot API entrypoint.

সিকিউরিটি পরিবর্তন:
  - CORS origin settings থেকে আসে, হার্ডকোড নয়
  - production-এ /docs, /redoc, /openapi.json তিনটাই বন্ধ
  - সিকিউরিটি হেডার মিডলওয়্যার
  - অপ্রত্যাশিত এরর ইউজারকে stack trace দেখায় না
"""

import asyncio
import logging
import sys

# উইন্ডোজে Playwright সাবপ্রসেসের জন্য সবার আগে ইভেন্ট লুপ পলিসি
if sys.platform == "win32":
    try:
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    except Exception:  # noqa: BLE001
        pass

from contextlib import asynccontextmanager  # noqa: E402

from fastapi import FastAPI, Request  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.responses import JSONResponse  # noqa: E402

from app.config import settings  # noqa: E402
from app.core.security import security_headers_middleware  # noqa: E402

logger = logging.getLogger("jobpilot")

IS_PROD = settings.APP_ENV == "production"


@asynccontextmanager
async def lifespan(app: FastAPI):
    if IS_PROD and not settings.CLERK_ISSUER:
        raise RuntimeError(
            "CLERK_ISSUER সেট করা নেই — production-এ auth ছাড়া চালানো যাবে না।"
        )
    logger.info("JobPilot starting in %s mode", settings.APP_ENV)
    yield


app = FastAPI(
    title="JobPilot API",
    version="1.0.0",
    # production-এ তিনটাই None — API schema পাবলিক হবে না
    docs_url=None if IS_PROD else "/docs",
    redoc_url=None if IS_PROD else "/redoc",
    openapi_url=None if IS_PROD else "/openapi.json",
    lifespan=lifespan,
)

# ── সিকিউরিটি হেডার ──
app.middleware("http")(security_headers_middleware)

# ── CORS ──
# allow_origins-এ কখনো "*" দিও না যখন allow_credentials=True,
# কারণ তখন যেকোনো সাইট ইউজারের হয়ে রিকোয়েস্ট পাঠাতে পারে।
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
    max_age=600,
)


# ── অপ্রত্যাশিত এরর: ভিতরের কিছু ফাঁস করবে না ──
@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled error on %s %s", request.method, request.url.path)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"},
    )


# ── রাউটার ──
from app.api.v1.pipeline import router as pipeline_router  # noqa: E402

app.include_router(pipeline_router, prefix="/api")

try:
    from app.api.v1.districts import router as district_router

    app.include_router(district_router, prefix="/api")
except ImportError:
    logger.warning("districts router not found")

try:
    from app.api.v1.cv import router as cv_router

    app.include_router(cv_router, prefix="/api")
except ImportError:
    logger.warning("cv router not found")


@app.get("/")
async def root():
    return {"status": "healthy", "service": "JobPilot Backend"}


@app.get("/health")
async def health():
    return {"status": "ok", "env": settings.APP_ENV}