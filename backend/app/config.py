import os
from typing import List
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # LLM Settings
    LLM_BASE_URL: str = "https://api.oxyy.ai/v1"
    LLM_API_KEY: str = ""
    LLM_ACTIVE_PROFILE: str = "premium"  # "cheap" or "premium"
    LLM_MODEL_PREMIUM: str = "claude-sonnet-4.6"
    LLM_MODEL_CHEAP: str = "deepseek-chat-v3"

    # Ultimate High-Accuracy Priority Fallback Chain
    MODEL_FALLBACK_CHAIN: List[str] = [
        # --- ১. ফ্ল্যাগশিপ টপ-টিয়ার মডেলস (বেস্ট কোয়ালিটি ও পার্সিং) ---
        "claude-sonnet-4.6",
        "claude-sonnet-4.5",
        "gpt-5.4",
        "gpt-5.2",
        "gpt-5.2-codex",
        "claude-opus-4.6",
        "gemini-3.7-flash-thinking",
        "gemini-3.1-pro",
        "grok-4.20-reasoning",
        "kimi-k3",
        "deepseek-r1",
        "deepseek-v3.2",

        # --- ২. সেকেন্ডারি ফাস্ট মডেলস ---
        "claude-haiku-4.5",
        "gpt-4o",
        "gemini-2.5-pro",
        "qwen3.7-plus",

        # --- ৩. ফ্রি ও আল্ট্রা-চিপ ব্যাকআপ (Oxyy Free) ---
        "dots-3-note-preview",
        "lyria-3-pro-preview",
        "granite-4.0-h-micro",
        "qwen3-7-flash"
    ]

    # ---- 2. Free Backup Provider (OpenRouter) ----
    OPENROUTER_BASE_URL: str = "https://openrouter.ai/api/v1"
    OPENROUTER_API_KEY: str = ""
    OPENROUTER_FREE_MODELS: List[str] = [
        "deepseek/deepseek-r1:free",
        "meta-llama/llama-3.3-70b-instruct:free",
        "google/gemini-2.0-flash-lite:free",
        "qwen/qwen-2.5-coder-32b-instruct:free"
    ]

    # ---- 3. Bangladesh Geo API (ডায়নামিক ৬৪ জেলা) ----
    BD_DISTRICTS_API_URL: str = "https://bdapis.vercel.app/geo/v2.0/districts"

    # App Settings
    APP_ENV: str = "development"
    DATA_DIR: str = "./data"
    JOB_FETCH_MIN_DELAY_SECONDS: int = 2

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def active_model_name(self) -> str:
        if self.LLM_ACTIVE_PROFILE.lower() == "premium":
            return self.LLM_MODEL_PREMIUM
        return self.LLM_MODEL_CHEAP


settings = Settings()