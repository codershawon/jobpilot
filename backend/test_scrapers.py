import asyncio
from scrapers.govt_scraper import GovtJobScraper
from scrapers.teletalk_alljobs_scraper import TeletalkAllJobsScraper
from scrapers.bangladesh_bank_scraper import BangladeshBankScraper

async def test_all_govt():
    print("Fetching BDGovtJob...")
    bd_jobs = await GovtJobScraper().search_jobs()
    print(f"-> BDGovtJob: {len(bd_jobs)} jobs")

    print("\nFetching Teletalk AllJobs API...")
    tt_jobs = await TeletalkAllJobsScraper().search_jobs()
    print(f"-> Teletalk: {len(tt_jobs)} jobs")
    if tt_jobs:
        print(f"   Sample: {tt_jobs[0]['title']} | Org: {tt_jobs[0]['company']}")
        print(f"   Apply URL: {tt_jobs[0]['url']}")

    print("\nFetching Bangladesh Bank...")
    bb_jobs = await BangladeshBankScraper().search_jobs()
    print(f"-> Bangladesh Bank: {len(bb_jobs)} circulars")

if __name__ == "__main__":
    asyncio.run(test_all_govt())