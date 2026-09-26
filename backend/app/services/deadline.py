"""
ডেডলাইন নরমালাইজেশন।

প্রতিটা সোর্স আলাদা ফরম্যাটে ডেডলাইন দেয়:
  teletalk  → date অবজেক্ট
  rss       → date অবজেক্ট বা None
  bdjobs    → স্ট্রিং ("Oct 20, 2026" / "20-10-2026" / "Apply Soon")
  ভবিষ্যৎ   → যা খুশি

এই ফাইল সবগুলোকে এক জায়গায় এনে একটাই `date` বানায়, আর কত দিন বাকি
সেটা হিসাব করে। নতুন সোর্স যোগ করলে শুধু raw মান পাঠিয়ে দিলেই হবে।
"""

from __future__ import annotations

import re
from datetime import date, datetime

# ══════════════════════════════════════════════════════════
# বাংলা সংখ্যা ও মাস
# ══════════════════════════════════════════════════════════
_BN_DIGITS = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")

_BN_MONTHS: dict[str, int] = {
    "জানুয়ারি": 1, "জানুয়ারী": 1,
    "ফেব্রুয়ারি": 2, "ফেব্রুয়ারী": 2,
    "মার্চ": 3,
    "এপ্রিল": 4,
    "মে": 5,
    "জুন": 6,
    "জুলাই": 7,
    "আগস্ট": 8, "অগাস্ট": 8,
    "সেপ্টেম্বর": 9,
    "অক্টোবর": 10,
    "নভেম্বর": 11,
    "ডিসেম্বর": 12,
}

# datetime.strptime-এ যে ফরম্যাটগুলো চেষ্টা করা হবে, ক্রম অনুযায়ী
_FORMATS = (
    "%Y-%m-%d",
    "%d-%m-%Y",
    "%d/%m/%Y",
    "%Y/%m/%d",
    "%b %d, %Y",      # Oct 20, 2026
    "%B %d, %Y",      # October 20, 2026
    "%d %b %Y",       # 20 Oct 2026
    "%d %B %Y",       # 20 October 2026
    "%d.%m.%Y",
)

# এই শব্দগুলো থাকলে বুঝব আসল তারিখ নেই
_NO_DATE_WORDS = (
    "apply soon", "recent", "চলমান", "ongoing", "asap", "urgent",
    "n/a", "na", "-", "tba", "until filled",
)


# ══════════════════════════════════════════════════════════
# ১. যেকোনো কিছু → date
# ══════════════════════════════════════════════════════════
def to_date(value) -> date | None:
    """date, datetime, বা যেকোনো ফরম্যাটের স্ট্রিং থেকে date বের করে।
    বুঝতে না পারলে None — ভুয়া তারিখ কখনো বানায় না।"""
    if value is None:
        return None

    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None

    text = value.translate(_BN_DIGITS).strip()
    if not text or text.lower() in _NO_DATE_WORDS:
        return None

    # ISO ("2026-10-20T00:00:00Z")
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass

    # বাংলা মাসের নাম ("১৫ অক্টোবর ২০২৬")
    for bn_month, num in _BN_MONTHS.items():
        if bn_month in text:
            m = re.search(r"(\d{1,2})\D{0,12}" + bn_month + r"\D{0,12}(\d{4})", text)
            if m:
                try:
                    return date(int(m.group(2)), num, int(m.group(1)))
                except ValueError:
                    pass

    # প্রচলিত ফরম্যাটগুলো
    for fmt in _FORMATS:
        for candidate in (text, text[:11], text[:10]):
            try:
                return datetime.strptime(candidate.strip(), fmt).date()
            except ValueError:
                continue

    # শেষ চেষ্টা: টেক্সটের ভেতর লুকানো তারিখ
    m = re.search(r"(\d{1,2})[-/.](\d{1,2})[-/.](\d{4})", text)
    if m:
        try:
            return date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
        except ValueError:
            pass

    return None


# ══════════════════════════════════════════════════════════
# ২. কত দিন বাকি
# ══════════════════════════════════════════════════════════
def days_until(deadline: date | None, today: date | None = None) -> int | None:
    """আজ থেকে কত দিন বাকি। ০ মানে আজই শেষ দিন, ঋণাত্মক মানে পার হয়ে গেছে।"""
    if deadline is None:
        return None
    return (deadline - (today or date.today())).days


# ══════════════════════════════════════════════════════════
# ৩. জরুরিত্বের স্তর — UI-তে রঙ ঠিক করার জন্য
# ══════════════════════════════════════════════════════════
EXPIRED = "expired"    # পার হয়ে গেছে
CRITICAL = "critical"  # ০-২ দিন
URGENT = "urgent"      # ৩-৭ দিন
SOON = "soon"          # ৮-১৫ দিন
NORMAL = "normal"      # ১৫+ দিন
UNKNOWN = "unknown"    # তারিখ জানা নেই

URGENCY_LABELS: dict[str, str] = {
    EXPIRED: "মেয়াদ শেষ",
    CRITICAL: "আজই শেষ",
    URGENT: "শেষ হচ্ছে",
    SOON: "সময় আছে",
    NORMAL: "চলমান",
    UNKNOWN: "তারিখ অজানা",
}


def urgency_of(days: int | None) -> str:
    if days is None:
        return UNKNOWN
    if days < 0:
        return EXPIRED
    if days <= 2:
        return CRITICAL
    if days <= 7:
        return URGENT
    if days <= 15:
        return SOON
    return NORMAL


def deadline_text(days: int | None) -> str:
    """কার্ডে দেখানোর জন্য বাংলা লেখা।"""
    if days is None:
        return "শেষ তারিখ উল্লেখ নেই"
    if days < 0:
        return f"{abs(days)} দিন আগে শেষ হয়েছে"
    if days == 0:
        return "আজই শেষ দিন"
    if days == 1:
        return "আগামীকাল শেষ"
    return f"{days} দিন বাকি"


# ══════════════════════════════════════════════════════════
# ৪. JobItem-এ বসিয়ে দেওয়া
# ══════════════════════════════════════════════════════════
def apply_deadline(job, raw_deadline) -> None:
    """একটা JobItem-এ deadline, days_left ও urgency বসায় (in place)।
    job_fetcher থেকে প্রতিটা সোর্সের raw মান পাঠিয়ে ডাকা হবে।"""
    d = to_date(raw_deadline)
    left = days_until(d)

    job.deadline = d
    job.days_left = left
    job.urgency = urgency_of(left)