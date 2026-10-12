"""Telegram অ্যাকাউন্ট লিংকিং — one-time code + webhook।"""

import secrets

import httpx
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.config import settings
from app.core.cache import get_json, set_json
from app.core.database import get_db
from app.db.models import User

router = APIRouter(prefix="/telegram", tags=["Telegram"])

TG_API = f"https://api.telegram.org/bot{settings.TELEGRAM_BOT_TOKEN}"
_bot_username: str | None = None


async def _bot_name() -> str:
    global _bot_username
    if not _bot_username:
        async with httpx.AsyncClient(timeout=10) as c:
            r = await c.get(f"{TG_API}/getMe")
            _bot_username = r.json()["result"]["username"]
    return _bot_username


async def _send(chat_id, text: str) -> None:
    async with httpx.AsyncClient(timeout=10) as c:
        await c.post(f"{TG_API}/sendMessage", json={"chat_id": chat_id, "text": text})


@router.post("/link-code")
async def create_link_code(clerk_id: str = Depends(get_current_user)):
    """লগইন করা ইউজারের জন্য ১০ মিনিট মেয়াদের deep link।"""
    code = secrets.token_urlsafe(8)
    await set_json(f"tg:link:{code}", {"clerk_id": clerk_id}, ttl_seconds=600)
    return {"deep_link": f"https://t.me/{await _bot_name()}?start={code}"}


@router.get("/status")
async def telegram_status(
    clerk_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = (
        await db.execute(select(User).where(User.clerk_id == clerk_id))
    ).scalar_one_or_none()
    return {
        "connected": bool(user and user.telegram_chat_id),
        "notify_enabled": bool(user and user.notify_enabled),
    }


@router.delete("/disconnect")
async def disconnect(
    clerk_id: str = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    user = (
        await db.execute(select(User).where(User.clerk_id == clerk_id))
    ).scalar_one_or_none()
    if user:
        user.telegram_chat_id = None
        user.notify_enabled = False
        await db.commit()
    return {"connected": False}


@router.post("/webhook")
async def telegram_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_telegram_bot_api_secret_token: str | None = Header(default=None),
):
    if (
        settings.TELEGRAM_WEBHOOK_SECRET
        and x_telegram_bot_api_secret_token != settings.TELEGRAM_WEBHOOK_SECRET
    ):
        raise HTTPException(status_code=403)

    update = await request.json()
    msg = update.get("message") or {}
    chat_id = (msg.get("chat") or {}).get("id")
    text = (msg.get("text") or "").strip()
    if not chat_id:
        return {"ok": True}

    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        code = parts[1].strip() if len(parts) > 1 else ""
        data = await get_json(f"tg:link:{code}") if code else None
        if not data:
            await _send(chat_id, "লিংক কোডটি সঠিক নয় বা মেয়াদ শেষ। JobPilot থেকে আবার Connect চাপুন।")
            return {"ok": True}

        user = (
            await db.execute(select(User).where(User.clerk_id == data["clerk_id"]))
        ).scalar_one_or_none()
        if not user:
            user = User(clerk_id=data["clerk_id"])
            db.add(user)
        user.telegram_chat_id = str(chat_id)
        user.notify_enabled = True
        await db.commit()
        await _send(chat_id, "JobPilot-এর সাথে Telegram যুক্ত হয়েছে ✅ নতুন ম্যাচ আর ডেডলাইন অ্যালার্ট এখানেই আসবে।")

    elif text == "/stop":
        user = (
            await db.execute(select(User).where(User.telegram_chat_id == str(chat_id)))
        ).scalar_one_or_none()
        if user:
            user.notify_enabled = False
            await db.commit()
        await _send(chat_id, "নোটিফিকেশন বন্ধ হলো। আবার চালু করতে সাইট থেকে Connect করুন।")

    return {"ok": True}