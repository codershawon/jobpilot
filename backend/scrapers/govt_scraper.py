import asyncio
import re
import urllib.parse
from typing import List, Dict, Any, Optional
import httpx
from bs4 import BeautifulSoup

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "bn,en-US;q=0.9,en;q=0.8",
}

class GovtJobScraper:
    def __init__(self):
        self.bdgovt_url = "https://bdgovtjob.net/"

    async def search_jobs(self, keyword: str = "", district: Optional[str] = None, max_results: int = 25) -> List[Dict[str, Any]]:
        """
        bdgovtjob.net থেকে মাল্টিপল পেজ ঘুরে লাইভ সরকারি সার্কুলার ফেচ করে।
        """
        jobs: List[Dict[str, Any]] = []
        seen_urls = set()

        async with httpx.AsyncClient(headers=HEADERS, timeout=15.0,
                             follow_redirects=True) as client:
            # পেজ ১, ২, ৩ ঘুরে সার্কুলার আনা
            for page_num in range(1, 4):
                if len(jobs) >= max_results:
                    break

                if page_num == 1:
                    target_url = f"{self.bdgovt_url}?s={urllib.parse.quote(keyword)}" if keyword else self.bdgovt_url
                else:
                    target_url = f"{self.bdgovt_url}page/{page_num}/"
                    if keyword:
                        target_url = f"{self.bdgovt_url}page/{page_num}/?s={urllib.parse.quote(keyword)}"

                try:
                    resp = await client.get(target_url)
                    if resp.status_code == 200:
                        page_jobs = self._parse_bdgovtjob(resp.text, keyword, district, seen_urls)
                        jobs.extend(page_jobs)
                        if not page_jobs:  # যদি আর নতুন পেজ না থাকে
                            break
                except Exception as e:
                    print(f"[GovtJobScraper] Page {page_num} error: {e}")
                    break

        return jobs[:max_results]

    def _parse_bdgovtjob(self, html: str, keyword: str, district: Optional[str], seen: set) -> List[Dict[str, Any]]:
        soup = BeautifulSoup(html, "html.parser")
        results = []
        articles = soup.select("article, .post, .entry-title a, h2.entry-title a, h3 a")
        kw_lower = keyword.lower().strip() if keyword else ""

        # সাধারণ আইটি বা টেক রিলেটেড সার্চ হলে এই বাংলা টার্মগুলোর যেকোনো একটি থাকলেও পাস করবে
        tech_terms = ["কম্পিউটার", "তথ্যপ্রযুক্তি", "আইসিটি", "প্রকৌশলী", "ইঞ্জিনিয়ার", "সহকারী", "কর্মকর্তা", "অফিসার", "engineer", "computer", "ict", "it"]

        for item in articles:
            anchor = item if item.name == "a" else item.select_one("h2 a, h3 a, .entry-title a, a")
            if not anchor:
                continue

            title = anchor.get_text(strip=True)
            href = anchor.get("href", "")

            if not title or len(title) < 5 or "http" not in href:
                continue
            if any(skip in title.lower() for skip in ["home", "contact", "about", "privacy", "এডমিট কার্ড", "ফলাফল", "পরীক্ষার তারিখ"]):
                continue

            if href in seen:
                continue
            seen.add(href)

            title_lower = title.lower()

            # ফিক্স: ইংরেজি কি-ওয়ার্ড থাকলে বাংলা সাইটে সরাসরি স্ট্রিক্ট চেক না করে ফ্লেক্সিবল রাখা
            if kw_lower:
                direct_match = kw_lower in title_lower
                is_general_tech = any(t in kw_lower for t in ["software", "engineer", "react", "developer", "web", "frontend", "fullstack", "tech"])
                has_govt_tech_keyword = any(term in title_lower for term in tech_terms)

                # সরাসরি টাইটেলে না থাকলে এবং সাধারণ টেক কি-ওয়ার্ড হলেও যদি কোনো পদ না মিলে, তবেই স্কিপ করবে
                if not direct_match and not (is_general_tech or has_govt_tech_keyword):
                    continue

            company = "গণপ্রজাতন্ত্রী বাংলাদেশ সরকার"
            parts = title.split("নিয়োগ")
            if len(parts) > 1 and len(parts[0].strip()) > 3:
                company = parts[0].strip()
            elif "বিজ্ঞপ্তি" in title:
                company = title.split("বিজ্ঞপ্তি")[0].strip()

            results.append({
                "id": f"govt_{abs(hash(href)) % 1000000}",
                "title": title,
                "company": company,
                "location": "সমগ্র বাংলাদেশ (Govt)",
                "district": district or "Bangladesh",
                "experience": "বিজ্ঞপ্তি দেখুন",
                "deadline": "চলমান (বিজ্ঞপ্তি দেখুন)",
                "description": f"সরকারি চাকরির বিজ্ঞপ্তি: {title}। সম্পূর্ণ সার্কুলার ও আবেদন প্রক্রিয়ার জন্য অফিসিয়াল নোটিশ দেখুন।",
                "url": href,
                "source": "Govt",
                "is_remote": False,
                "tags": ["Govt", "সরকারি চাকরি", "BD Govt Job"],
                "match_score": 80
            })

        return results