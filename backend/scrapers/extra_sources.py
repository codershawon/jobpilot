"""
অতিরিক্ত জব সোর্স — ReliefWeb (NGO), WeWorkRemotely ও Himalayas (রিমোট)।

প্রতিটা ফাংশন একই চুক্তি মানে:
  - সবসময় একটা list ফেরত দেয়, কখনো exception ছোড়ে না
  - raw deadline মান পাঠিয়ে apply_deadline() ডাকে
  - নেটওয়ার্ক ব্যর্থ হলে খালি list, অ্যাপ থামে না

নতুন সোর্স যোগ করতে চাইলে এই ফাইলে একটা ফাংশন লিখে
job_fetcher.py-র tasks লিস্টে যোগ করলেই হবে।
"""

from __future__ import annotations

import hashlib
import re
from typing import List

import httpx

from app.models import JobItem
from app.services.deadline import apply_deadline

UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0"


def _mk_id(source: str, url: str) -> str:
    return hashlib.md5(f"{source}:{url}".encode()).hexdigest()[:12]


def _clean(html: str, limit: int = 500) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html or "")).strip()[:limit]


def _matches(text: str, keywords: List[str]) -> bool:
    """কি-ওয়ার্ড না থাকলে সব পাস, থাকলে অন্তত একটা মিলতে হবে।"""
    if not keywords:
        return True
    low = text.lower()
    return any(k.lower() in low for k in keywords if k)


# ══════════════════════════════════════════════════════════
# ১. ReliefWeb — NGO / উন্নয়ন সেক্টর
#    UN OCHA-র অফিশিয়াল API। ডেডলাইন (date.closing) সহ আসে।
# ══════════════════════════════════════════════════════════
async def fetch_reliefweb(
    keywords: List[str] | None = None,
    bangladesh_only: bool = False,
    limit: int = 80,
) -> List[JobItem]:
    jobs: List[JobItem] = []
    url = "https://api.reliefweb.int/v2/jobs"

    payload: dict = {
        "limit": min(limit, 200),
        "profile": "full",
        "sort": ["date.created:desc"],
        "filter": {"field": "status", "value": "active"},
    }

    if bangladesh_only:
        payload["filter"] = {
            "operator": "AND",
            "conditions": [
                {"field": "status", "value": "active"},
                {"field": "country", "value": "Bangladesh"},
            ],
        }

    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            res = await client.post(
                url, json=payload, params={"appname": "jobpilot-bd"}
            )
            if res.status_code != 200:
                print(f"[ReliefWeb] HTTP {res.status_code} — {res.text[:200]}")
                return jobs

            for item in res.json().get("data", []):
                f = item.get("fields", {})
                title = f.get("title") or ""
                if not title:
                    continue

                body = _clean(f.get("body", ""))
                cats = [c.get("name", "") for c in (f.get("career_categories") or [])]
                if not _matches(f"{title} {body} {' '.join(cats)}", keywords or []):
                    continue

                sources = f.get("source") or []
                org = sources[0].get("name") if sources else "Humanitarian Organization"

                countries = [c.get("name", "") for c in (f.get("country") or [])]
                loc = countries[0] if countries else "Multiple Locations"
                is_bd = any("bangladesh" in c.lower() for c in countries)

                job_url = f.get("url") or f"https://reliefweb.int/node/{item.get('id')}"

                job = JobItem(
                    id=_mk_id("reliefweb", job_url),
                    title=title,
                    company=org,
                    location=loc,
                    district="Bangladesh" if is_bd else "International",
                    is_remote=False,
                    job_type="NGO",
                    source="ReliefWeb",
                    url=job_url,
                    description=body or f"{title} at {org}.",
                    salary="Organization scale",
                    tags=(cats[:3] or ["NGO"]) + ["ReliefWeb"],
                    posted_date=(f.get("date") or {}).get("created", "")[:10] or "সাম্প্রতিক",
                    match_score=70,
                    match_reason="Humanitarian sector vacancy",
                    cover_letter="",
                    status="SAVED",
                )
                apply_deadline(job, (f.get("date") or {}).get("closing"))
                jobs.append(job)

    except Exception as e:  # noqa: BLE001
        print(f"[ReliefWeb Notice]: {type(e).__name__} — {e}")

    return jobs


# ══════════════════════════════════════════════════════════
# ২. WeWorkRemotely — RSS ফিড, রিমোট টেক জব
# ══════════════════════════════════════════════════════════
_WWR_FEEDS = (
    "https://weworkremotely.com/categories/remote-programming-jobs.rss",
    "https://weworkremotely.com/categories/remote-design-jobs.rss",
    "https://weworkremotely.com/categories/remote-devops-sysadmin-jobs.rss",
)


async def fetch_weworkremotely(keywords: List[str] | None = None) -> List[JobItem]:
    jobs: List[JobItem] = []

    try:
        import feedparser
    except ImportError:
        print("[WWR] feedparser নেই")
        return jobs

    try:
        async with httpx.AsyncClient(
            timeout=20.0, headers={"User-Agent": UA}, follow_redirects=True
        ) as client:
            for feed_url in _WWR_FEEDS:
                try:
                    res = await client.get(feed_url)
                    if res.status_code != 200:
                        continue

                    parsed = feedparser.parse(res.text)
                    for entry in parsed.entries[:40]:
                        raw_title = entry.get("title", "")
                        link = entry.get("link", "")
                        if not raw_title or not link:
                            continue

                        # WWR ফরম্যাট: "CompanyName: Job Title"
                        if ":" in raw_title:
                            company, _, title = raw_title.partition(":")
                            company, title = company.strip(), title.strip()
                        else:
                            company, title = "Remote Company", raw_title.strip()

                        desc = _clean(entry.get("summary", ""))
                        if not _matches(f"{title} {desc}", keywords or []):
                            continue

                        job = JobItem(
                            id=_mk_id("wwr", link),
                            title=title,
                            company=company,
                            location="Worldwide Remote",
                            district="Remote",
                            is_remote=True,
                            job_type="Worldwide",
                            source="WeWorkRemotely",
                            url=link,
                            description=desc or f"{title} at {company}.",
                            salary="Competitive / USD",
                            tags=["Remote", "WWR"],
                            posted_date=entry.get("published", "")[:16] or "সাম্প্রতিক",
                            match_score=65,
                            match_reason="Remote opening",
                            cover_letter="",
                            status="SAVED",
                        )
                        apply_deadline(job, None)  # WWR ডেডলাইন দেয় না
                        jobs.append(job)
                except Exception as e:  # noqa: BLE001
                    print(f"[WWR feed notice]: {e}")
                    continue

    except Exception as e:  # noqa: BLE001
        print(f"[WWR Notice]: {type(e).__name__} — {e}")

    return jobs


# ══════════════════════════════════════════════════════════
# ৩. Himalayas — রিমোট জবের JSON API
# ══════════════════════════════════════════════════════════
async def fetch_himalayas(keywords: List[str] | None = None, limit: int = 50) -> List[JobItem]:
    jobs: List[JobItem] = []
    url = "https://himalayas.app/jobs/api"

    try:
        async with httpx.AsyncClient(timeout=20.0, headers={"User-Agent": UA}) as client:
            res = await client.get(url, params={"limit": min(limit, 100)})
            if res.status_code != 200:
                print(f"[Himalayas] HTTP {res.status_code}")
                return jobs

            data = res.json()
            items = data.get("jobs") if isinstance(data, dict) else data
            if not isinstance(items, list):
                return jobs

            for item in items:
                if not isinstance(item, dict):
                    continue

                title = item.get("title") or ""
                link = item.get("applicationLink") or item.get("url") or ""
                if not title or not link:
                    continue

                desc = _clean(item.get("description", ""))
                cats = item.get("categories") or []
                if not _matches(f"{title} {desc} {' '.join(map(str, cats))}", keywords or []):
                    continue

                job = JobItem(
                    id=_mk_id("himalayas", link),
                    title=title,
                    company=item.get("companyName") or "Remote Company",
                    location="Worldwide Remote",
                    district="Remote",
                    is_remote=True,
                    job_type="Worldwide",
                    source="Himalayas",
                    url=link,
                    description=desc or f"{title} — remote position.",
                    salary=item.get("salary") or "Competitive / USD",
                    tags=[str(c) for c in cats[:3]] + ["Himalayas"],
                    posted_date="সাম্প্রতিক",
                    match_score=65,
                    match_reason="Remote opening",
                    cover_letter="",
                    status="SAVED",
                )
                apply_deadline(job, item.get("expiryDate"))
                jobs.append(job)

    except Exception as e:  # noqa: BLE001
        print(f"[Himalayas Notice]: {type(e).__name__} — {e}")

    return jobs