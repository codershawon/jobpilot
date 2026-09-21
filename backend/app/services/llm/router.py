"""
পুরো অ্যাপে LLM কলের একমাত্র দরজা।

কোথাও আর সরাসরি AsyncOpenAI ক্লায়েন্ট বানানো হবে না।
সব জায়গা থেকে শুধু complete() বা complete_json() ডাকা হবে।

নীতি:
  1. যে প্রোভাইডারের key .env-এ নেই, সেটা নিজে থেকেই বাদ পড়বে
  2. একটা মডেল fail করলে পরেরটা — litellm নিজেই সামলায়
  3. সব fail করলে None ফেরত — ভুয়া টেক্সট নয়
"""

import json
import re
from typing import Any

import litellm
from litellm import Router

from app.config import settings

# litellm-এর নিজস্ব বাচালতা বন্ধ
litellm.suppress_debug_info = True
litellm.set_verbose = False


# ──────────────────────────────────────────────────────────
# ১. যে প্রোভাইডারের key আছে শুধু তারই মডেল তালিকায় ঢুকবে
# ──────────────────────────────────────────────────────────
def _api_key_for(model: str) -> str:
    if model.startswith("gemini/"):
        return settings.GEMINI_API_KEY
    if model.startswith("groq/"):
        return settings.GROQ_API_KEY
    if model.startswith("openrouter/"):
        return settings.OPENROUTER_API_KEY
    return ""


def _build_model_list() -> list[dict]:
    model_list: list[dict] = []
    for tier_name, models in (
        ("fast", settings.TIER_FAST),
        ("smart", settings.TIER_SMART),
    ):
        for model in models:
            key = _api_key_for(model)
            if not key:
                continue  # key নেই → চুপচাপ স্কিপ
            model_list.append(
                {
                    "model_name": tier_name,
                    "litellm_params": {
                        "model": model,
                        "api_key": key,
                    },
                }
            )
    return model_list


_MODEL_LIST = _build_model_list()

router: Router | None = None
if _MODEL_LIST:
    router = Router(
        model_list=_MODEL_LIST,
        num_retries=2,
        timeout=45,
        # smart-এ কিছু না থাকলে fast-এ নেমে যাবে
        fallbacks=[{"smart": ["fast"]}, {"fast": ["smart"]}],
        allowed_fails=3,
        cooldown_time=60,
    )
    _active = sorted({m["litellm_params"]["model"] for m in _MODEL_LIST})
    print(f"[LLM] {len(_active)} model(s) সক্রিয়: {', '.join(_active)}")
else:
    print("[LLM] ⚠️  কোনো API key পাওয়া যায়নি — local fallback ব্যবহার হবে")


# ──────────────────────────────────────────────────────────
# ২. কোন কাজ কোন টিয়ারে যাবে
# ──────────────────────────────────────────────────────────
TASK_TIER: dict[str, str] = {
    "cv_parse": "fast",
    "match_explain": "fast",
    "scam_detect": "fast",
    "tag_normalize": "fast",
    "cover_letter": "smart",   # ইউজার এটা পড়বে ও পাঠাবে
    "screening": "smart",
    "cv_tailor": "smart",
}


# ──────────────────────────────────────────────────────────
# ৩. মূল কল
# ──────────────────────────────────────────────────────────
async def complete(
    task: str,
    system: str,
    user: str,
    *,
    schema: dict[str, Any] | None = None,
    temperature: float = 0.2,
    max_tokens: int | None = None,
) -> str | None:
    """
    একটা LLM কল করে টেক্সট ফেরত দেয়।
    কোনো প্রোভাইডার না থাকলে বা সব fail করলে None ফেরত দেয়।
    """
    if router is None:
        return None

    kwargs: dict[str, Any] = {
        "model": TASK_TIER.get(task, "fast"),
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
    }
    if max_tokens:
        kwargs["max_tokens"] = max_tokens

    # JSON চাইলে আগে strict schema, সেটা প্রোভাইডার না মানলে সাধারণ json_object
    attempts: list[dict[str, Any]] = []
    if schema:
        attempts.append(
            {
                **kwargs,
                "response_format": {
                    "type": "json_schema",
                    "json_schema": {"name": task, "schema": schema},
                },
            }
        )
        attempts.append({**kwargs, "response_format": {"type": "json_object"}})
    attempts.append(kwargs)

    last_error: Exception | None = None
    for attempt in attempts:
        try:
            res = await router.acompletion(**attempt)
            content = res.choices[0].message.content
            if not content or not content.strip():
                continue

            _log_usage(task, res)
            return content.strip()
        except Exception as e:  # noqa: BLE001
            last_error = e
            continue

    print(f"[LLM FAIL] {task}: {type(last_error).__name__} — {str(last_error)[:140]}")
    return None


async def complete_json(
    task: str,
    system: str,
    user: str,
    schema: dict[str, Any],
    temperature: float = 0.1,
) -> dict | None:
    """JSON চেয়ে কল করে, পার্স করে dict ফেরত দেয়। না পারলে None।"""
    raw = await complete(
        task,
        system + "\n\nReturn ONLY a valid JSON object. No prose, no markdown fences.",
        user,
        schema=schema,
        temperature=temperature,
    )
    if not raw:
        return None
    return _extract_json(raw)


# ──────────────────────────────────────────────────────────
# ৪. সহায়ক
# ──────────────────────────────────────────────────────────
def _extract_json(text: str) -> dict | None:
    """মডেল ```json ফেন্স বা বাড়তি লেখা দিলেও JSON বের করে আনে।"""
    cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", text.strip(), flags=re.MULTILINE)

    try:
        data = json.loads(cleaned)
        return data if isinstance(data, dict) else None
    except json.JSONDecodeError:
        pass

    # প্রথম { থেকে শেষ } পর্যন্ত কেটে আবার চেষ্টা
    start, end = cleaned.find("{"), cleaned.rfind("}")
    if start != -1 and end > start:
        try:
            data = json.loads(cleaned[start : end + 1])
            return data if isinstance(data, dict) else None
        except json.JSONDecodeError:
            pass

    return None


def _log_usage(task: str, res: Any) -> None:
    """খরচ লগিং — পরে এখান থেকেই Cost Dashboard বানাবে।"""
    try:
        usage = res.usage
        cost = (getattr(res, "_hidden_params", {}) or {}).get("response_cost") or 0.0
        print(
            f"[LLM] {task:<14} {res.model:<34} "
            f"in={usage.prompt_tokens:>5} out={usage.completion_tokens:>4} "
            f"${cost:.6f}"
        )
    except Exception:  # noqa: BLE001
        pass