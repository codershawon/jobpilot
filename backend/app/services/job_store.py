"""
জব ডাটাবেসে রাখা ও পড়া।

কেন দরকার: ক্যাশ ৩০ মিনিট পরে মুছে যায়, তাই "গতকাল কী ছিল, আজ নতুন কী
এলো" বলা যায় না। ডাটাবেসে রাখলে বলা যায় — আর সেটাই নোটিফিকেশনের ভিত্তি।

মূল ধারণা: JobItem.id একটা স্থিতিশীল হ্যাশ (source + url), তাই সেটাকেই
প্রাইমারি কি বানানো হয়েছে। একই সার্কুলার দশবার ফেচ হলেও একটাই সারি
থাকবে, শুধু last_seen_at আপডেট হবে।
"""

from __future__ import annotations

import logging
from datetime import date, datetime, timedelta
from typing import Sequence

from sqlalchemy import select, update
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.models import Job
from app.models import JobItem
from app.services.deadline import days_until, urgency_of

logger = logging.getLogger("jobpilot.store")


# ══════════════════════════════════════════════════════════
# ১. JobItem ↔ Job রূপান্তর
# ══════════════════════════════════════════════════════════
def _to_row(job: JobItem) -> dict:
    return {
        "id": job.id,
        "title": (job.title or "")[:512],
        "company": (job.company or "")[:512],
        "location": (job.location or "")[:256],
        "district": (job.district or "")[:128],
        "is_remote": bool(job.is_remote),
        "job_type": (job.job_type or "Local")[:64],
        "source": (job.source or "")[:64],
        "url": job.url or "",
        "description": (job.description or "")[:4000],
        "salary": (job.salary or "")[:256],
        "posted_date": (job.posted_date or "")[:64],
        "sectors": job.sectors or ["private"],
        "job_function": job.job_function or "general",
        "tags": job.tags or [],
        "deadline": job.deadline,
        "is_active": True,
    }


def _to_item(row: Job) -> JobItem:
    """ডাটাবেস সারি থেকে JobItem। days_left ও urgency এখানেই হিসাব হয়,
    কারণ ওগুলো প্রতিদিন বদলায় — সংরক্ষণ করলে বাসি হয়ে যেত।"""
    left = days_until(row.deadline)
    return JobItem(
        id=row.id,
        title=row.title,
        company=row.company,
        location=row.location,
        district=row.district,
        is_remote=row.is_remote,
        job_type=row.job_type,
        source=row.source,
        url=row.url,
        description=row.description,
        salary=row.salary,
        tags=row.tags or [],
        posted_date=row.posted_date,
        match_score=50,
        match_reason="",
        cover_letter="",
        status="SAVED",
        sectors=row.sectors or ["private"],
        job_function=row.job_function,
        deadline=row.deadline,
        days_left=left,
        urgency=urgency_of(left),
    )


# ══════════════════════════════════════════════════════════
# ২. সেভ করা — নতুনগুলো ফেরত দেয়
# ══════════════════════════════════════════════════════════
async def upsert_jobs(db: AsyncSession, jobs: Sequence[JobItem]) -> list[str]:
    """
    জবগুলো ডাটাবেসে বসায়। যেগুলো আগে ছিল না, তাদের id ফেরত দেয় —
    ঠিক সেগুলোর জন্যই নোটিফিকেশন পাঠাতে হবে।

    Postgres-এর ON CONFLICT ব্যবহার করা হয়, তাই ৫০০টা জবের জন্য
    ৫০০টা SELECT চালাতে হয় না।
    """
    if not jobs:
        return []

    incoming = {j.id: j for j in jobs if j.id}
    if not incoming:
        return []

    # আগে থেকে কোনগুলো আছে
    existing = set(
        (await db.execute(select(Job.id).where(Job.id.in_(incoming.keys()))))
        .scalars()
        .all()
    )
    new_ids = [jid for jid in incoming if jid not in existing]

    rows = [_to_row(j) for j in incoming.values()]

    try:
        stmt = pg_insert(Job).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Job.id],
            set_={
                "last_seen_at": datetime.utcnow(),
                "is_active": True,
                "deadline": stmt.excluded.deadline,
                "sectors": stmt.excluded.sectors,
                "job_function": stmt.excluded.job_function,
            },
        )
        await db.execute(stmt)
        await db.commit()
    except Exception as e:  # noqa: BLE001
        await db.rollback()
        logger.warning("upsert ব্যর্থ, একটা একটা করে চেষ্টা: %s", e)
        return await _upsert_one_by_one(db, incoming, existing)

    logger.info("%d জব সেভ, %d নতুন", len(rows), len(new_ids))
    return new_ids


async def _upsert_one_by_one(
    db: AsyncSession, incoming: dict[str, JobItem], existing: set[str]
) -> list[str]:
    """SQLite-এ বা bulk ব্যর্থ হলে ফলব্যাক। ধীর, কিন্তু নির্ভরযোগ্য।"""
    new_ids: list[str] = []
    for jid, item in incoming.items():
        try:
            if jid in existing:
                await db.execute(
                    update(Job)
                    .where(Job.id == jid)
                    .values(last_seen_at=datetime.utcnow(), is_active=True)
                )
            else:
                db.add(Job(**_to_row(item)))
                new_ids.append(jid)
        except Exception:  # noqa: BLE001
            continue
    try:
        await db.commit()
    except Exception:  # noqa: BLE001
        await db.rollback()
        return []
    return new_ids


# ══════════════════════════════════════════════════════════
# ৩. পড়া
# ══════════════════════════════════════════════════════════
async def query_jobs(
    db: AsyncSession,
    *,
    sectors: list[str] | None = None,
    job_function: str | None = None,
    district: str | None = None,
    source: str | None = None,
    hide_expired: bool = True,
    max_days_left: int | None = None,
    limit: int = 500,
) -> list[JobItem]:
    stmt = select(Job).where(Job.is_active.is_(True))

    if job_function and job_function != "ALL":
        stmt = stmt.where(Job.job_function == job_function)
    if source and source != "ALL":
        stmt = stmt.where(Job.source == source)
    if district and district != "ALL":
        stmt = stmt.where(Job.district.ilike(f"%{district}%"))

    if hide_expired:
        # ডেডলাইন নেই এমনগুলোও রাখি — রিমোট জবে ডেডলাইন থাকে না
        stmt = stmt.where((Job.deadline.is_(None)) | (Job.deadline >= date.today()))

    if max_days_left is not None:
        cutoff = date.today() + timedelta(days=max_days_left)
        stmt = stmt.where(Job.deadline.is_not(None), Job.deadline <= cutoff)

    stmt = stmt.order_by(Job.deadline.asc().nulls_last()).limit(limit)

    rows = (await db.execute(stmt)).scalars().all()
    items = [_to_item(r) for r in rows]

    # sectors একটা JSON অ্যারে, তাই ফিল্টার Python-এ
    if sectors:
        wanted = set(sectors)
        items = [i for i in items if wanted & set(i.sectors or [])]

    return items


async def jobs_since(db: AsyncSession, since: datetime, limit: int = 200) -> list[JobItem]:
    """নির্দিষ্ট সময়ের পর যেসব জব প্রথম দেখা গেছে — নোটিফিকেশনের জন্য।"""
    stmt = (
        select(Job)
        .where(Job.first_seen_at >= since, Job.is_active.is_(True))
        .order_by(Job.first_seen_at.desc())
        .limit(limit)
    )
    rows = (await db.execute(stmt)).scalars().all()
    return [_to_item(r) for r in rows]


async def deactivate_expired(db: AsyncSession) -> int:
    """ডেডলাইন পেরিয়ে যাওয়া জব নিষ্ক্রিয় করে। মুছে ফেলা হয় না —
    কারণ ইউজারের আবেদনের ইতিহাস ওগুলোর সাথে জোড়া থাকতে পারে।"""
    try:
        res = await db.execute(
            update(Job)
            .where(
                Job.is_active.is_(True),
                Job.deadline.is_not(None),
                Job.deadline < date.today(),
            )
            .values(is_active=False)
        )
        await db.commit()
        return res.rowcount or 0
    except Exception as e:  # noqa: BLE001
        await db.rollback()
        logger.warning("deactivate ব্যর্থ: %s", e)
        return 0