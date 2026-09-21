import asyncio
from scrapers.bangladesh_bank_scraper import BangladeshBankScraper
from scrapers.teletalk_alljobs_scraper import TeletalkAllJobsScraper

async def test_both():
    print("=== TESTING BANGLADESH BANK ===")
    bb = BangladeshBankScraper()
    b_jobs = await bb.search_jobs()
    print(f"Bangladesh Bank Jobs Found: {len(b_jobs)}")
    for j in b_jobs[:3]:
        print(f" -> [{j['id']}] {j['title']} | {j['company']}")

    print("\n=== TESTING TELETALK ALLJOBS ===")
    tt = TeletalkAllJobsScraper()
    t_jobs = await tt.search_jobs()
    print(f"Teletalk Jobs Found: {len(t_jobs)}")
    for j in t_jobs[:3]:
        print(f" -> [{j['id']}] {j['title']} | {j['company']}")

if __name__ == "__main__":
    asyncio.run(test_both())