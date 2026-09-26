# test_cache.py
import asyncio, sys, time
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
from app.services.job_fetcher import aggregate_all_jobs

async def main():
    t = time.time()
    a = await aggregate_all_jobs(keywords=["Developer"])
    print(f"\n১ম বার: {len(a)} jobs, {time.time()-t:.1f} সেকেন্ড\n")

    t = time.time()
    b = await aggregate_all_jobs(keywords=["Developer"])
    print(f"\n২য় বার: {len(b)} jobs, {time.time()-t:.1f} সেকেন্ড")

asyncio.run(main())