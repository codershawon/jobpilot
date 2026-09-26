# test_rw.py
import asyncio, sys
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
from scrapers.extra_sources import fetch_reliefweb

async def main():
    jobs = await fetch_reliefweb(limit=10)
    print(f"{len(jobs)} jobs")
    for j in jobs[:5]:
        print(f"  {str(j.deadline):<12} {j.company[:25]:<27} {j.title[:45]}")

asyncio.run(main())