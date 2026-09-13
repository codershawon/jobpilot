from typing import List
import httpx
import logging

logger = logging.getLogger(__name__)

# পাবলিক এপিআই এন্ডপয়েন্ট (বাংলাদেশের জেলা ডেটা)
BD_DISTRICTS_API_URL = "https://bdapis.com/api/v1.1/districts"

# সার্ভার ডাউন থাকলে বা ইন্টারনেট ড্রপ করলে সেফ ফলব্যাক
FALLBACK_DISTRICTS: List[str] = [
    "Bagerhat", "Bandarban", "Barguna", "Barishal", "Bhola", "Bogura",
    "Brahmanbaria", "Chandpur", "Chapai Nawabganj", "Chattogram", "Chuadanga",
    "Cox's Bazar", "Cumilla", "Dhaka", "Dinajpur", "Faridpur", "Feni",
    "Gaibandha", "Gazipur", "Gopalganj", "Habiganj", "Jamalpur", "Jashore",
    "Jhalokathi", "Jhenaidah", "Joypurhat", "Khagrachhari", "Khulna",
    "Kishoreganj", "Kurigram", "Kushtia", "Lakshmipur", "Lalmonirhat",
    "Madaripur", "Magura", "Manikganj", "Meherpur", "Moulvibazar",
    "Munshiganj", "Mymensingh", "Naogaon", "Narail", "Narayanganj",
    "Narsingdi", "Natore", "Netrokona", "Nilphamari", "Noakhali", "Pabna",
    "Panchagarh", "Patuakhali", "Pirojpur", "Rajbari", "Rajshahi",
    "Rangamati", "Rangpur", "Satkhira", "Shariatpur", "Sherpur",
    "Sirajganj", "Sunamganj", "Sylhet", "Tangail", "Thakurgaon"
]

_cached_districts: List[str] = []

async def get_all_districts() -> List[str]:
    global _cached_districts

    # ১. ক্যাশ করা থাকলে সরাসরি মেমোরি থেকে রিটার্ন (০ms ল্যাটেন্সি)
    if _cached_districts:
        return _cached_districts

    # ২. এক্সটার্নাল ওপেন API থেকে ডাইনামিক ফেচ
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(BD_DISTRICTS_API_URL)
            if response.status_code == 200:
                payload = response.json()
                raw_data = payload.get("data", [])
                extracted = [
                    item.get("district")
                    for item in raw_data
                    if item.get("district")
                ]

                if extracted:
                    _cached_districts = sorted(extracted)
                    logger.info("Successfully fetched %d districts from public API.", len(_cached_districts))
                    return _cached_districts
    except Exception as e:
        logger.warning("Failed to fetch districts from live API: %s. Using fallback.", e)

    _cached_districts = sorted(FALLBACK_DISTRICTS)
    return _cached_districts