import asyncio
from scrapers.govt_scraper import GovtJobScraper

async def main():
    scraper = GovtJobScraper()
    
    # এখানে max_results বাড়িয়ে ২০ বা ৩০ দিন
    print("সবগুলো লাইভ সরকারি সার্কুলার ফেচ করা হচ্ছে (Up to 25)...")
    all_jobs = await scraper.search_jobs(keyword="", max_results=25)
    print(f"সর্বমোট সার্কুলার পাওয়া গেছে: {len(all_jobs)} টি\n")
    
    for idx, j in enumerate(all_jobs, 1):
        print(f"{idx}. [{j['source']}] {j['title']}")
        print(f"   প্রতিষ্ঠান: {j['company']}")
        print(f"   লিংক: {j['url']}\n")

if __name__ == "__main__":
    asyncio.run(main())