"""Teletalk AllJobs - official government job JSON API.

Verified field names (from tools/inspect_teletalk.py):
    id, job_id, job_title, job_title_bn, application_site,
    vacancy, vacancy_not_specific, published_date,
    deadline_date, job_utilities_govtorganization
Top level: status, statusCode, message, count, govtJobs
API returns 20 items per page regardless of the limit param.
"""

from __future__ import annotations

import asyncio
import re
from datetime import date, datetime
from typing import Any

import httpx

HEADERS = {
    "User-Agent": "JobPilotBot/1.0 (+https://jobpilot.example/bot)",
    "Accept": "application/json",
    "Referer": "https://alljobs.teletalk.com.bd/",
}

BD_DISTRICTS = [
    "Bagerhat", "Bandarban", "Barguna", "Barishal", "Bhola", "Bogura",
    "Brahmanbaria", "Chandpur", "Chapainawabganj", "Chattogram", "Chuadanga",
    "Coxsbazar", "Cumilla", "Dhaka", "Dinajpur", "Faridpur", "Feni",
    "Gaibandha", "Gazipur", "Gopalganj", "Habiganj", "Jamalpur", "Jashore",
    "Jhalokathi", "Jhenaidah", "Joypurhat", "Khagrachhari", "Khulna",
    "Kishoreganj", "Kurigram", "Kushtia", "Lakshmipur", "Lalmonirhat",
    "Madaripur", "Magura", "Manikganj", "Meherpur", "Moulvibazar",
    "Munshiganj", "Mymensingh", "Naogaon", "Narail", "Narayanganj",
    "Narsingdi", "Natore", "Netrokona", "Nilphamari", "Noakhali", "Pabna",
    "Panchagarh", "Patuakhali", "Pirojpur", "Rajbari", "Rajshahi",
    "Rangamati", "Rangpur", "Satkhira", "Shariatpur", "Sherpur",
    "Sirajganj", "Sunamganj", "Sylhet", "Tangail", "Thakurgaon",
]

ALIASES = {
    "comilla": "Cumilla",
    "chittagong": "Chattogram",
    "barisal": "Barishal",
    "jessore": "Jashore",
    "bogra": "Bogura",
    "coxs bazar": "Coxsbazar",
    "chapai nawabganj": "Chapainawabganj",
    "nawabganj": "Chapainawabganj",
    "khagrachari": "Khagrachhari",
}

LOOKUP = {d.lower(): d for d in BD_DISTRICTS}
LOOKUP.update(ALIASES)

BN_DIGITS = str.maketrans("\u09e6\u09e7\u09e8\u09e9\u09ea\u09eb\u09ec\u09ed\u09ee\u09ef",
                          "0123456789")

GOVT_FALLBACK = "Government of Bangladesh"


def detect_district(*texts):
    blob = " ".join(t for t in texts if t).lower()
    if not blob:
        return None
    for key in sorted(LOOKUP, key=len, reverse=True):
        if re.search(r"(?<![a-z])" + re.escape(key) + r"(?![a-z])", blob):
            return LOOKUP[key]
    return None


def parse_date(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if not isinstance(value, str):
        return None
    text = value.translate(BN_DIGITS).strip()
    try:
        return datetime.fromisoformat(text.replace("Z", "+00:00")).date()
    except ValueError:
        pass
    for fmt in ("%Y-%m-%d", "%d-%m-%Y", "%d/%m/%Y"):
        try:
            return datetime.strptime(text[:10], fmt).date()
        except ValueError:
            continue
    return None


class TeletalkAllJobsScraper:
    id = "teletalk_alljobs"
    category = "govt"

    API = "https://alljobs.teletalk.com.bd/api/v1/govt-jobs/list"
    PER_PAGE = 20
    MAX_PAGES = 40
    PAGE_DELAY = 0.5

    async def fetch(self):
        jobs = []
        seen = set()
        total = None

        async with httpx.AsyncClient(headers=HEADERS, timeout=25.0) as client:
            for page in range(1, self.MAX_PAGES + 1):
                payload = await self._fetch_page(client, page)
                if payload is None:
                    break
                if total is None:
                    total = payload.get("count")

                batch = payload.get("govtJobs") or []
                if not batch:
                    break

                fresh = 0
                for raw in batch:
                    job = self._normalize(raw)
                    if job and job["external_id"] not in seen:
                        seen.add(job["external_id"])
                        jobs.append(job)
                        fresh += 1

                print("  page %d: got %d, new %d (total %d)"
                      % (page, len(batch), fresh, len(jobs)))

                if fresh == 0:
                    print("  -> same data repeated, stopping")
                    break
                if total and len(jobs) >= total:
                    break
                await asyncio.sleep(self.PAGE_DELAY)

        dl = sum(1 for j in jobs if j["deadline"])
        di = sum(1 for j in jobs if j["district"] != "Bangladesh")
        print("[%s] %d circulars (API count %s) | deadline %d | district %d"
              % (self.id, len(jobs), total, dl, di))
        return jobs

    async def _fetch_page(self, client, page):
        try:
            res = await client.get(self.API,
                                   params={"page": page, "limit": self.PER_PAGE})
            if res.status_code != 200:
                print("  page %d -> HTTP %d" % (page, res.status_code))
                return None
            data = res.json()
            return data if isinstance(data, dict) else None
        except Exception as e:
            print("  page %d -> %s: %s" % (page, type(e).__name__, str(e)[:90]))
            return None

    def _normalize(self, item):
        row_id = item.get("id")
        if not row_id:
            return None

        title_en = (item.get("job_title") or "").strip()
        title_bn = (item.get("job_title_bn") or "").strip()
        if not title_en and not title_bn:
            return None

        org = item.get("job_utilities_govtorganization") or {}
        name_en = (org.get("name") or "").strip()
        name_bn = (org.get("name_bn") or "").strip()
        company = name_en or name_bn or GOVT_FALLBACK

        site = (item.get("application_site") or "").strip()
        url = site if site.startswith("http") else (
            "https://alljobs.teletalk.com.bd/jobs/government/details/%s" % row_id)

        deadline = parse_date(item.get("deadline_date"))
        published = parse_date(item.get("published_date"))
        district = detect_district(name_en, org.get("short_name"), site)

        vacancy = None
        if not item.get("vacancy_not_specific"):
            vacancy = (item.get("vacancy") or "").strip() or None

        parts = ["Organization: %s" % company]
        if vacancy:
            parts.append("Vacancy: %s" % vacancy)
        if published:
            parts.append("Published: %s" % published.strftime("%d-%m-%Y"))
        if deadline:
            parts.append("Deadline: %s" % deadline.strftime("%d-%m-%Y"))

        tags = ["Teletalk", "Govt"]
        if org.get("short_name"):
            tags.append(org["short_name"])

        return {
            "external_id": "teletalk_%s" % (item.get("job_id") or row_id),
            "source_id": self.id,
            "title": title_en or title_bn,
            "title_bn": title_bn or None,
            "company": company,
            "company_bn": name_bn or None,
            "org_website": org.get("website") or None,
            "url": url,
            "description": " | ".join(parts),
            "deadline": deadline,
            "posted_at": published,
            "category": "govt",
            "district": district or "Bangladesh",
            "location": ("%s, Bangladesh" % district) if district else "Bangladesh (Govt)",
            "is_remote": False,
            "salary": None,
            "vacancy": vacancy,
            "tags": tags,
            "raw": item,
        }


if __name__ == "__main__":
    async def demo():
        jobs = await TeletalkAllJobsScraper().fetch()
        from collections import Counter

        dl = sum(1 for j in jobs if j["deadline"])
        di = sum(1 for j in jobs if j["district"] != "Bangladesh")
        print("\n" + "=" * 60)
        print("total     : %d" % len(jobs))
        print("deadline  : %d/%d" % (dl, len(jobs)))
        print("district  : %d/%d" % (di, len(jobs)))

        top = Counter(j["district"] for j in jobs
                      if j["district"] != "Bangladesh").most_common(10)
        if top:
            print("\nby district:")
            for d, n in top:
                print("  %-18s %d" % (d, n))

        print("\n" + "-" * 60)
        for j in jobs[:5]:
            print("\n  %s" % j["title"])
            print("  %s" % j["company"][:58])
            print("  district=%s  deadline=%s" % (j["district"], j["deadline"]))

    asyncio.run(demo())
