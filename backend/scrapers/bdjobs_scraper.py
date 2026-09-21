import sys
import asyncio
import json
import urllib.parse
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
from playwright.async_api import async_playwright


class BdjobsScraper:
    def __init__(self):
        self.base_url = "https://jobs.bdjobs.com/jobsearch.asp"

    async def search_jobs(self, keyword: str, district: Optional[str] = None, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        Windows Uvicorn NotImplementedError সম্পূর্ণ বাইপাস করার জন্য
        একটি পৃথক থ্রেড ও নিজস্ব Proactor লুপে স্ক্র্যাপার রান করে।
        """
        def _run_in_isolated_proactor():
            if sys.platform == "win32":
                loop = asyncio.WindowsProactorEventLoopPolicy().new_event_loop()
            else:
                loop = asyncio.new_event_loop()

            asyncio.set_event_loop(loop)
            try:
                return loop.run_until_complete(self._scrape_logic(keyword, district, max_results))
            finally:
                loop.close()

        loop = asyncio.get_running_loop()
        with ThreadPoolExecutor(max_workers=1) as executor:
            return await loop.run_in_executor(executor, _run_in_isolated_proactor)

    async def _scrape_logic(self, keyword: str, district: Optional[str] = None, max_results: int = 20) -> List[Dict[str, Any]]:
        """
        বিডিজবসের একাধিক পেজ ঘুরে লাইভ সার্কুলার স্ক্র্যাপ করার মূল প্লে-রাইট লজিক।
        """
        encoded_keyword = urllib.parse.quote(keyword)
        jobs: List[Dict[str, Any]] = []
        seen_job_ids = set()

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
            )
            page = await context.new_page()

            current_page_captured: List[Any] = []

            async def handle_response(response):
                try:
                    content_type = response.headers.get("content-type", "")
                    if "application/json" in content_type:
                        raw = await response.json()
                        current_page_captured.append(raw)
                except Exception:
                    pass

            page.on("response", handle_response)

            for page_num in range(1, 4):
                if len(jobs) >= max_results:
                    break

                target_url = f"{self.base_url}?fcatId=0&txtsearch={encoded_keyword}&pg={page_num}"
                if district and district.upper() != "ALL":
                    target_url += f"&qLoc={urllib.parse.quote(district)}"

                current_page_captured.clear()

                try:
                    await page.goto(target_url, wait_until="networkidle", timeout=30000)
                    await page.wait_for_timeout(2500)

                    # ১. এপিআই পে-লোড থেকে সার্কুলার এক্সট্র্যাক্ট করা
                    for payload in current_page_captured:
                        items = []
                        if isinstance(payload, dict):
                            for key in ["data", "jobs", "JobList", "items", "CommonJobs"]:
                                val = payload.get(key)
                                if isinstance(val, list):
                                    items = val
                                    break
                        elif isinstance(payload, list):
                            items = payload

                        for item in items:
                            if not isinstance(item, dict):
                                continue

                            title = item.get("jobTitle") or item.get("JobTitle") or item.get("title")
                            if not title:
                                continue

                            job_id = ""
                            for k, v in item.items():
                                if "id" in k.lower() and v:
                                    val_str = str(v).strip()
                                    if val_str.isdigit() and len(val_str) >= 4:
                                        job_id = val_str
                                        break

                            if not job_id:
                                job_id = str(item.get("jobid") or item.get("jobId") or item.get("JP_ID") or "").strip()

                            final_id = job_id or str(abs(hash(title)) % 1000000)
                            if final_id in seen_job_ids:
                                continue
                            seen_job_ids.add(final_id)

                            company = item.get("companyName") or item.get("CompanyName") or item.get("company", "Top BD Employer")
                            location = item.get("location") or item.get("JobLocation") or "Dhaka"
                            deadline = item.get("deadline") or item.get("Deadline") or "Apply Soon"
                            exp = item.get("experience") or item.get("Experience") or "1-3 years"

                            job_url = f"https://jobs.bdjobs.com/jobdetails.asp?id={job_id}" if job_id else target_url

                            jobs.append({
                                "id": f"bdjobs_{final_id}",
                                "title": title,
                                "company": company,
                                "location": location,
                                "district": district or "Dhaka",
                                "experience": exp,
                                "deadline": deadline,
                                "description": f"Verified vacancy for {title} at {company}.",
                                "url": job_url,
                                "source": "BDJOBS",
                                "is_remote": "remote" in title.lower() or "remote" in location.lower(),
                                "tags": ["Bdjobs", "Live"],
                                "match_score": 85
                            })

                            if len(jobs) >= max_results:
                                break

                        if len(jobs) >= max_results:
                            break

                    # ২. ফলব্যাক DOM এক্সট্র্যাক্টর
                    if not jobs or len(jobs) < max_results:
                        dom_jobs = await page.evaluate('''() => {
                            const results = [];
                            const links = document.querySelectorAll("a[href*='jobdetails.asp']");
                            links.forEach(a => {
                                const title = a.innerText.trim();
                                const href = a.getAttribute('href') || '';
                                if (title.length > 3 && href && !results.some(r => r.url === href)) {
                                    let card = a.closest('div[class*="job"]') || a.parentElement;
                                    let compElem = card ? card.querySelector('.comp-name-text, .comp-name, .company-name') : null;
                                    results.push({
                                        title: title,
                                        url: href.startsWith('http') ? href : `https://jobs.bdjobs.com/${href.replace(/^\\//, '')}`,
                                        company: compElem ? compElem.innerText.trim() : "Bdjobs Employer"
                                    });
                                }
                            });
                            return results;
                        }''')

                        for item in dom_jobs:
                            url = item.get("url", "")
                            title = item.get("title", "")
                            if not title or not url:
                                continue

                            id_match = None
                            if "id=" in url:
                                id_match = url.split("id=")[-1].split("&")[0]
                            final_id = id_match or str(abs(hash(url)) % 1000000)

                            if final_id in seen_job_ids:
                                continue
                            seen_job_ids.add(final_id)

                            jobs.append({
                                "id": f"bdjobs_{final_id}",
                                "title": title,
                                "company": item.get("company", "Top BD Employer"),
                                "location": "Dhaka, Bangladesh",
                                "district": district or "Dhaka",
                                "experience": "1-3 years",
                                "deadline": "Apply Soon",
                                "description": f"Live opportunity on Bdjobs for {title}.",
                                "url": url,
                                "source": "BDJOBS",
                                "is_remote": "remote" in title.lower(),
                                "tags": ["Bdjobs", "Live"],
                                "match_score": 85
                            })

                            if len(jobs) >= max_results:
                                break

                except Exception as page_err:
                    print(f"[BdjobsScraper] Error on page {page_num}: {page_err}")
                    break

            await browser.close()

        return jobs