from fastapi import APIRouter, Depends, UploadFile, File, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import (
    FullPipelineResponse,
    JobSearchQuery,
    JobSearchResponse,
    JobMatchRequest,
    JobMatchResponse
)
from app.services.cv_parser import parse_cv
from app.services.job_fetcher import aggregate_jobs_by_profile, aggregate_all_jobs
from app.services.matcher import process_matching_pipeline, match_and_score_jobs
from app.core.database import get_db
from app.db.models import User, CandidateProfile
from app.api.deps import get_current_clerk_user

router = APIRouter(prefix="/pipeline", tags=["Pipeline & Jobs"])

@router.post("/search", response_model=JobSearchResponse)
async def search_jobs(query: JobSearchQuery):
    jobs = await aggregate_all_jobs(
        keywords=query.keywords,
        districts=query.districts,
        include_remote=query.include_remote,
        include_gov=query.include_gov,
        limit_per_source=query.limit_per_source
    )
    return JobSearchResponse(total_found=len(jobs), jobs=jobs)

@router.post("/match", response_model=JobMatchResponse)
async def match_jobs_endpoint(payload: JobMatchRequest):
    matched_jobs = await match_and_score_jobs(
        profile=payload.profile,
        jobs=payload.jobs,
        top_k_cover_letters=payload.generate_cover_letters_for_top
    )
    return JobMatchResponse(matched_jobs=matched_jobs)

@router.post("/run", response_model=FullPipelineResponse)
async def run_full_pipeline(file: UploadFile = File(...)):
    if not file.filename.lower().endswith((".pdf", ".docx")):
        raise HTTPException(status_code=400, detail="Only .pdf and .docx are supported.")
    
    contents = await file.read()
    cv_res = await parse_cv(contents, file.filename)
    profile = cv_res.profile

    user_district = profile.district or "Cumilla"
    search_keywords = profile.preferred_job_titles or profile.skills[:3] or ["Web Developer"]

    fetched_jobs = await aggregate_jobs_by_profile(
        keywords=search_keywords,
        user_district=user_district
    )

    matched_jobs = await process_matching_pipeline(profile, fetched_jobs)

    return FullPipelineResponse(
        profile=profile,
        total_found=len(matched_jobs),
        matched_jobs=matched_jobs
    )

# ডাটাবেজ থেকে ইউজারের সংরক্ষিত ডাটা ফেচ
@router.get("/saved")
async def get_saved_pipeline(
    clerk_id: str = Depends(get_current_clerk_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(CandidateProfile).join(User).where(User.clerk_id == clerk_id)
    result = await db.execute(stmt)
    profile = result.scalar_one_or_none()
    
    if not profile:
        return {"profile": None, "total_found": 0, "matched_jobs": []}
    return profile.parsed_data

# ডাটাবেজে ইউজারের পাইপলাইন ডাটা সেভ
@router.post("/save")
async def save_pipeline_state(
    payload: FullPipelineResponse,
    clerk_id: str = Depends(get_current_clerk_user),
    db: AsyncSession = Depends(get_db)
):
    stmt = select(User).where(User.clerk_id == clerk_id)
    res = await db.execute(stmt)
    user = res.scalar_one_or_none()

    if not user:
        user = User(clerk_id=clerk_id)
        db.add(user)
        await db.flush()

    profile_stmt = select(CandidateProfile).where(CandidateProfile.user_id == user.id)
    profile_res = await db.execute(profile_stmt)
    profile = profile_res.scalar_one_or_none()

    payload_dict = payload.model_dump()

    if profile:
        profile.parsed_data = payload_dict
    else:
        profile = CandidateProfile(user_id=user.id, parsed_data=payload_dict)
        db.add(profile)

    await db.commit()
    return {"status": "saved"}