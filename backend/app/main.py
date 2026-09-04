import os
import json
from app.config import settings

DATA_FILE = os.path.join(settings.DATA_DIR, "saved_pipeline.json")
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List

from app.models import (
    CVProfile, 
    JobItem,
    CVParseResponse,
    JobSearchQuery,
    JobSearchResponse,
    JobMatchRequest,
    JobMatchResponse,
    FullPipelineResponse
)
from app.cv_parser import parse_cv
from app.job_fetcher import aggregate_jobs_by_profile, aggregate_all_jobs
from app.matcher import process_matching_pipeline, match_and_score_jobs
from app.district_service import get_all_districts
from fastapi.responses import StreamingResponse
from app.autonomous_agent import AutonomousAgent
from pydantic import BaseModel

app = FastAPI(
    title="JobPilot API",
    description="Autonomous Profile Parser & District/Worldwide Job Matcher",
    version="1.0.0"
)

# CORS Enabled for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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

# বাংলাদেশের ৬৪ জেলার তালিকা এপিআই
@app.get("/api/districts")
async def fetch_districts():
    districts = await get_all_districts()
    return {"total": len(districts), "districts": districts}

# সোশ্যাল ও এক্সটারনাল সার্চ লিংক হেল্পার
@app.get("/api/jobs/external-links")
def get_external_job_links(keyword: str = "React Developer", location: str = "Bangladesh"):
    return {
        "linkedin_search": f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location={location}",
        "indeed_search": f"https://bd.indeed.com/jobs?q={keyword}&l={location}",
        "glassdoor_search": f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={keyword}&locT=C&locId=1",
        "facebook_jobs_search": f"https://www.facebook.com/search/posts/?q={keyword}%20job%20{location}"
    }

# ১. শুধু সিভি আপলোড ও পার্সিং
@app.post("/api/cv/upload", response_model=CVParseResponse)
async def upload_cv(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only .pdf and .docx are supported.")
    contents = await file.read()
    return await parse_cv(contents, file.filename)

# ২. কাস্টম জব সার্চ
@app.post("/api/jobs/search", response_model=JobSearchResponse)
async def search_jobs(query: JobSearchQuery):
    jobs = await aggregate_all_jobs(
        keywords=query.keywords,
        districts=query.districts,
        include_remote=query.include_remote,
        include_gov=query.include_gov,
        limit_per_source=query.limit_per_source
    )
    return JobSearchResponse(total_found=len(jobs), jobs=jobs)

# ৩. কাস্টম জব ম্যাচিং
@app.post("/api/jobs/match", response_model=JobMatchResponse)
async def match_jobs_endpoint(payload: JobMatchRequest):
    matched_jobs = await match_and_score_jobs(
        profile=payload.profile,
        jobs=payload.jobs,
        top_k_cover_letters=payload.generate_cover_letters_for_top
    )
    return JobMatchResponse(matched_jobs=matched_jobs)

# ৪. সম্পূর্ণ ওয়ান-ক্লিক অটোমেটেড পাইপলাইন (LinkedIn, Remotive, Bdjobs, Internshala সহ)
@app.post("/api/pipeline/run", response_model=FullPipelineResponse)
async def run_full_pipeline(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only .pdf and .docx are supported.")
    
    # Step 1: CV Parsing
    contents = await file.read()
    cv_res = await parse_cv(contents, file.filename)
    profile = cv_res.profile

    # জেলা এবং স্কিলস ডিটেকশন
    user_district = profile.district or "Cumilla"
    search_keywords = profile.preferred_job_titles or profile.skills[:3] or ["Web Developer"]

    # Step 2: Multi-source Fetching
    fetched_jobs = await aggregate_jobs_by_profile(
        keywords=search_keywords,
        user_district=user_district
    )

    # Step 3: AI Matching & Cover Letter Generation
    matched_jobs = await process_matching_pipeline(profile, fetched_jobs)

    return FullPipelineResponse(
        profile=profile,
        total_found=len(matched_jobs),
        matched_jobs=matched_jobs
    )

    # ৫. পার্মানেন্ট সেভ করা পাইপলাইন ডাটা লোড
@app.get("/api/pipeline/saved")
def get_saved_pipeline():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"profile": None, "total_found": 0, "matched_jobs": []}

# ৬. পাইপলাইন স্টেট ব্যাকএন্ডে সেভ করা
@app.post("/api/pipeline/save")
def save_pipeline_state(payload: FullPipelineResponse):
    os.makedirs(settings.DATA_DIR, exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        f.write(payload.model_dump_json(indent=2))
    return {"status": "saved"}

class AgentBatchRequest(BaseModel):
    profile: CVProfile
    jobs: List[JobItem]

@app.post("/api/agent/stream-apply")
async def start_autonomous_batch_stream(payload: AgentBatchRequest):
    agent = AutonomousAgent(profile=payload.profile, jobs=payload.jobs)
    return StreamingResponse(
        agent.run_batch_with_logs(),
        media_type="text/event-stream"
    )