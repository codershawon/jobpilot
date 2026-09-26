"""
আবেদন ট্র্যাকার।

এতদিন "Applied" শুধু localStorage-এ ছিল — ব্রাউজার বদলালে বা ক্লিয়ার
করলে সব হারিয়ে যেত। এখন ডাটাবেসে, তাই যেকোনো ডিভাইস থেকে দেখা যাবে।

সরকারি চাকরির জন্য tracking_id, fee_paid, admit_downloaded আর exam_date
রাখা হয় — প্রবেশপত্র নামাতে ট্র্যাকিং নম্বরই লাগে, আর মানুষ সেটা হারায়।
"""

from __future__ import annotations

from datetime import date, datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user
from app.core.database import get_db
from app.core.security import RateLimiter
from app.db.models import Application, Job, User
from app.services.deadline import days_until, urgency_of

router = APIRouter(prefix="/applications", tags=["Applications"])

VALID_STATUSES = ("SAVED", "APPLIED", "EXAM", "INTERVIEW", "OFFER", "REJECTED")


# ══════════════════════════════════════════════════════════
# স্কিমা
# ══════════════════════════════════════════════════════════
class ApplicationCreate(BaseModel):
    job_id: str = Field(..., max_length=32)
    status: str = "APPLIED"
    notes: str = ""
    tracking_id: Optional[str] = None

    # জব ডাটাবেসে না থাকলে এগুলো থেকে সারি বানানো হবে
    title: Optional[str] = None
    company: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    district: Optional[str] = None
    deadline: Optional[date] = None


class ApplicationUpdate(BaseModel):
    status: Optional[str] = None
    notes: Optional[str] = None
    tracking_id: Optional[str] = None
    fee_paid: Optional[bool] = None
    admit_downloaded: Optional[bool] = None
    exam_date: Optional[date] = None


class ApplicationOut(BaseModel):
    id: str
    job_id: str
    status: str
    tracking_id: Optional[str] = None
    fee_paid: bool = False
    admit_downloaded: bool = False
    exam_date: Optional[date] = None
    notes: str = ""
    applied_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    # জবের তথ্য — ফ্রন্টএন্ডে আলাদা কল না লাগার জন্য
    title: str = ""
    company: str = ""
    url: str = ""
    source: str = ""
    district: str = ""
    deadline: Optional[date] = None
    days_left: Optional[int] = None
    urgency: str = "unknown"


def _to_out(app: Application) -> ApplicationOut:
    """জব মুছে গেলেও snapshot থেকে দেখানো যায়।"""
    snap = app.job_snapshot or {}
    job = app.job

    deadline = job.deadline if job else None
    left = days_until(deadline)

    return ApplicationOut(
        id=str(app.id),
        job_id=app.job_id,
        status=app.status,
        tracking_id=app.tracking_id,
        fee_paid=app.fee_paid,
        admit_downloaded=app.admit_downloaded,
        exam_date=app.exam_date,
        notes=app.notes or "",
        applied_at=app.applied_at,
        updated_at=app.updated_at,
        title=(job.title if job else snap.get("title", "")),
        company=(job.company if job else snap.get("company", "")),
        url=(job.url if job else snap.get("url", "")),
        source=(job.source if job else snap.get("source", "")),
        district=(job.district if job else snap.get("district", "")),
        deadline=deadline,
        days_left=left,
        urgency=urgency_of(left),
    )


async def _get_user(db: AsyncSession, clerk_id: str) -> User:
    res = await db.execute(select(User).where(User.clerk_id == clerk_id))
    user = res.scalar_one_or_none()
    if not user:
        user = User(clerk_id=clerk_id)
        db.add(user)
        await db.flush()
    return user


# ══════════════════════════════════════════════════════════
# ১. ড্যাশবোর্ডের সংখ্যা — নির্দিষ্ট পাথ, তাই {id} রুটের আগে
# ══════════════════════════════════════════════════════════
@router.get("/stats")
async def application_stats(
    clerk_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(db, clerk_id)

    rows = (
        await db.execute(
            select(Application)
            .options(selectinload(Application.job))
            .where(Application.user_id == user.id)
        )
    ).scalars().all()

    counts = {s: 0 for s in VALID_STATUSES}
    upcoming_exams = 0

    for a in rows:
        counts[a.status] = counts.get(a.status, 0) + 1
        if a.exam_date and a.exam_date >= date.today():
            upcoming_exams += 1

    return {
        "total": len(rows),
        "by_status": counts,
        "upcoming_exams": upcoming_exams,
    }


# ══════════════════════════════════════════════════════════
# ২. তালিকা
# ══════════════════════════════════════════════════════════
@router.get("", response_model=List[ApplicationOut])
async def list_applications(
    status_filter: Optional[str] = None,
    clerk_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(db, clerk_id)

    stmt = (
        select(Application)
        .options(selectinload(Application.job))
        .where(Application.user_id == user.id)
        .order_by(Application.updated_at.desc())
    )
    if status_filter and status_filter != "ALL":
        stmt = stmt.where(Application.status == status_filter)

    rows = (await db.execute(stmt)).scalars().all()
    return [_to_out(a) for a in rows]


# ══════════════════════════════════════════════════════════
# ৩. যোগ করা বা আপডেট
# ══════════════════════════════════════════════════════════
@router.post(
    "",
    response_model=ApplicationOut,
    dependencies=[Depends(RateLimiter("app_create", limit=200, window_seconds=3600))],
)
async def create_application(
    payload: ApplicationCreate,
    clerk_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if payload.status not in VALID_STATUSES:
        raise HTTPException(status.HTTP_400_BAD_REQUEST, "অবৈধ স্ট্যাটাস")

    user = await _get_user(db, clerk_id)

    job = (
        await db.execute(select(Job).where(Job.id == payload.job_id))
    ).scalar_one_or_none()
    # ডাটাবেসে না থাকলে ফ্রন্টএন্ডের পাঠানো তথ্য দিয়ে সারি বানাই
    if not job:
        if not payload.title:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "জব পাওয়া যায়নি — Sync Jobs চেপে আবার চেষ্টা করুন",
            )
        job = Job(
            id=payload.job_id,
            title=payload.title[:512],
            company=(payload.company or "")[:512],
            url=payload.url or "",
            source=(payload.source or "manual")[:64],
            district=(payload.district or "")[:128],
            deadline=payload.deadline,
            sectors=["private"],
            job_function="general",
            is_active=True,
        )
        db.add(job)
        await db.flush()

    existing = (
        await db.execute(
            select(Application)
            .options(selectinload(Application.job))
            .where(
                Application.user_id == user.id,
                Application.job_id == payload.job_id,
            )
        )
    ).scalar_one_or_none()

    if existing:
        existing.status = payload.status
        if payload.notes:
            existing.notes = payload.notes
        if payload.tracking_id:
            existing.tracking_id = payload.tracking_id
        if payload.status == "APPLIED" and not existing.applied_at:
            existing.applied_at = datetime.utcnow()
        await db.commit()
        return _to_out(existing)

    app_row = Application(
        user_id=user.id,
        job_id=payload.job_id,
        status=payload.status,
        notes=payload.notes,
        tracking_id=payload.tracking_id,
        applied_at=datetime.utcnow() if payload.status == "APPLIED" else None,
        # জব মুছে গেলেও ইউজার যেন দেখতে পায় কোথায় আবেদন করেছিল
        job_snapshot={
            "title": job.title,
            "company": job.company,
            "url": job.url,
            "source": job.source,
            "district": job.district,
            "deadline": str(job.deadline) if job.deadline else None,
        },
    )
    db.add(app_row)
    await db.commit()
    await db.refresh(app_row, ["job"])
    return _to_out(app_row)


# ══════════════════════════════════════════════════════════
# ৪. সম্পাদনা
# ══════════════════════════════════════════════════════════
@router.patch("/{application_id}", response_model=ApplicationOut)
async def update_application(
    application_id: str,
    payload: ApplicationUpdate,
    clerk_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(db, clerk_id)

    app_row = (
        await db.execute(
            select(Application)
            .options(selectinload(Application.job))
            .where(Application.id == application_id, Application.user_id == user.id)
        )
    ).scalar_one_or_none()

    if not app_row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "পাওয়া যায়নি")

    if payload.status is not None:
        if payload.status not in VALID_STATUSES:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "অবৈধ স্ট্যাটাস")
        app_row.status = payload.status
        if payload.status == "APPLIED" and not app_row.applied_at:
            app_row.applied_at = datetime.utcnow()

    for field in ("notes", "tracking_id", "fee_paid", "admit_downloaded", "exam_date"):
        value = getattr(payload, field)
        if value is not None:
            setattr(app_row, field, value)

    await db.commit()
    return _to_out(app_row)


# ══════════════════════════════════════════════════════════
# ৫. মুছে ফেলা
# ══════════════════════════════════════════════════════════
@router.delete("/{application_id}")
async def delete_application(
    application_id: str,
    clerk_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = await _get_user(db, clerk_id)

    app_row = (
        await db.execute(
            select(Application).where(
                Application.id == application_id, Application.user_id == user.id
            )
        )
    ).scalar_one_or_none()

    if not app_row:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "পাওয়া যায়নি")

    await db.delete(app_row)
    await db.commit()
    return {"status": "deleted"}