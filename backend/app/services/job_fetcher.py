import asyncio
import hashlib
import re
from scrapers.bdjobs_scraper import BdjobsScraper
from scrapers.govt_scraper import GovtJobScraper
from scrapers.teletalk_alljobs_scraper import TeletalkAllJobsScraper
from scrapers.rss_scraper import all_rss_sources
from scrapers.portal_links import PortalLinksSource
from app.services.classifier import classify_job
from app.core.cache import get_json, job_cache_key, set_json
from app.services.deadline import apply_deadline
from scrapers.extra_sources import (
    fetch_himalayas,
    fetch_reliefweb,
    fetch_weworkremotely,
)
from typing import List
from bs4 import BeautifulSoup
import httpx
from app.config import settings
from app.models import JobItem
bdjobs_engine = BdjobsScraper()
teletalk_engine = TeletalkAllJobsScraper()
portal_source = PortalLinksSource()

BD_DISTRICTS = [
    "Dhaka", "Chattogram", "Cumilla", "Sylhet", "Rajshahi", "Khulna",
    "Barishal", "Rangpur", "Mymensingh", "Gazipur", "Narayanganj",
    "Cox's Bazar", "Noakhali", "Feni", "Brahmanbaria", "Chandpur",
    "Bogura", "Jashore", "Kushtia", "Pabna", "Tangail", "Dinajpur"
]

def generate_id(source: str, url: str) -> str:
    return hashlib.md5(f"{source}:{url}".encode()).hexdigest()[:12]

# ১. লাইভ বিডিজবস ফেচার (সম্পূর্ণ প্রাইভেট এবং আসল BDJOBS হিসেবে থাকবে)
async def fetch_bdjobs_unlimited(keywords: List[str], target_district: str = "Dhaka") -> List[JobItem]:
    jobs: List[JobItem] = []
    kw = keywords[0] if keywords else "Software Engineer"
    
    try:
        raw_results = await bdjobs_engine.search_jobs(keyword=kw, district=target_district, max_results=20)
        for r in raw_results:
            job_district = r.get("district") or target_district or "Dhaka"
            is_rem = bool(r.get("is_remote", False))
            
            job = JobItem(
                id=generate_id("bdjobs", r["url"]),
                title=r.get("title", "Job Vacancy"),
                company=r.get("company", "Private Employer"),
                location=r.get("location", job_district),
                district=job_district,
                is_remote=is_rem,
                job_type="Remote" if is_rem else "Local",
                source="BDJOBS",                     
                url=r["url"],
                description=r.get("description", f"Verified opening for {r.get('title')} at {r.get('company')}."),
                salary=r.get("salary", "Negotiable"),
                tags=r.get("tags", ["Bdjobs", "Live"]), 
                posted_date=r.get("deadline", "Recent"),
                match_score=85,
                match_reason="Matched from BDJobs circular",
                cover_letter="",
                status="SAVED"
            )
            apply_deadline(job, r.get("deadline"))
            jobs.append(job)
    except Exception as e:
        print(f"[Bdjobs Fetch Notice]: {e}")
        
    return jobs

# ১.১ লাইভ সরকারি চাকরি ফেচার (bdgovtjob.net ইঞ্জিন)
async def fetch_govt_jobs_live(keywords=None, target_district="Dhaka"):
    """keywords উপেক্ষা করা হয় - সব আনা হয়, ফিল্টারিং পরে।"""
    # সরকারি সার্কুলার কি-ওয়ার্ডে বদলায় না — একবার এনে সবার জন্য
    gov_cached = await get_json("jobs:govt:all")
    if gov_cached:
        print(f"[CACHE HIT] govt — {len(gov_cached)} jobs")
        return [JobItem(**j) for j in gov_cached]

    tasks = [teletalk_engine.fetch()]
    tasks += [s.fetch() for s in all_rss_sources() if s.category in ("govt", "mixed")]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    jobs: List[JobItem] = []
    for res in results:
        if isinstance(res, Exception):
            print(f"[govt fetch] {res}")
            continue
        for r in res:
            deadline = r.get("deadline")
            job = JobItem(
                id=generate_id(r["source_id"], r.get("external_id") or r["url"]),
                title=r["title"],
                company=r.get("company") or "Government of Bangladesh",
                location=r.get("location", "Bangladesh"),
                district=r.get("district", "Bangladesh"),
                is_remote=False,
                job_type="Government",
                source="Govt",
                url=r["url"],
                description=r.get("description", ""),
                salary=r.get("salary") or "জাতীয় বেতন স্কেল",
                tags=r.get("tags", ["Govt"]),
                posted_date=r.get("published_date") or "সাম্প্রতিক",
                match_score=85,
                match_reason="Government recruitment circular",
                cover_letter="",
                status="SAVED",
            )
            apply_deadline(job, deadline)
            jobs.append(job)

    for j in jobs:
        classify_job(j)
    await set_json("jobs:govt:all", [j.model_dump() for j in jobs], ttl_seconds=1800)
    return jobs

# ২. LinkedIn Public Job Postings (No Limits)
async def fetch_linkedin_unlimited(keywords: List[str]) -> List[JobItem]:
    jobs: List[JobItem] = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
    }

    search_terms = keywords[:4] if keywords else ["React Developer", "Web Developer", "Frontend"]
    locations = ["Bangladesh", "Worldwide"]

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        for kw in search_terms:
            for loc in locations:
                url = f"https://www.linkedin.com/jobs-guest/jobs/api/seeMoreJobPostings/search?keywords={kw}&location={loc}&f_TPR=r2592000"
                try:
                    res = await client.get(url, headers=headers)
                    if res.status_code == 200:
                        soup = BeautifulSoup(res.text, "html.parser")
                        cards = soup.select("li, .base-card, .job-search-card")

                        for card in cards:
                            title_elem = card.select_one(".base-search-card__title, .job-search-card__title")
                            link_elem = card.select_one("a.base-card__full-link, a.job-search-card__url-link, a")
                            comp_elem = card.select_one(".base-search-card__subtitle, .job-search-card__company-name")
                            loc_elem = card.select_one(".job-search-card__location")

                            if not title_elem or not link_elem:
                                continue

                            title = title_elem.get_text(strip=True)
                            apply_url = link_elem.get("href", "").split("?")[0]
                            company = comp_elem.get_text(strip=True) if comp_elem else "LinkedIn Verified Employer"
                            exact_loc = loc_elem.get_text(strip=True) if loc_elem else loc

                            is_remote = "remote" in exact_loc.lower() or "worldwide" in loc.lower() or "remote" in title.lower()

                            li_job = JobItem(
                                id=generate_id("linkedin", apply_url or title),
                                title=title,
                                company=company,
                                location=exact_loc,
                                district="Remote" if is_remote else "Dhaka",
                                is_remote=is_remote,
                                job_type="Worldwide" if is_remote else "Local",
                                source="LinkedIn",
                                url=apply_url or "https://www.linkedin.com/jobs",
                                description=f"LinkedIn Opening: {title} at {company}. Direct apply available.",
                                tags=[kw, "LinkedIn"]
                            )
                            apply_deadline(li_job, None)
                            jobs.append(li_job)
                except Exception as e:
                    print(f"[LinkedIn Notice for {kw}]: {e}")
                    continue

    return jobs

# ৩. Remotive Global Software Devs (All Available Jobs)
async def fetch_remotive_unlimited(keywords: List[str]) -> List[JobItem]:
    jobs: List[JobItem] = []
    url = "https://remotive.com/api/remote-jobs?category=software-dev"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json().get("jobs", [])
                kw_set = [k.lower() for k in keywords if k]

                for item in data:
                    title = item.get("title", "")
                    tags = item.get("tags", [])
                    desc = item.get("description", "")
                    full_txt = f"{title} {' '.join(tags)} {desc}".lower()

                    if not kw_set or any(k in full_txt for k in kw_set) or "react" in full_txt or "javascript" in full_txt or "frontend" in full_txt or "web" in full_txt:
                        clean_desc = re.sub(r"<[^>]+>", " ", desc)[:500].strip()
                        jobs.append(JobItem(
                            id=generate_id("remotive", item.get("url", title)),
                            title=title,
                            company=item.get("company_name", "Global Remote Tech"),
                            location="Worldwide Remote",
                            district="Remote",
                            is_remote=True,
                            job_type="Worldwide",
                            source="Remotive",
                            url=item.get("url", "https://remotive.com"),
                            description=clean_desc,
                            salary=item.get("salary") or "Competitive / USD",
                            tags=tags[:5]
                        ))
    except Exception as e:
        print(f"[Remotive Notice]: {e}")
    return jobs

# ৪. Arbeitnow API (All Available Tech Jobs)
async def fetch_arbeitnow_unlimited(keywords: List[str]) -> List[JobItem]:
    jobs: List[JobItem] = []
    url = "https://www.arbeitnow.com/api/job-board-api"
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            res = await client.get(url)
            if res.status_code == 200:
                data = res.json().get("data", [])
                kw_set = [k.lower() for k in keywords if k]

                for item in data:
                    title = item.get("title", "")
                    tags = item.get("tags", [])
                    desc = item.get("description", "")
                    full_txt = f"{title} {' '.join(tags)} {desc}".lower()

                    if not kw_set or any(k in full_txt for k in kw_set) or "developer" in full_txt or "engineer" in full_txt:
                        clean_desc = re.sub(r"<[^>]+>", " ", desc)[:500].strip()
                        jobs.append(JobItem(
                            id=generate_id("arbeitnow", item.get("url", title)),
                            title=title,
                            company=item.get("company_name", "Global Employer"),
                            location=item.get("location", "Remote"),
                            district="Remote" if item.get("remote") else "International",
                            is_remote=item.get("remote", True),
                            job_type="Worldwide",
                            source="Arbeitnow",
                            url=item.get("url", "https://arbeitnow.com"),
                            description=clean_desc,
                            tags=tags[:5]
                        ))
    except Exception as e:
        print(f"[Arbeitnow Notice]: {e}")
    return jobs

# ৫. RemoteOK API (All Available Jobs)
async def fetch_remoteok_unlimited(keywords: List[str]) -> List[JobItem]:
    jobs: List[JobItem] = []
    url = "https://remoteok.com/api"
    headers = {"User-Agent": "Mozilla/5.0"}
    try:
        async with httpx.AsyncClient(timeout=15.0, headers=headers) as client:
            res = await client.get(url)
            if res.status_code == 200:
                raw_data = res.json()
                clean_data = [item for item in raw_data if isinstance(item, dict) and "position" in item]
                kw_set = [k.lower() for k in keywords if k]

                for item in clean_data:
                    title = item.get("position", "")
                    tags = item.get("tags", [])
                    desc = item.get("description", "")
                    full_txt = f"{title} {' '.join(tags)} {desc}".lower()

                    if not kw_set or any(k in full_txt for k in kw_set) or "dev" in full_txt or "software" in full_txt:
                        clean_desc = re.sub(r"<[^>]+>", " ", desc)[:500].strip()
                        jobs.append(JobItem(
                            id=generate_id("remoteok", item.get("url", title)),
                            title=title,
                            company=item.get("company", "Remote Tech"),
                            location="Worldwide Remote",
                            district="Remote",
                            is_remote=True,
                            job_type="Worldwide",
                            source="RemoteOK",
                            url=item.get("url", "https://remoteok.com"),
                            description=clean_desc,
                            tags=tags[:5]
                        ))
    except Exception as e:
        print(f"[RemoteOK Notice]: {e}")
    return jobs

# মাস্টার আনলিমিটেড ফেচার (সব প্ল্যাটফর্মের সব রেজাল্ট একত্রিত করে)
async def aggregate_all_jobs(
    keywords: List[str] = None,
    districts: List[str] = None,
    include_remote: bool = True,
    include_gov: bool = True,
    only_gov: bool = False, 
    limit_per_source: int = None
) -> List[JobItem]:
    dist = districts[0] if districts and len(districts) > 0 and districts[0] != "All" else "Cumilla"
    # ── ক্যাশ চেক ──
    ckey = job_cache_key(keywords, districts, include_gov, only_gov)
    cached = await get_json(ckey)
    if cached:
        print(f"[CACHE HIT] {ckey} — {len(cached)} jobs")
        return [JobItem(**j) for j in cached]

    # ১. ইউজার যদি শুধু Govt Circulars দেখতে চায়:
    if only_gov:
        gov_only = await fetch_govt_jobs_live(keywords=keywords, target_district=dist)
        await set_json(ckey, [j.model_dump() for j in gov_only], ttl_seconds=1800)
        return gov_only

    # ২. সাধারণ সার্চ হলে সবগুলো প্লাটফর্ম থেকে:
    search_keywords = keywords or ["React", "Next.js", "Frontend Developer", "Web Developer", "Node.js", "JavaScript"]

        # নাম ও টাস্ক একসাথে — কখনো আলাদা হতে পারবে না
    jobs_by_source: list[tuple[str, object]] = [
        ("bdjobs", fetch_bdjobs_unlimited(search_keywords, target_district=dist)),
        ("bdjobs_ngo", fetch_bdjobs_unlimited(["NGO", "Project Officer"], target_district=dist)),
        ("remotive", fetch_remotive_unlimited(search_keywords)),
        ("arbeitnow", fetch_arbeitnow_unlimited(search_keywords)),
        ("remoteok", fetch_remoteok_unlimited(search_keywords)),
        ("linkedin", fetch_linkedin_unlimited(search_keywords)),
        ("weworkremotely", fetch_weworkremotely(search_keywords)),
        ("himalayas", fetch_himalayas(search_keywords)),
        # ReliefWeb: অনুমোদিত appname দরকার — https://apidoc.reliefweb.int/
        # ("reliefweb", fetch_reliefweb(search_keywords)),
    ]

    if include_gov:
        jobs_by_source.append(
            ("govt", fetch_govt_jobs_live(search_keywords, target_district=dist))
        )

    source_names = [name for name, _ in jobs_by_source]
    results = await asyncio.gather(*(task for _, task in jobs_by_source), return_exceptions=True)

    all_jobs: List[JobItem] = []
    for name, res in zip(source_names, results):
        if isinstance(res, Exception):
            print(f"[FETCH FAIL] {name}: {type(res).__name__} — {res}")
            continue
        if isinstance(res, list):
            print(f"[FETCH OK]   {name}: {len(res)} jobs")
            all_jobs.extend(res)

    print(f"[FETCH TOTAL] {len(all_jobs)} jobs before dedup")

    # ডুপ্লিকেট রিমুভ (ইউনিক আইডি দিয়ে)
    unique_jobs = {}
    for j in all_jobs:
        if j.id not in unique_jobs and len(j.title.strip()) > 2:
            unique_jobs[j.id] = j

    final = list(unique_jobs.values())
    for job in final:
        classify_job(job)

    print(f"[FETCH FINAL] {len(final)} unique jobs")

    # ৩০ মিনিট ধরে রাখা — সার্কুলার এত দ্রুত বদলায় না
    await set_json(ckey, [j.model_dump() for j in final], ttl_seconds=1800)

    return final

async def aggregate_jobs_by_profile(
    keywords: List[str],
    user_district: str = "Cumilla",
    limit_per_source: int = None
) -> List[JobItem]:
    return await aggregate_all_jobs(
        keywords=keywords,
        districts=[user_district],
        include_remote=True,
        include_gov=True
    )