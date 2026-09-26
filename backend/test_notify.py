import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from app.worker import send_deadline_reminders, send_digests


async def main():
    print("ডাইজেস্ট:", await send_digests())
    print("রিমাইন্ডার:", await send_deadline_reminders())


asyncio.run(main())