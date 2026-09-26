# test_llm.py
import asyncio, litellm
from app.config import settings

litellm.suppress_debug_info = True

TESTS = [
    ("github/gpt-4o-mini", settings.GITHUB_API_KEY),
    ("openrouter/openrouter/free", settings.OPENROUTER_API_KEY),
    ("gemini/gemini-flash-lite-latest", settings.GEMINI_API_KEY),
]

async def main():
    for model, key in TESTS:
        if not key:
            print(f"⏭️  {model:<34} key নেই")
            continue
        try:
            r = await litellm.acompletion(
                model=model,
                messages=[{"role": "user", "content": "Say OK"}],
                api_key=key, max_tokens=5, timeout=30,
            )
            print(f"✅ {model:<34} → {r.choices[0].message.content.strip()}")
        except Exception as e:
            print(f"❌ {model:<34} → {type(e).__name__}: {str(e)[:90]}")

asyncio.run(main())