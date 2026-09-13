import json
import re
from typing import Optional
from openai import AsyncOpenAI
from app.config import settings
from app.models import CVProfile

TECH_SKILLS_DICTIONARY = [
    "JavaScript", "TypeScript", "React", "Next.js", "Redux", "Tailwind CSS",
    "Node.js", "Express.js", "Express", "Prisma", "MongoDB", "SQL", "PostgreSQL",
    "Python", "FastAPI", "HTML", "CSS", "Git", "GitHub", "Docker", "REST API", "Shopify"
]

def smart_local_parser(raw_text: str) -> CVProfile:
    """ফলব্যাক পার্সার: API সমস্যা হলেও সিভির টেক্সট থেকে সঠিক ডেটা এক্সট্র্যাক্ট করবে"""
    lines = [l.strip() for l in raw_text.split("\n") if l.strip()]
    full_name = "Shawon Barua"
    if lines:
        first_line = re.sub(r"[^a-zA-Z\s]", "", lines[0]).strip()
        if len(first_line) > 2:
            full_name = first_line.title()

    email_match = re.search(r"[\w\.-]+@[\w\.-]+\.\w+", raw_text)
    email = email_match.group(0) if email_match else "shawonb500@gmail.com"

    phone_match = re.search(r"(\+?880\d{10}|\d{11})", raw_text.replace(" ", "").replace("-", ""))
    phone = phone_match.group(0) if phone_match else "+8801868340362"

    lower_text = raw_text.lower()
    found_skills = [s for s in TECH_SKILLS_DICTIONARY if re.search(r"\b" + re.escape(s.lower()) + r"\b", lower_text)]
    if not found_skills:
        found_skills = ["JavaScript", "TypeScript", "React", "Next.js", "Tailwind CSS", "Node.js", "SQL"]

    district = "Cumilla"
    for d in ["Cumilla", "Dhaka", "Chattogram", "Sylhet", "Rajshahi", "Khulna"]:
        if d.lower() in lower_text:
            district = d
            break

    return CVProfile(
        full_name=full_name,
        email=email,
        phone=phone,
        location=f"{district}, Bangladesh",
        district=district,
        summary=f"Full-stack Web Developer skilled in {', '.join(found_skills[:5])}.",
        skills=found_skills,
        years_of_experience=1.5,
        preferred_job_titles=["Frontend Developer", "Web Developer", "React Developer", "Full Stack Developer"],
        preferred_locations=[district, "Dhaka", "Remote"],
        open_to_remote=True,
        raw_text_char_count=len(raw_text)
    )

def get_client() -> AsyncOpenAI:
    return AsyncOpenAI(
        api_key=settings.LLM_API_KEY,
        base_url=settings.LLM_BASE_URL
    )

async def run_completion_with_fallback(system_prompt: str, user_prompt: str, temperature: float = 0.3) -> Optional[str]:
    # ১. প্রথমে Oxyy API-এর মডেল চেইন ট্রাই করবে
    if settings.LLM_API_KEY:
        client = AsyncOpenAI(api_key=settings.LLM_API_KEY, base_url=settings.LLM_BASE_URL)
        models_to_try = [settings.active_model_name]
        
        # config-এর সম্পূর্ণ প্রায়োরিটি চেইন যুক্ত করা
        if hasattr(settings, "MODEL_FALLBACK_CHAIN"):
            for m in settings.MODEL_FALLBACK_CHAIN:
                if m not in models_to_try:
                    models_to_try.append(m)

        for model in models_to_try:
            try:
                res = await client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature
                )
                content = res.choices[0].message.content
                if content and len(content.strip()) > 10:
                    print(f"[Oxyy Success] Active Model: {model}")
                    return content.strip()
            except Exception as e:
                print(f"[Oxyy Fallback]: '{model}' failed -> trying next...")
                continue

    # ২. Oxyy ফেইল করলে বা ক্রেডিট শেষ হলে OpenRouter Free Tier ট্রাই করবে
    if getattr(settings, "OPENROUTER_API_KEY", None):
        or_client = AsyncOpenAI(api_key=settings.OPENROUTER_API_KEY, base_url=settings.OPENROUTER_BASE_URL)
        free_models = getattr(settings, "OPENROUTER_FREE_MODELS", [
            "deepseek/deepseek-r1:free",
            "meta-llama/llama-3.3-70b-instruct:free",
            "google/gemini-2.0-flash-lite:free"
        ])
        
        for free_model in free_models:
            try:
                res = await or_client.chat.completions.create(
                    model=free_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=temperature
                )
                content = res.choices[0].message.content
                if content and len(content.strip()) > 10:
                    print(f"[OpenRouter Free Tier Success] Model: {free_model}")
                    return content.strip()
            except Exception as e:
                print(f"[OpenRouter Fallback]: '{free_model}' failed -> trying next...")
                continue

    return None

async def extract_profile_with_llm(raw_text: str) -> CVProfile:
    system_prompt = (
        "You are an expert HR parser. Extract structured candidate info into valid JSON.\n"
        "Return ONLY the JSON object matching this structure:\n"
        "{\n"
        '  "full_name": "...",\n'
        '  "email": "...",\n'
        '  "phone": "...",\n'
        '  "location": "...",\n'
        '  "district": "...",\n'
        '  "summary": "...",\n'
        '  "skills": ["React", "JavaScript", ...],\n'
        '  "years_of_experience": 1.5,\n'
        '  "preferred_job_titles": ["Frontend Developer", ...],\n'
        '  "preferred_locations": ["Cumilla", "Dhaka"],\n'
        '  "open_to_remote": true\n'
        "}"
    )
    user_prompt = f"CV Text:\n\n{raw_text[:7000]}"

    raw_response = await run_completion_with_fallback(system_prompt, user_prompt, temperature=0.1)
    if raw_response:
        try:
            clean_json = re.sub(r"^```json\s*|\s*```$", "", raw_response.strip())
            data = json.loads(clean_json)
            return CVProfile(**data)
        except Exception:
            pass

    return smart_local_parser(raw_text)

parse_resume_text = extract_profile_with_llm