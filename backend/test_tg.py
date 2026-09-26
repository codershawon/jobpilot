import asyncio
import sys

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

from app.config import settings
from app.services import telegram


async def main():
    bot = await telegram.check_bot()
    if not bot:
        print("❌ বট সংযুক্ত নয় — TELEGRAM_BOT_TOKEN দেখুন")
        return
    print(f"✅ বট: @{bot.get('username')}")

    chat = settings.TELEGRAM_TEST_CHAT_ID
    if not chat:
        print("⚠ TELEGRAM_TEST_CHAT_ID নেই")
        return

    ok = await telegram.send_welcome(chat, "Shawon")
    print("মেসেজ গেছে?" , "✅" if ok else "❌")


asyncio.run(main())