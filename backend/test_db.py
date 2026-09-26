import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from app.core.database import AsyncSessionLocal
from app.services.job_fetcher import aggregate_all_jobs
from app.services.job_store import deactivate_expired, query_jobs, upsert_jobs


async def main():
    jobs = await aggregate_all_jobs(keywords=["Developer", "Engineer"])
    print(f"\nফেচ: {len(jobs)}")

    async with AsyncSessionLocal() as db:
        new_ids = await upsert_jobs(db, jobs)
        print(f"নতুন: {len(new_ids)}")

        urgent = await query_jobs(db, max_days_left=7, limit=10)
        print(f"\n⏰ ৭ দিনের মধ্যে {len(urgent)}টি:")
        for j in urgent[:5]:
            print(f"  {j.days_left:>3} দিন  {j.title[:50]}")

        govt = await query_jobs(db, sectors=["govt"], limit=500)
        print(f"\nসরকারি: {len(govt)}")

        print(f"মেয়াদোত্তীর্ণ নিষ্ক্রিয়: {await deactivate_expired(db)}")


asyncio.run(main())