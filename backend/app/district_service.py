import httpx
from typing import List

# ব্যাকআপ ডিফল্ট তালিকা (যদি ইন্টারনেট/এপিআই ডাউন থাকে)
FALLBACK_DISTRICTS = [
    "Dhaka", "Chattogram", "Cumilla", "Sylhet", "Rajshahi", "Khulna",
    "Barishal", "Rangpur", "Mymensingh", "Gazipur", "Narayanganj",
    "Cox's Bazar", "Noakhali", "Feni", "Brahmanbaria", "Chandpur",
    "Bogura", "Jashore", "Kushtia", "Pabna", "Tangail", "Dinajpur"
]

_cached_districts: List[str] = []

async def get_all_districts() -> List[str]:
    """বাংলাদেশ জিও API থেকে লাইভ জেলা লোড ও ক্যাশ করে"""
    global _cached_districts
    if _cached_districts:
        return _cached_districts

    api_url = "https://bdapis.vercel.app/geo/v2.0/districts"
    try:
        async with httpx.AsyncClient(timeout=6.0) as client:
            res = await client.get(api_url)
            if res.status_code == 200:
                data = res.json().get("data", [])
                districts = [d.get("district", "").strip() for d in data if d.get("district")]
                if districts:
                    _cached_districts = sorted(list(set(districts)))
                    return _cached_districts
    except Exception as e:
        print(f"[District API Notice]: Using fallback list ({e})")

    _cached_districts = FALLBACK_DISTRICTS
    return _cached_districts