"""
JobPilot settings.

পুরনো Oxyy-নির্ভর কনফিগ বাদ। এখন কাজ অনুযায়ী মডেল টিয়ার,
আর যে প্রোভাইডারের key .env-এ আছে শুধু সেটাই ব্যবহার হবে।
"""

from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):

     # ──────────────── Auth (Clerk) ────────────────
    CLERK_ISSUER: str = ""              # যেমন https://your-app-12.clerk.accounts.dev
    CLERK_ALLOWED_PARTIES: List[str] = []   # যেমন ["http://localhost:3000"]

    # ──────────────── Security ────────────────
    MAX_UPLOAD_MB: int = 5
    CORS_ORIGINS: str = "http://localhost:3000,http://127.0.0.1:3000"
    # ──────────────── Database ────────────────
    # অ্যাপ চলবে pooler এন্ডপয়েন্টে
    DATABASE_URL: str = "sqlite+aiosqlite:///./test.db"
    # Alembic migration চলবে direct এন্ডপয়েন্টে (pooler DDL-এ সমস্যা করে)
    DATABASE_URL_DIRECT: str = ""

    # ──────────────── LLM providers ────────────────
    # যেটার key ফাঁকা, সেটা নিজে থেকেই স্কিপ হবে।
    GEMINI_API_KEY: str = ""
    GROQ_API_KEY: str = ""
    OPENROUTER_API_KEY: str = ""

    # ──────────────── Model tiers ────────────────
    # তালিকার ক্রম = fallback-এর ক্রম। উপরেরটা আগে চেষ্টা হবে।
    #
    # fast  → ভলিউম বেশি, মান মাঝারি হলেও চলে (CV পার্স, ম্যাচ ব্যাখ্যা)
    # smart → ইউজার নিজে পড়বে ও পাঠাবে, মান এখানেই সব (কভার লেটার)
    TIER_FAST: List[str] = [
        "gemini/gemini-2.5-flash-lite",
        "groq/openai/gpt-oss-120b",
        "openrouter/google/gemma-4-27b-it:free",
    ]
    TIER_SMART: List[str] = [
        "gemini/gemini-2.5-flash",
        "gemini/gemini-2.5-flash-lite",
        "groq/openai/gpt-oss-120b",
    ]

    # ──────────────── Embeddings (দিন ১০-এ চালু হবে) ────────────────
    EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"

    # ──────────────── App ────────────────
    APP_ENV: str = "development"
    DATA_DIR: str = "./data"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @property
    def has_any_llm(self) -> bool:
        return bool(self.GEMINI_API_KEY or self.GROQ_API_KEY or self.OPENROUTER_API_KEY)

    @property
    def cors_origins(self) -> List[str]:
        return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]


settings = Settings()