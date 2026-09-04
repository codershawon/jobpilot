import asyncio
import hashlib
import re
from typing import List
from bs4 import BeautifulSoup
import httpx
from app.config import settings
from app.models import JobItem

BD_DISTRICTS = [
    "Dhaka", "Chattogram", "Cumilla", "Sylhet", "Rajshahi", "Khulna",
    "Barishal", "Rangpur", "Mymensingh", "Gazipur", "Narayanganj",
    "Cox's Bazar", "Noakhali", "Feni", "Brahmanbaria", "Chandpur",
    "Bogura", "Jashore", "Kushtia", "Pabna", "Tangail", "Dinajpur"
]

def generate_id(source: str, url: str) -> str:
    return hashlib.md5(f"{source}:{url}".encode()).hexdigest()[:12]

# ১. Bdjobs IT & Multi-Keyword Deep Scraper (No Limits)
async def fetch_bdjobs_unlimited(keywords: List[str], target_district: str = "Cumilla") -> List[JobItem]:
    jobs: List[JobItem] = []
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8"
    }

    # সবকটি প্রাসঙ্গিক কি-ওয়ার্ড দিয়ে গভীর সার্চ
    search_terms = keywords if keywords else ["React", "Next.js", "Web Developer", "Frontend Developer", "Full Stack", "JavaScript", "Node.js"]

    async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
        for kw in search_terms[:6]:
            url = f"https://jobs.bdjobs.com/jobsearch.asp?fcatId=8&txtsearch={kw}"
            try:
                await asyncio.sleep(settings.JOB_FETCH_MIN_DELAY_SECONDS)
                res = await client.get(url, headers=headers)
                if res.status_code == 200:
                    soup = BeautifulSoup(res.text, "html.parser")
                    cards = soup.select(".norm-jobs-wrapper, .sout-jobs-wrapper, .job-title-text, .featured-jobs")

                    for card in cards:
                        title_elem = card.find("a")
                        if not title_elem:
                            continue

                        title = title_elem.get_text(strip=True)
                        rel_url = title_elem.get("href", "")
                        if not rel_url or "javascript" in rel_url.lower():
                            continue

                        full_url = f"https://jobs.bdjobs.com/{rel_url}" if not rel_url.startswith("http") else rel_url
                        card_text = card.get_text()

                        loc = f"{target_district}, Bangladesh"
                        for d in BD_DISTRICTS:
                            if d.lower() in card_text.lower():
                                loc = f"{d}, Bangladesh"
                                break

                        company_elem = card.find_next(class_=re.compile(r"comp-name|comp_name|company"))
                        company = company_elem.get_text(strip=True) if company_elem else "Verified Bdjobs Employer"

                        jobs.append(JobItem(
                            id=generate_id("bdjobs", full_url),
                            title=title,
                            company=company,
                            location=loc,
                            district=loc.split(",")[0],
                            is_remote=False,
                            job_type="Local",
                            source="Bdjobs",
                            url=full_url,
                            description=f"Bdjobs IT Opportunity: {title} at {company}. Location: {loc}. Visit original link to apply.",
                            tags=[kw, "Bdjobs", "Local IT"]
                        ))
            except Exception as e:
                print(f"[Bdjobs Fetch Notice for {kw}]: {e}")
                continue

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

                            jobs.append(JobItem(
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
                            ))
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
    limit_per_source: int = None
) -> List[JobItem]:
    search_keywords = keywords or ["React", "Next.js", "Frontend Developer", "Web Developer", "Node.js", "JavaScript"]
    dist = districts[0] if districts and len(districts) > 0 else "Cumilla"

    tasks = [
        fetch_bdjobs_unlimited(search_keywords, target_district=dist),
        fetch_linkedin_unlimited(search_keywords),
        fetch_remotive_unlimited(search_keywords),
        fetch_arbeitnow_unlimited(search_keywords),
        fetch_remoteok_unlimited(search_keywords)
    ]

    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_jobs: List[JobItem] = []
    for res in results:
        if isinstance(res, list):
            all_jobs.extend(res)

    # ডুপ্লিকেট রিমুভ (ইউনিক আইডি দিয়ে)
    unique_jobs = {}
    for j in all_jobs:
        if j.id not in unique_jobs and len(j.title.strip()) > 2:
            unique_jobs[j.id] = j

    return list(unique_jobs.values())

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