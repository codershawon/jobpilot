"""
অফিসিয়াল নিয়োগ পোর্টাল — স্ক্র্যাপ করা যায় না এমন সাইটের সৎ লিংক।

ব্যাংক, BPSC, chakri.com-এর মতো সাইটে WAF বা robots.txt আছে।
সেগুলো বাইপাস না করে ইউজারকে সরাসরি পোর্টালে পাঠানো হয়।
"""

from fastapi import APIRouter

from scrapers.portal_links import PortalLinksSource

router = APIRouter(prefix="/portals", tags=["Portals"])

_source = PortalLinksSource()


@router.get("")
async def get_portals(category: str | None = None):
    portals = await _source.fetch()

    if category and category != "all":
        portals = [p for p in portals if p.get("category") == category]

    return {"total": len(portals), "portals": portals}