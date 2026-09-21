"""
RSS ফিড খুঁজে বের করার ও পরীক্ষা করার টুল।

দুইটা কাজ করে:
  1. ডোমেইন দিলে সব সম্ভাব্য feed path চেষ্টা করে, কোনটা কাজ করে বলে
  2. ফিডের ভিতরে আসলে কী আছে দেখায় — বিশেষত ডেডলাইনের টেক্সট আছে কিনা

ব্যবহার:
    python tools/inspect_rss.py                        # ডিফল্ট তালিকা
    python tools/inspect_rss.py bdgovtjob.net          # একটা ডোমেইন
    python tools/inspect_rss.py site1.com site2.com    # একাধিক
    python tools/inspect_rss.py https://x.com/feed/    # সরাসরি ফিড URL
"""

from __future__ import annotations

import asyncio
import re
import sys

import feedparser
import httpx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                  "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "application/rss+xml, application/xml, text/xml, text/html;q=0.9",
}

# WordPress ও অন্যান্য CMS-এ সবচেয়ে প্রচলিত feed path
FEED_PATHS = [
    "/feed/",
    "/feed",
    "/rss",
    "/rss.xml",
    "/feed/rss2/",
    "/?feed=rss2",
    "/atom.xml",
    "/index.xml",
    "/blog/feed/",
    "/jobs/feed/",
]

# যাচাই করার ডিফল্ট তালিকা
DEFAULT_DOMAINS = [
    "bdgovtjob.net",
    "chakritahole.com",
    "bdjobstoday.com",
    "chakrirkhobor.net",
    "ejobscircular.com",
    "alljobsbd.com",
    "bdjobsresults.com",
    "jobscircular24.com",
]

DEADLINE_HINTS = (
    "শেষ তারিখ", "আবেদনের শেষ", "সময়সীমা", "আবেদনের সময়",
    "deadline", "last date", "application deadline", "apply before",
)

_BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")


def strip_html(text: str) -> str:
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", text or "")).strip()


def find_deadline_context(text: str) -> list[str]:
    """ডেডলাইনের ইঙ্গিত কোথায় আছে তা আশপাশের লেখাসহ দেখায়।"""
    hits = []
    normalized = (text or "").translate(_BN_DIGITS)
    lower = normalized.lower()
    for hint in DEADLINE_HINTS:
        idx = lower.find(hint.lower())
        if idx != -1:
            start = max(0, idx - 30)
            hits.append(normalized[start: idx + 90].strip())
    return hits


async def try_feed(client: httpx.AsyncClient, url: str) -> tuple[int, str] | None:
    """ফিড আনার চেষ্টা। (entry সংখ্যা, শিরোনাম) অথবা None।"""
    try:
        res = await client.get(url)
    except Exception:
        return None

    if res.status_code != 200:
        return None

    body = res.text.lstrip()
    if not body.startswith("<?xml") and "<rss" not in body[:600] and "<feed" not in body[:600]:
        return None

    parsed = feedparser.parse(res.text)
    if not parsed.entries:
        return None

    return len(parsed.entries), (parsed.feed.get("title") or "").strip()


async def discover(domain: str) -> str | None:
    """একটা ডোমেইনের কার্যকর feed URL খুঁজে বের করে।"""
    if domain.startswith("http"):
        candidates = [domain]
        label = domain
    else:
        domain = domain.rstrip("/")
        candidates = [
            f"https://{domain}{p}" for p in FEED_PATHS
        ] + [
            f"https://www.{domain}{p}" for p in FEED_PATHS[:3]
        ]
        label = domain

    print(f"\n{'═' * 66}\n🔎 {label}\n{'═' * 66}")

    async with httpx.AsyncClient(
        headers=HEADERS, timeout=12.0, follow_redirects=True
    ) as client:
        for url in candidates:
            result = await try_feed(client, url)
            if result:
                count, title = result
                print(f"  ✅ {url}")
                print(f"     {count} entries | {title[:55]}")
                return url

    print("  ❌ কোনো কার্যকর ফিড পাওয়া যায়নি")
    print("     → ডোমেইনটা ব্রাউজারে খুলে দেখো আদৌ আছে কিনা")
    return None


async def inspect(feed_url: str) -> None:
    """ফিডের ভিতরে আসলে কী আছে দেখায়।"""
    async with httpx.AsyncClient(
        headers=HEADERS, timeout=20.0, follow_redirects=True
    ) as client:
        res = await client.get(feed_url)

    parsed = feedparser.parse(res.text)
    if not parsed.entries:
        print("  ⚠️  কোনো entry নেই")
        return

    entry = parsed.entries[0]

    print(f"\n  ── entry-তে যে ফিল্ডগুলো আছে ──")
    print(f"  {', '.join(sorted(entry.keys()))}")

    summary = strip_html(entry.get("summary") or entry.get("description") or "")
    content = ""
    if entry.get("content"):
        content = strip_html(entry["content"][0].get("value", ""))

    print(f"\n  ── প্রথম entry ──")
    print(f"  title   : {entry.get('title', '')[:80]}")
    print(f"  link    : {entry.get('link', '')[:80]}")
    print(f"  published: {entry.get('published', '(নেই)')}")
    print(f"  summary  : {len(summary)} অক্ষর")
    print(f"  content  : {len(content)} অক্ষর")

    body = content or summary
    print(f"\n  ── বডির প্রথম ৪০০ অক্ষর ──")
    print(f"  {body[:400] or '(খালি)'}")

    # ── ডেডলাইন খুঁজে পাওয়া যায় কিনা ──
    print(f"\n  ── ডেডলাইন বিশ্লেষণ ──")
    found_any = 0
    for e in parsed.entries[:10]:
        text = strip_html(
            (e.get("content", [{}])[0].get("value", "") if e.get("content") else "")
            or e.get("summary", "")
        )
        full = f"{e.get('title', '')} {text}"
        hits = find_deadline_context(full)
        if hits:
            found_any += 1
            if found_any <= 2:
                print(f"  ✅ \"{hits[0][:110]}\"")

    total = min(len(parsed.entries), 10)
    print(f"  → {found_any}/{total} entry-তে ডেডলাইনের ইঙ্গিত আছে")

    if found_any == 0:
        print(
            "\n  💡 RSS-এ শুধু excerpt আছে, ডেডলাইন নেই।\n"
            "     সমাধান: RSS থেকে লিংক নিয়ে সেই পেজটা আলাদাভাবে fetch করতে হবে।\n"
            "     (দিন ৩-এ background worker-এ এটা করা যাবে)"
        )


async def main() -> None:
    targets = sys.argv[1:] or DEFAULT_DOMAINS

    working: list[str] = []
    for target in targets:
        feed_url = await discover(target)
        if feed_url:
            working.append(feed_url)
            await inspect(feed_url)
        await asyncio.sleep(0.4)

    print(f"\n\n{'═' * 66}\n✅ যেগুলো কাজ করে — rss_scraper.py-এর FEEDS-এ বসাও\n{'═' * 66}")
    if working:
        for url in working:
            slug = re.sub(r"^https?://(www\.)?", "", url).split(".")[0]
            print(f'    {{"id": "{slug}", "url": "{url}", "category": "govt"}},')
    else:
        print("    (কোনোটাই কাজ করেনি)")


if __name__ == "__main__":
    asyncio.run(main())