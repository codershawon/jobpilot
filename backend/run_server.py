import sys
import asyncio
import uvicorn

if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
    
    # loop="asyncio" দিলে এটি উইন্ডোজের সেট করা Proactor লুপ ব্যবহার করবে
    uvicorn.run("app.main:app", host="127.0.0.1", port=8000, reload=True, loop="asyncio")