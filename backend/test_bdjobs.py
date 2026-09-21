import asyncio
from scrapers.bdjobs_scraper import BdjobsScraper

async def main():
    scraper = BdjobsScraper()
    print("বিডিজবস থেকে মাল্টি-পেজ লাইভ সার্কুলার ফেচ করা হচ্ছে (Up to 15)...")
    jobs = await scraper.search_jobs(keyword="Software Engineer", district="Dhaka", max_results=15)
    print(f"সর্বমোট সার্কুলার পাওয়া গেছে: {len(jobs)} টি\n")
    for idx, j in enumerate(jobs, 1):
        print(f"{idx}. [{j['source']}] {j['title']} at {j['company']}")
        print(f"   Link: {j['url']}\n")

if __name__ == "__main__":
    asyncio.run(main())