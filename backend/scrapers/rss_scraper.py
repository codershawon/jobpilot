"""
RSS অ্যাডাপ্টার — একটা ক্লাস, অনেকগুলো সোর্স।

বাংলাদেশের বেশিরভাগ job circular সাইট WordPress-এ চলে, তাই সবার
/feed/ আছে। HTML স্ক্র্যাপিংয়ের চেয়ে RSS অনেক ভালো:
  - সাইট রিডিজাইন করলেও ভাঙে না (কোনো CSS selector নেই)
  - ভদ্র — RSS প্রকাশই করা হয় পড়ার জন্য
  - parsing কোড ১০ লাইন

নতুন সোর্স যোগ করা = FEEDS তালিকায় এক লাইন।
"""

from __future__ import annotations

import asyncio
import hashlib
import re
from datetime import date, datetime
from typing import Any

import feedparser
import httpx

HEADERS = {"User-Agent": "JobPilotBot/1.0 (+https://jobpilot.example/bot)"}

# ── নতুন সোর্স এখানে যোগ করো ──
FEEDS: list[dict[str, str]] = [
    # content সবচেয়ে সমৃদ্ধ — ৩,৬০০ অক্ষর
    {"id": "chakrirkhobor", "url": "https://chakrirkhobor.net/feed/", "category": "govt"},
    # বাংলা ডেডলাইন টেক্সট আছে
    {"id": "ejobscircular", "url": "https://ejobscircular.com/feed/", "category": "govt"},
    # শুধু টাইটেল+লিংক, আবিষ্কারের জন্য
    {"id": "bdgovtjob",     "url": "https://bdgovtjob.net/feed/",     "category": "govt"},
    # আন্তর্জাতিক রিমোট
    {"id": "weworkremotely",
     "url": "https://weworkremotely.com/categories/remote-programming-jobs.rss",
     "category": "remote"},
]

_BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
_BN_MONTHS = {
    "জানুয়ারি": 1, "ফেব্রুয়ারি": 2, "মার্চ": 3, "এপ্রিল": 4,
    "মে": 5, "জুন": 6, "জুলাই": 7, "আগস্ট": 8,
    "সেপ্টেম্বর": 9, "অক্টোবর": 10, "নভেম্বর": 11, "ডিসেম্বর": 12,
}

# "আবেদনের শেষ তারিখ: ১৫ অক্টোবর ২০২৬" ধরনের প্যাটার্ন
_DEADLINE_HINTS = (
    "শেষ তারিখ", "আবেদনের শেষ", "সময়সীমা",
    "deadline", "last date", "application deadline",
)


def _strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def _extract_deadline(text: str) -> date | None:
    """বর্ণনার ভিতর থেকে আবেদনের শেষ তারিখ খুঁজে বের করে।"""
    if not text:
        return None
    normalized = text.translate(_BN_DIGITS)
    lower = normalized.lower()

    for hint in _DEADLINE_HINTS:
        idx = lower.find(hint.lower())
        if idx == -1:
            continue
        window = normalized[idx: idx + 120]

        # বাংলা মাসের নাম সহ
        for bn_month, num in _BN_MONTHS.items():
            if bn_month in window:
                m = re.search(r"(\d{1,2})\D{0,12}" + bn_month + r"\D{0,12}(\d{4})", window)
                if m:
                    try:
                        return date(int(m.group(2)), num, int(m.group(1)))
                    except ValueError:
                        pass

        # সংখ্যায় লেখা: 15-10-2026 / 15/10/2026
        m = re.search(r"(\d{1,2})[-/](\d{1,2})[-/](\d{4})", window)
        if m:
            try:
                return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            except ValueError:
                pass
    return None


def _guess_company(title: str) -> str:
    """
    'Bangladesh Bank Job Circular 2026' → 'Bangladesh Bank'
    'বাংলাদেশ ব্যাংক নিয়োগ বিজ্ঞপ্তি ২০২৬' → 'বাংলাদেশ ব্যাংক'
    """
    cleaned = re.sub(
        r"\b(job|jobs)?\s*(circular|vacancy|recruitment|notice)\b.*$",
        "", title, flags=re.IGNORECASE,
    )
    cleaned = re.split(r"নিয়োগ|বিজ্ঞপ্তি|সার্কুলার", cleaned)[0]
    cleaned = re.sub(r"[-–|]\s*$", "", cleaned).strip(" -–|")
    return cleaned if 2 < len(cleaned) < 90 else ""


def _to_date(struct_time) -> date | None:
    if not struct_time:
        return None
    try:
        return datetime(*struct_time[:6]).date()
    except Exception:  # noqa: BLE001
        return None


class RSSSource:
    """একটা RSS ফিড।"""

    def __init__(self, feed: dict[str, str]):
        self.id = feed["id"]
        self.url = feed["url"]
        self.category = feed["category"]

    async def fetch(self) -> list[dict[str, Any]]:
        try:
            async with httpx.AsyncClient(
                headers=HEADERS, timeout=25.0, follow_redirects=True
            ) as client:
                res = await client.get(self.url)
            if res.status_code != 200:
                print(f"[{self.id}] HTTP {res.status_code}")
                return []
        except Exception as e:  # noqa: BLE001
            print(f"[{self.id}] {type(e).__name__}: {str(e)[:90]}")
            return []

        parsed = feedparser.parse(res.text)
        if parsed.bozo and not parsed.entries:
            print(f"[{self.id}] ফিড পার্স করা গেল না")
            return []

        jobs: list[dict[str, Any]] = []
        for entry in parsed.entries:
            job = self._normalize(entry)
            if job:
                jobs.append(job)

        print(f"[{self.id}] {len(jobs)} এন্ট্রি")
        return jobs

    def _normalize(self, entry: Any) -> dict[str, Any] | None:
        link = (entry.get("link") or "").strip()
        title = (entry.get("title") or "").strip()
        if not link or not title:
            return None

        # content থাকলে সেটাই ভালো — অনেক বেশি তথ্য
        body = ""
        if entry.get("content"):
            body = _strip_html(entry["content"][0].get("value", ""))
        if len(body) < 200:
            body = _strip_html(entry.get("summary") or entry.get("description") or "") or body

        return {
            "external_id": f"{self.id}_{hashlib.md5(link.encode()).hexdigest()[:12]}",
            "source_id": self.id,
            "title": title,
            "title_bn": title if re.search(r"[\u0980-\u09FF]", title) else None,
            "company": _guess_company(title),
            "url": link,
            "description": body[:1500],
            "deadline": _extract_deadline(f"{title} {body}"),
            "posted_at": _to_date(entry.get("published_parsed")),
            "category": self.category,
            "district": "Remote" if self.category == "remote" else "Bangladesh",
            "location": "Worldwide Remote" if self.category == "remote" else "বাংলাদেশ",
            "is_remote": self.category == "remote",
            "salary": None,
            "tags": [self.id, self.category],
            "raw": {"link": link, "title": title},
        }


def all_rss_sources() -> list[RSSSource]:
    return [RSSSource(f) for f in FEEDS]


# ── দ্রুত পরীক্ষা: python -m scrapers.rss_scraper ──
if __name__ == "__main__":
    async def _demo():
        sources = all_rss_sources()
        results = await asyncio.gather(
            *[s.fetch() for s in sources], return_exceptions=True
        )
        total = 0
        for src, res in zip(sources, results):
            if isinstance(res, Exception):
                print(f"❌ {src.id}: {res}")
                continue
            total += len(res)
            with_dl = sum(1 for j in res if j["deadline"])
            print(f"✅ {src.id:<22} {len(res):>3} এন্ট্রি, {with_dl} টায় ডেডলাইন")
            if res:
                print(f"   উদাহরণ: {res[0]['title'][:65]}")
        print(f"\nমোট: {total}")

    asyncio.run(_demo())