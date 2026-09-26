"""
Telegram নোটিফিকেশন।

নকশার নিয়ম: **নোটিফিকেশন ব্যর্থ হলে অ্যাপ থামবে না।** ইউজার বট ব্লক
করেছে, টোকেন ভুল, নেটওয়ার্ক বন্ধ — সব ক্ষেত্রেই চুপচাপ False ফেরত যাবে।

Telegram-এর সীমা: সেকেন্ডে ~৩০টা মেসেজ। তাই পাঠানোর মাঝে ছোট বিরতি
দেওয়া হয়, নইলে 429 খেয়ে মেসেজ হারাবে।
"""

from __future__ import annotations

import asyncio
import html
import logging

import httpx

from app.config import settings
from app.models import JobItem

logger = logging.getLogger("jobpilot.telegram")

API = "https://api.telegram.org"
SEND_DELAY = 0.05      # সেকেন্ডে ~২০টা, নিরাপদ সীমার নিচে


def _enabled() -> bool:
    return bool(getattr(settings, "TELEGRAM_BOT_TOKEN", ""))


def _esc(text: str) -> str:
    """Telegram-এর HTML মোডে < > & এস্কেপ করতে হয়।"""
    return html.escape(text or "", quote=False)


# ══════════════════════════════════════════════════════════
# ১. মেসেজ পাঠানো
# ══════════════════════════════════════════════════════════
async def send_message(
    chat_id: str | int,
    text: str,
    *,
    buttons: list[list[dict]] | None = None,
    preview: bool = False,
) -> bool:
    if not _enabled():
        logger.debug("TELEGRAM_BOT_TOKEN নেই — মেসেজ পাঠানো হলো না")
        return False

    url = f"{API}/bot{settings.TELEGRAM_BOT_TOKEN}/sendMessage"
    payload: dict = {
        "chat_id": str(chat_id),
        "text": text[:4000],           # Telegram-এর সীমা ৪০৯৬
        "parse_mode": "HTML",
        "link_preview_options": {"is_disabled": not preview},
    }
    if buttons:
        payload["reply_markup"] = {"inline_keyboard": buttons}

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.post(url, json=payload)
            if res.status_code == 200:
                return True

            body = res.text[:200]
            if res.status_code == 403:
                logger.info("ইউজার বট ব্লক করেছে: %s", chat_id)
            elif res.status_code == 429:
                logger.warning("Telegram রেট লিমিট: %s", body)
            else:
                logger.warning("Telegram %s: %s", res.status_code, body)
            return False
    except Exception as e:  # noqa: BLE001
        logger.warning("Telegram পাঠাতে ব্যর্থ: %s", e)
        return False


# ══════════════════════════════════════════════════════════
# ২. জবের মেসেজ তৈরি
# ══════════════════════════════════════════════════════════
_URGENCY_ICON = {
    "critical": "🔴",
    "urgent": "🟠",
    "soon": "🟡",
    "normal": "🟢",
    "unknown": "⚪",
    "expired": "⚫",
}


def _deadline_line(job: JobItem) -> str:
    d = job.days_left
    if d is None:
        return ""
    if d < 0:
        return "মেয়াদ শেষ"
    if d == 0:
        return "<b>আজই শেষ দিন</b>"
    if d == 1:
        return "<b>আগামীকাল শেষ</b>"
    return f"{d} দিন বাকি"


def format_job(job: JobItem, index: int | None = None) -> str:
    icon = _URGENCY_ICON.get(job.urgency or "unknown", "⚪")
    prefix = f"{index}. " if index else ""

    lines = [f"{icon} {prefix}<b>{_esc(job.title)}</b>"]
    if job.company:
        lines.append(_esc(job.company))

    meta: list[str] = []
    if job.district and job.district not in ("", "Bangladesh"):
        meta.append(_esc(job.district))
    deadline = _deadline_line(job)
    if deadline:
        meta.append(deadline)
    if meta:
        lines.append(" · ".join(meta))

    if job.url:
        lines.append(f'<a href="{_esc(job.url)}">আবেদন করুন →</a>')

    return "\n".join(lines)


# ══════════════════════════════════════════════════════════
# ৩. দৈনিক ডাইজেস্ট
# ══════════════════════════════════════════════════════════
async def send_new_jobs_digest(
    chat_id: str | int,
    jobs: list[JobItem],
    *,
    name: str | None = None,
) -> bool:
    """নতুন জবের তালিকা। প্রতিটার জন্য আলাদা মেসেজ নয় — একটাই,
    নইলে ইউজার বিরক্ত হয়ে বট ব্লক করবে।"""
    if not jobs:
        return False

    greeting = f"সুপ্রভাত{', ' + _esc(name) if name else ''}!"
    header = f"🔔 {greeting}\n<b>{len(jobs)}টি নতুন সার্কুলার আপনার প্রোফাইলের সাথে মিলেছে</b>\n"

    body = "\n\n".join(format_job(j, i + 1) for i, j in enumerate(jobs[:8]))

    footer = ""
    if len(jobs) > 8:
        footer = f"\n\n<i>আরও {len(jobs) - 8}টি আছে — ড্যাশবোর্ডে দেখুন</i>"

    return await send_message(chat_id, f"{header}\n{body}{footer}")


# ══════════════════════════════════════════════════════════
# ৪. ডেডলাইন রিমাইন্ডার
# ══════════════════════════════════════════════════════════
async def send_deadline_reminder(
    chat_id: str | int,
    jobs: list[JobItem],
) -> bool:
    if not jobs:
        return False

    critical = [j for j in jobs if (j.days_left or 99) <= 1]
    header = (
        "⏰ <b>ডেডলাইন ঘনিয়ে আসছে</b>\n"
        f"{len(jobs)}টি পদের আবেদন শীঘ্রই শেষ"
        + (f" — এর মধ্যে {len(critical)}টি আজ/কাল" if critical else "")
        + "\n"
    )

    body = "\n\n".join(format_job(j, i + 1) for i, j in enumerate(jobs[:6]))
    return await send_message(chat_id, f"{header}\n{body}")


# ══════════════════════════════════════════════════════════
# ৫. অ্যাকাউন্ট যুক্ত হওয়ার বার্তা
# ══════════════════════════════════════════════════════════
async def send_welcome(chat_id: str | int, name: str | None = None) -> bool:
    text = (
        f"✅ <b>যুক্ত হয়েছে{', ' + _esc(name) if name else ''}!</b>\n\n"
        "এখন থেকে আপনি পাবেন:\n"
        "• প্রতিদিন সকালে নতুন সার্কুলারের তালিকা\n"
        "• ডেডলাইনের ৭, ৩ ও ১ দিন আগে মনে করিয়ে দেওয়া\n"
        "• আপনার CV-র সাথে মেলে এমন পদের খবর\n\n"
        "<i>বন্ধ করতে /stop লিখুন।</i>"
    )
    return await send_message(chat_id, text)


# ══════════════════════════════════════════════════════════
# ৬. অনেকজনকে পাঠানো
# ══════════════════════════════════════════════════════════
async def broadcast(messages: list[tuple[str, str]]) -> int:
    """[(chat_id, text)] তালিকা। কতজনের কাছে গেল সেটা ফেরত দেয়।
    রেট লিমিট এড়াতে একটার পর একটা, ছোট বিরতি দিয়ে।"""
    sent = 0
    for chat_id, text in messages:
        if await send_message(chat_id, text):
            sent += 1
        await asyncio.sleep(SEND_DELAY)
    return sent


# ══════════════════════════════════════════════════════════
# ৭. বট ঠিক আছে কিনা
# ══════════════════════════════════════════════════════════
async def check_bot() -> dict | None:
    if not _enabled():
        return None
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            res = await client.get(f"{API}/bot{settings.TELEGRAM_BOT_TOKEN}/getMe")
            if res.status_code == 200:
                return res.json().get("result")
    except Exception as e:  # noqa: BLE001
        logger.warning("getMe ব্যর্থ: %s", e)
    return None