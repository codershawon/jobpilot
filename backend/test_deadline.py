import asyncio, sys
from collections import Counter

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from app.services.job_fetcher import aggregate_all_jobs


async def main():
    jobs = await aggregate_all_jobs(keywords=["Developer", "Engineer"])
    print(f"\nমোট: {len(jobs)} jobs\n")

    by_source = {}
    for j in jobs:
        s = by_source.setdefault(j.source, {"total": 0, "dated": 0})
        s["total"] += 1
        if j.deadline:
            s["dated"] += 1

    print(f"{'SOURCE':<14} {'মোট':>6} {'তারিখ আছে':>10}  %")
    print("-" * 44)
    for src, s in sorted(by_source.items()):
        pct = 100 * s["dated"] / s["total"]
        print(f"{src:<14} {s['total']:>6} {s['dated']:>10}  {pct:.0f}%")

    print("\nজরুরিত্ব:", dict(Counter(j.urgency for j in jobs)))

    soon = sorted(
        [j for j in jobs if j.days_left is not None and j.days_left >= 0],
        key=lambda j: j.days_left,
    )[:8]
    print("\n⏰ সবচেয়ে কাছের ৮টা ডেডলাইন:")
    for j in soon:
        print(f"  {j.days_left:>3} দিন  {j.deadline}  {j.title[:48]}")


asyncio.run(main())