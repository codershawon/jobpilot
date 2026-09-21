"""
সরকারি ও ব্যাংক নিয়োগ পোর্টাল — সৎ লিংক কার্ড।

আগের bangladesh_bank_scraper.py erecruitment.bb.org.bd স্ক্র্যাপ করার
চেষ্টা করত, কিন্তু সাইটে WAF আছে (রেসপন্সে window["bobcmn"] থাকে)। তাই
if শর্তটা প্রায় কখনো pass করত না, আর প্রতিবার নিচের hardcoded ভুয়া
"জব" ফেরত যেত। ইউজার সেটা ক্লিক করে হতাশ হতো।

WAF মানে সাইটটা স্পষ্ট বলছে "আমরা বট চাই না"। সেটা বাইপাস করার
চেয়ে সৎভাবে পোর্টালের লিংক দেওয়াই ভালো — ইউজার ভ্যালু পায়,
আর আমাদের কোনো ঝুঁকি থাকে না।

এগুলো kind="portal", তাই ম্যাচিং স্কোরিং বা জব কাউন্টে ঢুকবে না।
UI-তে আলাদা সেকশনে দেখাবে।
"""

from __future__ import annotations

from typing import Any

PORTALS: list[dict[str, Any]] = [
    {
        "external_id": "portal_bb_bsc",
        "title": "ব্যাংকার্স সিলেকশন কমিটি — সমন্বিত ব্যাংক নিয়োগ",
        "company": "বাংলাদেশ ব্যাংক (BSCS)",
        "url": "https://erecruitment.bb.org.bd/onlineapp/joblist.php",
        "description": (
            "সোনালী, রূপালী, জনতা, অগ্রণী, বেসিক ব্যাংকসহ রাষ্ট্রায়ত্ত "
            "ব্যাংকসমূহের সমন্বিত নিয়োগ বিজ্ঞপ্তি ও অনলাইন আবেদন।"
        ),
        "category": "bank",
    },
    {
        "external_id": "portal_bpsc",
        "title": "বাংলাদেশ সরকারি কর্ম কমিশন — BCS ও নন-ক্যাডার",
        "company": "BPSC",
        "url": "http://www.bpsc.gov.bd/",
        "description": "বিসিএস, নন-ক্যাডার এবং পিএসসির অন্যান্য নিয়োগ বিজ্ঞপ্তি।",
        "category": "govt",
    },
    {
        "external_id": "portal_bpsc_teletalk",
        "title": "BPSC অনলাইন আবেদন পোর্টাল",
        "company": "BPSC × Teletalk",
        "url": "http://bpsc.teletalk.com.bd/",
        "description": "পিএসসির চলমান নিয়োগের অনলাইন আবেদন ও প্রবেশপত্র।",
        "category": "govt",
    },
    {
        "external_id": "portal_smartjob",
        "title": "Smart Job — সরকারি চাকরি কেন্দ্রীয় পোর্টাল",
        "company": "গণপ্রজাতন্ত্রী বাংলাদেশ সরকার",
        "url": "https://smartjob.gov.bd/",
        "description": (
            "মন্ত্রণালয়, অধিদপ্তর ও স্বায়ত্তশাসিত প্রতিষ্ঠানের "
            "সরকারি চাকরি এক জায়গায়।"
        ),
        "category": "govt",
    },
    {
        "external_id": "portal_national",
        "title": "জাতীয় তথ্য বাতায়ন — নিয়োগ সেবা",
        "company": "Bangladesh National Portal",
        "url": "https://bangladesh.gov.bd/",
        "description": (
            "BIWTA, BADC, BWDB, BJRI, DLS, Coast Guard সহ বিভিন্ন "
            "প্রতিষ্ঠানের নিজস্ব recruitment portal-এর তালিকা।"
        ),
        "category": "govt",
    },
]


class PortalLinksSource:
    """স্ক্র্যাপ করে না — কিউরেটেড অফিসিয়াল লিংক দেয়।"""

    id = "official_portals"
    category = "portal"

    async def fetch(self) -> list[dict[str, Any]]:
        results = []
        for p in PORTALS:
            results.append({
                **p,
                "source_id": self.id,
                "kind": "portal",        # ← জব নয়, পোর্টাল
                "district": "Bangladesh",
                "location": "বাংলাদেশ",
                "is_remote": False,
                "deadline": None,
                "salary": None,
                "tags": ["Official", "Portal"],
                "note": "স্বয়ংক্রিয় সংগ্রহ সম্ভব নয় — সরাসরি পোর্টালে দেখুন",
            })
        print(f"[{self.id}] {len(results)} পোর্টাল লিংক")
        return results