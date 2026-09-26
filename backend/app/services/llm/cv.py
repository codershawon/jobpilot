"""
CV টেক্সট থেকে স্ট্রাকচার্ড প্রোফাইল বের করা।

পুরনো llm_client.py-এর smart_local_parser()-এ তোমার নিজের নাম, ইমেইল আর
ফোন hardcoded ছিল — LLM fail করলে যেকোনো ইউজার সেটা পেত। এখানে সেটা সরানো।
কিছু না পেলে None থাকবে, ভুয়া ডেটা নয়।
"""

import re

from app.models import CVProfile
from app.services.classifier import detect_function_from_profile
from app.services.llm.router import complete_json


def _with_function(profile: CVProfile) -> CVProfile:
    """প্রোফাইলে কাজের ক্ষেত্র বসিয়ে দেয়। LLM আর লোকাল — দুই পথেই লাগবে।"""
    profile.job_function = detect_function_from_profile(
        skills=profile.skills,
        preferred_titles=profile.preferred_job_titles,
        summary=profile.summary,
    )
    return profile

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
        # ── এই দুইটা এতদিন চাওয়াই হয়নি, তাই কখনো আসেনি ──
        "work_experience": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "title": {"type": "string"},
                    "company": {"type": "string"},
                    "duration": {"type": "string"},
                    "highlights": {"type": "array", "items": {"type": "string"}},
                },
                "required": ["title", "company"],
            },
        },
        "education": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "degree": {"type": "string"},
                    "institution": {"type": "string"},
                    "year": {"type": "string"},
                },
                "required": ["degree", "institution"],
            },
        },
    },
    "required": ["full_name", "skills", "preferred_job_titles"],
}

SYSTEM_PROMPT = (
    "You are an expert HR CV parser. The CV may be written in English or Bangla, "
    "or a mix of both. Extract EVERY field below from the CV.\n"
    "- district: the Bangladeshi district name in English (e.g. Cumilla, Dhaka, "
    "Chattogram). If not found, leave it empty.\n"
    "- skills: every technology, tool, framework and language named anywhere in "
    "the CV, including inside project descriptions. Do not stop at the skills "
    "section.\n"
    "- work_experience: every job, internship and freelance role. For each, give "
    "title, company, duration as written, and 2-3 highlights taken from the CV. "
    "Never leave this empty if the CV names any employer.\n"
    "- education: every degree, diploma or certificate with institution and year.\n"
    "- preferred_job_titles: 4-6 job titles this candidate should apply for. "
    "Include both the exact titles they have held and adjacent ones their skills "
    "qualify them for. These become job-search keywords, so use common Bangladeshi "
    "job-board wording (e.g. 'Software Engineer', 'Frontend Developer', "
    "'MERN Stack Developer').\n"
    "- years_of_experience: a number, 0 if fresher. Count internships as "
    "experience.\n"
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
            return _with_function(CVProfile(**data))
        except Exception as e:  # noqa: BLE001
            print(f"[CV] schema mismatch, falling back to local parser: {e}")

    return _with_function(local_parse(raw_text))


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