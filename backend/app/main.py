from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.core.database import engine
from app.api.v1.pipeline import router as pipeline_router


# ১. প্রোডাকশনে /docs ও /redoc বন্ধ রাখার কনফিগ
docs_url = "/docs" if settings.APP_ENV != "production" else None
redoc_url = "/redoc" if settings.APP_ENV != "production" else None


@asynccontextmanager
async def lifespan(app: FastAPI):
    # স্টার্টআপ চেক
    yield


# ২. FastAPI ইনিশিয়ালাইজেশন
app = FastAPI(
    title="JobPilot API",
    docs_url=docs_url,
    redoc_url=redoc_url,
    lifespan=lifespan,
)


# ৩. নির্দিষ্ট অরিজিনের জন্য CORS লক করা
origins = [
    "https://jobpilot-plum-omega.vercel.app",
    "http://localhost:3000",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ৪. রাউটার সংযুক্ত করা
app.include_router(pipeline_router, prefix="/api")


@app.get("/")
async def root():
    return {"status": "healthy", "service": "JobPilot Backend"}