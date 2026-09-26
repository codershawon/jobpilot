"""
পাইপলাইন এন্ডপয়েন্ট।

সিকিউরিটি পরিবর্তন:
  - /run, /search, /match তিনটাতেই রেট লিমিট
  - /run-এ ফাইল যাচাই (সাইজ, টাইপ, magic bytes)
  - /saved, /save-এ আসল JWT যাচাই
  - /search এখন Pydantic model ব্যবহার করে, হাতে হাতে request.json() পার্স নয়
"""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Request, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_optional_user
from app.core.database import get_db
from app.core.security import RateLimiter, read_validated_cv
from app.db.models import CandidateProfile, User
from app.models import (
    FullPipelineResponse,
    JobMatchRequest,
    JobMatchResponse,
    JobSearchResponse,
)
from app.services.cv_parser import parse_cv
from app.services.job_fetcher import aggregate_all_jobs, aggregate_jobs_by_profile
from app.services.job_store import query_jobs
from app.core.database import get_db
from app.services.job_store import query_jobs
from app.services.matcher import match_and_score_jobs, process_matching_pipeline

router = APIRouter(prefix="/pipeline", tags=["Pipeline & Jobs"])


# ──────────────────────────────────────────────────────────
# রিকোয়েস্ট মডেল — validation বিনামূল্যে পাওয়া যায়
# ──────────────────────────────────────────────────────────
class SearchRequest(BaseModel):
    keywords: List[str] = Field(default_factory=list, max_length=10)
    districts: List[str] = Field(default_factory=list, max_length=10)
    sectors: List[str] = Field(default_factory=list, max_length=8)
    job_function: Optional[str] = None
    hide_expired: bool = True
    sort_by: str = "relevance"      # relevance | deadline
    live: bool = False              # true হলে লাইভ স্ক্র্যাপ
    include_remote: bool = True
    include_gov: bool = True
    source: Optional[str] = None
    job_type: Optional[str] = None
    limit_per_source: int = Field(default=20, ge=1, le=50)


# ──────────────────────────────────────────────────────────
# ১. জব সার্চ — ঘণ্টায় ৩০ বার
# ──────────────────────────────────────────────────────────
@router.post(
    "/search",
    response_model=JobSearchResponse,
    dependencies=[Depends(RateLimiter("search", limit=30, window_seconds=3600))],
)
async def search_jobs(payload: SearchRequest, db: AsyncSession = Depends(get_db)):
    only_gov = (payload.source or "").lower() == "govt" or (
        payload.job_type or ""
    ).lower() == "government"

    districts = [d for d in payload.districts if d and d != "All"]

    if not payload.live:
        db_jobs = await query_jobs(
            db,
            sectors=payload.sectors or None,
            job_function=payload.job_function,
            district=districts[0] if districts else None,
            source=payload.source,
            hide_expired=payload.hide_expired,
            limit=500,
        )
        if db_jobs:
            return JobSearchResponse(total_found=len(db_jobs), jobs=db_jobs)

    jobs = await aggregate_all_jobs(
        keywords=payload.keywords,
        districts=districts,
        include_remote=payload.include_remote,
        include_gov=payload.include_gov,
        only_gov=only_gov,
        limit_per_source=payload.limit_per_source,
    )

    # সেক্টর ফিল্টার — একটাও মিললেই রাখা হবে
    if payload.sectors:
        wanted = set(payload.sectors)
        jobs = [j for j in jobs if wanted & set(j.sectors or [])]

    # কাজের ক্ষেত্র ফিল্টার
    if payload.job_function and payload.job_function != "ALL":
        jobs = [j for j in jobs if j.job_function == payload.job_function]

    # মেয়াদ শেষ হওয়া সার্কুলার দেখিয়ে লাভ নেই
    if payload.hide_expired:
        jobs = [j for j in jobs if j.urgency != "expired"]

    if payload.sort_by == "deadline":
        # তারিখ নেই এমনগুলো সবার শেষে
        jobs.sort(key=lambda j: j.days_left if j.days_left is not None else 9999)

    # মেয়াদ শেষ হওয়া সার্কুলার দেখিয়ে লাভ নেই
    if payload.hide_expired:
        jobs = [j for j in jobs if j.urgency != "expired"]

    if payload.sort_by == "deadline":
        # তারিখ নেই এমনগুলো সবার শেষে
        jobs.sort(key=lambda j: j.days_left if j.days_left is not None else 9999)

    return JobSearchResponse(total_found=len(jobs), jobs=jobs)


# ──────────────────────────────────────────────────────────
# ২. ম্যাচিং — LLM খরচ হয়, তাই কড়া লিমিট
# ──────────────────────────────────────────────────────────
@router.post(
    "/match",
    response_model=JobMatchResponse,
    dependencies=[Depends(RateLimiter("match", limit=20, window_seconds=3600))],
)
async def match_jobs_endpoint(payload: JobMatchRequest):
    # একবারে অগুনতি জব পাঠিয়ে কোটা শেষ করা ঠেকাতে
    jobs = payload.jobs[:300]

    matched = await match_and_score_jobs(
        profile=payload.profile,
        jobs=jobs,
        top_k_cover_letters=min(payload.generate_cover_letters_for_top, 5),
    )
    return JobMatchResponse(matched_jobs=matched)


# ──────────────────────────────────────────────────────────
# ৩. পুরো পাইপলাইন — সবচেয়ে দামি, তাই সবচেয়ে কড়া
# ──────────────────────────────────────────────────────────
@router.post(
    "/run",
    response_model=FullPipelineResponse,
    dependencies=[Depends(RateLimiter("run", limit=5, window_seconds=3600))],
)
async def run_full_pipeline(
    request: Request,
    file: UploadFile = File(...),
    user_id: str | None = Depends(get_optional_user),
):
    # রেট লিমিটার যেন IP নয়, ইউজার ধরে হিসাব করে
    request.state.user_id = user_id

    contents = await read_validated_cv(file)     # সাইজ + টাইপ + magic bytes

    cv_res = await parse_cv(contents, file.filename or "resume.pdf")
    profile = cv_res.profile

    keywords = profile.preferred_job_titles or profile.skills[:3] or ["Web Developer"]
    fetched = await aggregate_jobs_by_profile(
        keywords=keywords,
        user_district=profile.district or "Dhaka",
    )
    matched = await process_matching_pipeline(profile, fetched)

    return FullPipelineResponse(
        profile=profile,
        total_found=len(matched),
        matched_jobs=matched,
    )


# ──────────────────────────────────────────────────────────
# ৪. সংরক্ষিত ডেটা — লগইন বাধ্যতামূলক, JWT যাচাই সহ
# ──────────────────────────────────────────────────────────
@router.get("/saved")
async def get_saved_pipeline(
    clerk_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CandidateProfile).join(User).where(User.clerk_id == clerk_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()

    if not profile:
        return {"profile": None, "total_found": 0, "matched_jobs": []}
    return profile.parsed_data


@router.post(
    "/save",
    dependencies=[Depends(RateLimiter("save", limit=60, window_seconds=3600))],
)
async def save_pipeline_state(
    payload: FullPipelineResponse,
    clerk_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    res = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = res.scalar_one_or_none()

    if not user:
        user = User(clerk_id=clerk_id)
        db.add(user)
        await db.flush()

    res = await db.execute(
        select(CandidateProfile).where(CandidateProfile.user_id == user.id)
    )
    profile = res.scalar_one_or_none()

    # অতিরিক্ত বড় payload আটকাতে
    data = payload.model_dump()
    data["matched_jobs"] = data.get("matched_jobs", [])[:300]

    if profile:
        profile.parsed_data = data
    else:
        db.add(CandidateProfile(user_id=user.id, parsed_data=data))

    await db.commit()
    return {"status": "saved"}