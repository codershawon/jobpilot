from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.database import engine
from app.db.models import Base
from app.api.v1.districts import router as districts_router
from app.api.v1.cv import router as cv_router
from app.api.v1.pipeline import router as pipeline_router
from app.api.v1.agent import router as agent_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield

app = FastAPI(
    title="JobPilot API",
    description="Autonomous Profile Parser & District/Worldwide Job Matcher",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# এপিআই রাউটার মাউন্ট করা
app.include_router(districts_router, prefix="/api")
app.include_router(cv_router, prefix="/api")
app.include_router(pipeline_router, prefix="/api")
app.include_router(agent_router, prefix="/api")

@app.get("/")
def root():
    return {
        "app": "JobPilot API",
        "status": "running",
        "docs_url": "/docs"
    }

@app.get("/api/health")
def health_check():
    return {"status": "ok"}