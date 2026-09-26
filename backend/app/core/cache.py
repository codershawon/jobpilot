"""
ক্যাশ লেয়ার — Redis থাকলে Redis, না থাকলে ইন-মেমরি।

নকশার মূল নিয়ম: **ক্যাশ কখনো অ্যাপ থামাবে না।**
Redis ডাউন, নেটওয়ার্ক বন্ধ, ভুল URL — যাই হোক, ক্যাশ মিস হিসেবে
ধরে নিয়ে অ্যাপ স্বাভাবিকভাবে চলবে, শুধু ধীরে।

দুইটা কাজে ব্যবহার হয়:
  ১. জব সার্চের ফলাফল ধরে রাখা (৩০+ সেকেন্ড → ৫০ মিলিসেকেন্ড)
  ২. রেট লিমিট গোনা (একাধিক worker-এ একই হিসাব)
"""

from __future__ import annotations

import hashlib
import json
import logging
import time
from typing import Any

from app.config import settings

logger = logging.getLogger("jobpilot.cache")

# ── Redis ক্লায়েন্ট, লেজি ──
_redis: Any = None
_redis_tried = False

# ── ফলব্যাক: ইন-মেমরি ──
_mem: dict[str, tuple[float, str]] = {}   # key → (expires_at, json)
_mem_counters: dict[str, tuple[float, int]] = {}


async def _client():
    """Redis ক্লায়েন্ট, একবারই তৈরি হয়। না পারলে None।"""
    global _redis, _redis_tried

    if _redis is not None:
        return _redis
    if _redis_tried:
        return None

    _redis_tried = True
    url = getattr(settings, "REDIS_URL", "") or ""
    if not url:
        logger.info("REDIS_URL নেই — ইন-মেমরি ক্যাশ ব্যবহার হবে")
        return None

    try:
        from redis.asyncio import from_url

        client = from_url(url, encoding="utf-8", decode_responses=True)
        await client.ping()
        _redis = client
        logger.info("Redis সংযুক্ত")
        return _redis
    except Exception as e:  # noqa: BLE001
        logger.warning("Redis সংযোগ ব্যর্থ (%s) — ইন-মেমরি ক্যাশ চলবে", e)
        return None


# ══════════════════════════════════════════════════════════
# ১. সাধারণ get / set
# ══════════════════════════════════════════════════════════
async def get_json(key: str) -> Any | None:
    """ক্যাশ থেকে পড়ে। না পেলে বা কোনো সমস্যা হলে None।"""
    try:
        r = await _client()
        if r:
            raw = await r.get(key)
            return json.loads(raw) if raw else None

        hit = _mem.get(key)
        if not hit:
            return None
        expires_at, raw = hit
        if time.time() > expires_at:
            _mem.pop(key, None)
            return None
        return json.loads(raw)
    except Exception as e:  # noqa: BLE001
        logger.debug("cache get ব্যর্থ (%s): %s", key, e)
        return None


async def set_json(key: str, value: Any, ttl_seconds: int = 1800) -> None:
    """ক্যাশে রাখে। ব্যর্থ হলে চুপচাপ ছেড়ে দেয় — অ্যাপ থামবে না।"""
    try:
        raw = json.dumps(value, ensure_ascii=False, default=str)

        r = await _client()
        if r:
            await r.setex(key, ttl_seconds, raw)
            return

        _mem[key] = (time.time() + ttl_seconds, raw)

        # মেমরি বাড়তে না দেওয়া
        if len(_mem) > 500:
            now = time.time()
            for k in [k for k, (exp, _) in _mem.items() if exp < now]:
                _mem.pop(k, None)
    except Exception as e:  # noqa: BLE001
        logger.debug("cache set ব্যর্থ (%s): %s", key, e)


async def delete(key: str) -> None:
    try:
        r = await _client()
        if r:
            await r.delete(key)
        else:
            _mem.pop(key, None)
    except Exception:  # noqa: BLE001
        pass


# ══════════════════════════════════════════════════════════
# ২. রেট লিমিটের গোনা
# ══════════════════════════════════════════════════════════
async def incr_with_expiry(key: str, window_seconds: int) -> int:
    """key-এর মান ১ বাড়িয়ে নতুন মান ফেরত দেয়। প্রথমবার হলে TTL বসায়।
    ব্যর্থ হলে 0 — কলার তখন ইন-মেমরি হিসাবে ফিরে যাবে।"""
    try:
        r = await _client()
        if r:
            count = await r.incr(key)
            if count == 1:
                await r.expire(key, window_seconds)
            return int(count)

        now = time.time()
        expires_at, count = _mem_counters.get(key, (0.0, 0))
        if now > expires_at:
            _mem_counters[key] = (now + window_seconds, 1)
            return 1
        _mem_counters[key] = (expires_at, count + 1)
        return count + 1
    except Exception as e:  # noqa: BLE001
        logger.debug("cache incr ব্যর্থ (%s): %s", key, e)
        return 0


async def ttl_of(key: str) -> int:
    """আর কত সেকেন্ড পরে মেয়াদ শেষ। জানা না গেলে 60।"""
    try:
        r = await _client()
        if r:
            t = await r.ttl(key)
            return int(t) if t and t > 0 else 60

        expires_at, _ = _mem_counters.get(key, (0.0, 0))
        left = int(expires_at - time.time())
        return left if left > 0 else 60
    except Exception:  # noqa: BLE001
        return 60


# ══════════════════════════════════════════════════════════
# ৩. জব সার্চের জন্য ক্যাশ কি
# ══════════════════════════════════════════════════════════
def job_cache_key(
    keywords: list[str] | None,
    districts: list[str] | None,
    include_gov: bool,
    only_gov: bool,
) -> str:
    """একই সার্চ = একই কি। কি-ওয়ার্ডের ক্রম আলাদা হলেও যেন একই হয়,
    তাই সাজিয়ে নেওয়া হয়।"""
    parts = {
        "kw": sorted(k.lower().strip() for k in (keywords or []) if k),
        "dist": sorted(d.lower().strip() for d in (districts or []) if d),
        "gov": include_gov,
        "only_gov": only_gov,
    }
    blob = json.dumps(parts, sort_keys=True, ensure_ascii=False)
    return "jobs:" + hashlib.md5(blob.encode()).hexdigest()[:16]