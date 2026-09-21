"""
CV টেক্সট থেকে স্ট্রাকচার্ড প্রোফাইল বের করা।

পুরনো llm_client.py-এর smart_local_parser()-এ তোমার নিজের নাম, ইমেইল আর
ফোন hardcoded ছিল — LLM fail করলে যেকোনো ইউজার সেটা পেত। এখানে সেটা সরানো।
কিছু না পেলে None থাকবে, ভুয়া ডেটা নয়।
"""

import re

from app.models import CVProfile
from app.services.llm.router import complete_json

# ──────────────────────────────────────────────────────────
CV_SCHEMA = {
    "type": "object",
    "properties": {
        "full_name": {"type": "string"},
        "email": {"type": "string"},
        "phone": {"type": "string"},
        "location": {"type": "string"},
        "district": {"type": "string"},
        "summary": {"type": "string"},
        "skills": {"type": "array", "items": {"type": "string"}},
        "years_of_experience": {"type": "number"},
        "preferred_job_titles": {"type": "array", "items": {"type": "string"}},
        "preferred_locations": {"type": "array", "items": {"type": "string"}},
        "open_to_remote": {"type": "boolean"},
    },
    "required": ["full_name", "skills", "preferred_job_titles"],
}

SYSTEM_PROMPT = (
    "You are an expert HR CV parser. The CV may be written in English or Bangla, "
    "or a mix of both. Extract the candidate's information accurately.\n"
    "- district: the Bangladeshi district name in English (e.g. Cumilla, Dhaka, "
    "Chattogram). If not found, leave it empty.\n"
    "- preferred_job_titles: 3-5 realistic job titles this candidate should apply "
    "for, based on their actual skills and experience.\n"
    "- years_of_experience: a number, 0 if fresher.\n"
    "- Do not invent an email or phone number. If absent, use an empty string."
)

# ফলব্যাক পার্সারের জন্য স্কিল অভিধান
TECH_SKILLS = [
    "JavaScript", "TypeScript", "React", "Next.js", "Redux", "Tailwind CSS",
    "Node.js", "Express.js", "Express", "Prisma", "MongoDB", "SQL", "PostgreSQL",
    "MySQL", "Python", "FastAPI", "Django", "Flask", "HTML", "CSS", "Sass",
    "Git", "GitHub", "Docker", "REST API", "GraphQL", "Shopify", "WordPress",
    "PHP", "Laravel", "Java", "Spring", "C#", ".NET", "Figma", "AWS", "Firebase",
]

BD_DISTRICTS_HINT = [
    "Cumilla", "Comilla", "Dhaka", "Chattogram", "Chittagong", "Sylhet",
    "Rajshahi", "Khulna", "Barishal", "Rangpur", "Mymensingh", "Gazipur",
    "Narayanganj", "Noakhali", "Feni", "Bogura", "Jashore", "Cox's Bazar",
]


# ──────────────────────────────────────────────────────────
async def extract_profile(raw_text: str) -> CVProfile:
    """LLM দিয়ে চেষ্টা, না পারলে লোকাল regex পার্সার।"""
    data = await complete_json(
        task="cv_parse",
        system=SYSTEM_PROMPT,
        user=f"CV Text:\n\n{raw_text[:8000]}",
        schema=CV_SCHEMA,
    )

    if data:
        try:
            # খালি স্ট্রিংকে None বানাই, যাতে ভুয়া ডেটা না ঢোকে
            for field in ("email", "phone", "location", "district", "summary"):
                if isinstance(data.get(field), str) and not data[field].strip():
                    data[field] = None
            return CVProfile(**data)
        except Exception as e:  # noqa: BLE001
            print(f"[CV] schema mismatch, falling back to local parser: {e}")

    return local_parse(raw_text)


def local_parse(raw_text: str) -> CVProfile:
    """কোনো ব্যক্তিগত ডেটা hardcoded নেই। না পেলে None।"""
    lines = [ln.strip() for ln in raw_text.split("\n") if ln.strip()]
    lower = raw_text.lower()

    # নাম: প্রথম যুক্তিসঙ্গত লাইন
    full_name = "Candidate"
    for line in lines[:5]:
        candidate = re.sub(r"[^A-Za-z\s.]", "", line).strip()
        if 3 <= len(candidate) <= 45 and 1 <= len(candidate.split()) <= 4:
            full_name = candidate.title()
            break

    email_m = re.search(r"[\w.+-]+@[\w-]+\.[\w.]+", raw_text)
    phone_m = re.search(
        r"(\+?880\d{10}|01\d{9})",
        raw_text.replace(" ", "").replace("-", ""),
    )

    skills = [
        s for s in TECH_SKILLS
        if re.search(r"\b" + re.escape(s.lower()) + r"\b", lower)
    ]

    district = None
    for d in BD_DISTRICTS_HINT:
        if d.lower() in lower:
            district = "Cumilla" if d == "Comilla" else (
                "Chattogram" if d == "Chittagong" else d
            )
            break

    # অভিজ্ঞতা: "3 years" বা "3+ years" ধরনের প্যাটার্ন
    years = 0.0
    yr_m = re.search(r"(\d+(?:\.\d+)?)\s*\+?\s*years?", lower)
    if yr_m:
        try:
            years = min(float(yr_m.group(1)), 50.0)
        except ValueError:
            pass

    titles: list[str] = []
    if any(s in skills for s in ("React", "Next.js", "TypeScript")):
        titles += ["Frontend Developer", "React Developer"]
    if any(s in skills for s in ("Node.js", "FastAPI", "Django", "Express")):
        titles += ["Backend Developer"]
    if not titles:
        titles = ["Software Developer"]
    if len(skills) >= 6:
        titles.append("Full Stack Developer")

    return CVProfile(
        full_name=full_name,
        email=email_m.group(0) if email_m else None,
        phone=phone_m.group(0) if phone_m else None,
        location=f"{district}, Bangladesh" if district else None,
        district=district,
        summary=(
            f"Developer with experience in {', '.join(skills[:5])}."
            if skills else None
        ),
        skills=skills,
        years_of_experience=years,
        preferred_job_titles=list(dict.fromkeys(titles))[:5],
        preferred_locations=[d for d in (district, "Dhaka", "Remote") if d],
        open_to_remote=True,
        raw_text_char_count=len(raw_text),
    )