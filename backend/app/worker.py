"""
ব্যাকগ্রাউন্ড ওয়ার্কার।

কেন দরকার: এখন ইউজার সার্চ করলে তখনই ৯টা সোর্সে গিয়ে স্ক্র্যাপ হয় —
৩৩ সেকেন্ড লাগে, আর দুইটা Playwright একসাথে চললে টাইমআউট হয়।

এই ওয়ার্কার আগেভাগে কাজটা করে রাখে:
  প্রতি ৩০ মিনিটে → সব সোর্স থেকে ফেচ → ডাটাবেসে সেভ → নতুনগুলো বের করা
  প্রতিদিন সকাল ৯টায় → ইউজারদের নতুন জবের ডাইজেস্ট
  প্রতিদিন সকাল ১০টায় → ডেডলাইন রিমাইন্ডার

চালানো:
    python -m app.worker            # একটানা চলবে
    python -m app.worker --once     # একবার চালিয়ে থামবে
"""

from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timedelta

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.core.database import AsyncSessionLocal
from app.db.models import NotificationLog, User
from app.models import CVProfile, JobItem
from app.services import telegram
from app.services.job_fetcher import aggregate_all_jobs
from app.services.job_store import (
    deactivate_expired,
    jobs_since,
    query_jobs,
    upsert_jobs,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-7s %(name)s — %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("jobpilot.worker")

FETCH_INTERVAL = 30 * 60        # ৩০ মিনিট
DIGEST_HOUR = 9                 # সকাল ৯টা (সার্ভারের সময়)
DEADLINE_HOUR = 10              # সকাল ১০টা


# ══════════════════════════════════════════════════════════
# ১. ফেচ ও সেভ
# ══════════════════════════════════════════════════════════
# বিভিন্ন পেশার কি-ওয়ার্ড — একটা সেট দিয়ে সব ধরনের জব আনা যায় না
KEYWORD_SETS = [
    ["Developer", "Engineer", "Software"],
    ["Officer", "Assistant", "Executive"],
    ["Teacher", "Lecturer", "Instructor"],
    ["Accounts", "Finance", "Audit"],
    ["NGO", "Project Officer", "Field"],
]


async def fetch_and_store() -> list[JobItem]:
    """সব কি-ওয়ার্ড সেটে ফেচ করে ডাটাবেসে রাখে। নতুন জবগুলো ফেরত দেয়।

    সেটগুলো একটার পর একটা চালানো হয়, একসাথে নয় — কারণ Playwright
    একাধিক ব্রাউজার একসাথে সামলাতে পারে না।
    """
    all_new: list[JobItem] = []

    for i, keywords in enumerate(KEYWORD_SETS, 1):
        logger.info("[%d/%d] ফেচ: %s", i, len(KEYWORD_SETS), ", ".join(keywords))
        try:
            jobs = await aggregate_all_jobs(keywords=keywords)
        except Exception as e:  # noqa: BLE001
            logger.warning("ফেচ ব্যর্থ (%s): %s", keywords[0], e)
            continue

        async with AsyncSessionLocal() as db:
            new_ids = await upsert_jobs(db, jobs)
            if new_ids:
                new_set = set(new_ids)
                all_new.extend(j for j in jobs if j.id in new_set)

        await asyncio.sleep(3)   # সোর্সগুলোর উপর চাপ কমাতে

    async with AsyncSessionLocal() as db:
        expired = await deactivate_expired(db)

    logger.info("মোট নতুন: %d | মেয়াদোত্তীর্ণ নিষ্ক্রিয়: %d", len(all_new), expired)
    return all_new


# ══════════════════════════════════════════════════════════
# ২. কার কাছে কোন জব যাবে
# ══════════════════════════════════════════════════════════
def _relevance(job: JobItem, profile: dict) -> int:
    """সহজ স্কোর — LLM ছাড়াই। ওয়ার্কারে শত শত জবে LLM চালানো
    ব্যয়বহুল, আর নোটিফিকেশনের জন্য এটুকুই যথেষ্ট।"""
    score = 0

    fn = profile.get("job_function")
    if fn and fn != "general" and job.job_function == fn:
        score += 40

    skills = [s.lower() for s in (profile.get("skills") or [])]
    titles = [t.lower() for t in (profile.get("preferred_job_titles") or [])]
    haystack = f"{job.title} {' '.join(job.tags or [])}".lower()

    score += sum(15 for t in titles if t and t in haystack)
    score += sum(5 for s in skills if s and s in haystack)

    district = (profile.get("district") or "").lower()
    if district and district in (job.district or "").lower():
        score += 15

    if job.is_remote and profile.get("open_to_remote"):
        score += 10

    return min(score, 100)


async def _users_with_telegram(db) -> list[tuple[User, dict]]:
    """যাদের Telegram যুক্ত আছে আর নোটিফিকেশন চালু, তাদের তালিকা।

    selectinload অপরিহার্য — async মোডে lazy loading কাজ করে না,
    তাই profile আগেই একসাথে আনতে হবে।
    """
    stmt = (
        select(User)
        .options(selectinload(User.profile))
        .where(User.telegram_chat_id.is_not(None), User.notify_enabled.is_(True))
    )
    users = (await db.execute(stmt)).scalars().all()

    out: list[tuple[User, dict]] = []
    for u in users:
        profile: dict = {}
        if u.profile is not None and isinstance(u.profile.parsed_data, dict):
            profile = u.profile.parsed_data.get("profile") or {}
        out.append((u, profile))
    return out


async def _already_notified(db, user_id, job_id: str, kind: str) -> bool:
    stmt = select(NotificationLog.id).where(
        NotificationLog.user_id == user_id,
        NotificationLog.job_id == job_id,
        NotificationLog.kind == kind,
    )
    return (await db.execute(stmt)).first() is not None


async def _log_sent(db, user_id, job_ids: list[str], kind: str) -> None:
    for jid in job_ids:
        db.add(
            NotificationLog(
                user_id=user_id, job_id=jid, channel="telegram", kind=kind
            )
        )
    await db.commit()


# ══════════════════════════════════════════════════════════
# ৩. নতুন জবের ডাইজেস্ট
# ══════════════════════════════════════════════════════════
async def send_digests(min_score: int = 30) -> int:
    """গত ২৪ ঘণ্টার নতুন জব থেকে প্রত্যেকের জন্য প্রাসঙ্গিকগুলো বেছে পাঠায়।"""
    sent = 0

    async with AsyncSessionLocal() as db:
        recent = await jobs_since(db, datetime.utcnow() - timedelta(hours=24))
        if not recent:
            logger.info("গত ২৪ ঘণ্টায় নতুন জব নেই")
            return 0

        for user, profile in await _users_with_telegram(db):
            scored = [(j, _relevance(j, profile)) for j in recent]
            picks = [j for j, s in sorted(scored, key=lambda x: -x[1]) if s >= min_score]

            # আগে পাঠানো হয়নি এমনগুলো
            fresh = [
                j for j in picks[:10]
                if not await _already_notified(db, user.id, j.id, "new_match")
            ]
            if not fresh:
                continue

            ok = await telegram.send_new_jobs_digest(
                user.telegram_chat_id,
                fresh,
                name=profile.get("full_name"),
            )
            if ok:
                await _log_sent(db, user.id, [j.id for j in fresh], "new_match")
                sent += 1
            await asyncio.sleep(telegram.SEND_DELAY)

    logger.info("ডাইজেস্ট পাঠানো হয়েছে: %d জনকে", sent)
    return sent


# ══════════════════════════════════════════════════════════
# ৪. ডেডলাইন রিমাইন্ডার
# ══════════════════════════════════════════════════════════
async def send_deadline_reminders() -> int:
    """৭ দিনের মধ্যে শেষ হচ্ছে এমন প্রাসঙ্গিক জবের কথা মনে করিয়ে দেয়।"""
    sent = 0

    async with AsyncSessionLocal() as db:
        urgent = await query_jobs(db, max_days_left=7, limit=200)
        if not urgent:
            logger.info("জরুরি ডেডলাইন নেই")
            return 0

        for user, profile in await _users_with_telegram(db):
            scored = [(j, _relevance(j, profile)) for j in urgent]
            picks = [j for j, s in sorted(scored, key=lambda x: -x[1]) if s >= 30]

            fresh = [
                j for j in picks[:6]
                if not await _already_notified(db, user.id, j.id, "deadline")
            ]
            if not fresh:
                continue

            fresh.sort(key=lambda j: j.days_left if j.days_left is not None else 99)

            if await telegram.send_deadline_reminder(user.telegram_chat_id, fresh):
                await _log_sent(db, user.id, [j.id for j in fresh], "deadline")
                sent += 1
            await asyncio.sleep(telegram.SEND_DELAY)

    logger.info("ডেডলাইন রিমাইন্ডার: %d জনকে", sent)
    return sent


# ══════════════════════════════════════════════════════════
# ৫. মূল লুপ
# ══════════════════════════════════════════════════════════
async def run_once() -> None:
    logger.info("── একবার চালানো শুরু ──")
    await fetch_and_store()
    await send_digests()
    await send_deadline_reminders()
    logger.info("── শেষ ──")


async def run_forever() -> None:
    bot = await telegram.check_bot()
    if bot:
        logger.info("Telegram বট সক্রিয়: @%s", bot.get("username"))
    else:
        logger.warning("Telegram বট সংযুক্ত নয় — শুধু ফেচ চলবে")

    last_digest_day: int | None = None
    last_deadline_day: int | None = None

    while True:
        try:
            await fetch_and_store()

            now = datetime.now()
            if now.hour >= DIGEST_HOUR and last_digest_day != now.day:
                await send_digests()
                last_digest_day = now.day

            if now.hour >= DEADLINE_HOUR and last_deadline_day != now.day:
                await send_deadline_reminders()
                last_deadline_day = now.day

        except Exception as e:  # noqa: BLE001
            logger.exception("ওয়ার্কার চক্রে সমস্যা: %s", e)

        logger.info("পরবর্তী চক্র %d মিনিট পরে", FETCH_INTERVAL // 60)
        await asyncio.sleep(FETCH_INTERVAL)


def main() -> None:
    parser = argparse.ArgumentParser(description="JobPilot ব্যাকগ্রাউন্ড ওয়ার্কার")
    parser.add_argument("--once", action="store_true", help="একবার চালিয়ে থামবে")
    parser.add_argument("--fetch-only", action="store_true", help="শুধু ফেচ, নোটিফিকেশন নয়")
    args = parser.parse_args()

    if args.fetch_only:
        asyncio.run(fetch_and_store())
    elif args.once:
        asyncio.run(run_once())
    else:
        asyncio.run(run_forever())


if __name__ == "__main__":
    main()