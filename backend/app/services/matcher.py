"""
জব ম্যাচিং ও স্কোরিং।

আগের ভার্সনের মূল বাগ: evaluate_job_with_llm() আর generate_cover_letter()
সরাসরি get_client() ডাকত — কোনো fallback ছিল না। Oxyy key মরতেই দুটোই
নীরবে fail করে hardcoded টেক্সট দিত।

এখন সব কল router.complete() দিয়ে যায়, তাই যেকোনো একটা প্রোভাইডার
কাজ করলেই চলবে। আর LLM কলগুলো asyncio.gather() দিয়ে সমান্তরাল।
"""

import asyncio
import re
from typing import List

from app.models import CVProfile, JobItem
from app.services.llm.router import complete, complete_json

# নন-টেক বা অ্যাডমিন পদের নেগেটিভ কি-ওয়ার্ড
NON_TECH_PENALTY_KEYWORDS = [
    "office assistant", "virtual assistant", "administrative", "bookkeeper",
    "data entry", "receptionist", "customer service", "telecaller", "call center",
]

MATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "match_score": {"type": "integer"},
        "match_reason": {"type": "string"},
    },
    "required": ["match_score", "match_reason"],
}


# ──────────────────────────────────────────────────────────
# ১. হিউরিস্টিক স্কোর — ফ্রি, তাৎক্ষণিক, সব জবের জন্য
# ──────────────────────────────────────────────────────────
def calculate_base_heuristic_score(profile: CVProfile, job: JobItem) -> int:
    score = 20.0
    title_lower = (job.title or "").lower()
    job_text = f"{job.title} {job.description} {' '.join(job.tags or [])}".lower()

    # Job title match — সর্বোচ্চ ৪০
    target_titles = [t.lower() for t in (profile.preferred_job_titles or [])]
    if not target_titles:
        target_titles = ["developer", "software engineer", "frontend", "full stack"]

    matched_words = {
        word
        for pt in target_titles
        for word in pt.split()
        if len(word) > 2 and word in title_lower
    }
    if matched_words:
        score += min(40.0, len(matched_words) * 15.0)
    elif any(c in title_lower for c in ("developer", "engineer", "programmer", "software")):
        score += 25.0

    # Skills match — সর্বোচ্চ ৩০
    user_skills = [s.lower() for s in (profile.skills or [])]
    if user_skills:
        matched = [
            s for s in user_skills
            if re.search(r"\b" + re.escape(s) + r"\b", job_text)
        ]
        ratio = len(matched) / min(len(user_skills), 10)
        score += min(30.0, ratio * 30.0)

    # Location / remote — সর্বোচ্চ ১০
    if profile.district and profile.district.lower() in (job.location or "").lower():
        score += 10.0
    elif job.is_remote and profile.open_to_remote:
        score += 10.0

    # নন-টেক পদের জন্য পেনাল্টি
    if any(p in title_lower for p in NON_TECH_PENALTY_KEYWORDS):
        score -= 40.0

    return int(max(10.0, min(score, 98.0)))


# ──────────────────────────────────────────────────────────
# ২. LLM ইভ্যালুয়েশন — fallback chain দিয়ে
# ──────────────────────────────────────────────────────────
def _build_match_prompt(profile: CVProfile, job: JobItem) -> str:
    return f"""Evaluate how well this candidate fits this job.

CANDIDATE
  Target roles : {', '.join(profile.preferred_job_titles or ['Software Developer'])}
  Skills       : {', '.join(profile.skills[:15])}
  Experience   : {profile.years_of_experience} years
  Summary      : {profile.summary or 'N/A'}
  Location     : {profile.district or 'Bangladesh'}

JOB
  Title    : {job.title}
  Company  : {job.company}
  Location : {job.location}
  Details  : {(job.description or '')[:700]}

SCORING RULES
  80-95 : title matches a target role and most key skills overlap
  60-79 : related role, partial skill overlap
  40-59 : same field but wrong level or stack
  10-39 : admin / data-entry / unrelated to software development

match_reason must be ONE short sentence naming the specific skills that
matched or the specific gap."""


async def evaluate_job_with_llm(profile: CVProfile, job: JobItem) -> dict:
    data = await complete_json(
        task="match_explain",
        system="You are a senior technical recruiter. Be strict and concrete.",
        user=_build_match_prompt(profile, job),
        schema=MATCH_SCHEMA,
    )

    if data and isinstance(data.get("match_score"), int):
        return {
            "match_score": max(0, min(100, data["match_score"])),
            "match_reason": (data.get("match_reason") or "").strip()
            or "Evaluated against candidate profile.",
        }

    # LLM না পেলে হিউরিস্টিকই থাকবে
    return {
        "match_score": calculate_base_heuristic_score(profile, job),
        "match_reason": (
            f"Skill overlap with {', '.join(profile.skills[:3])}."
            if profile.skills else "Heuristic title match."
        ),
    }


async def generate_cover_letter(profile: CVProfile, job: JobItem) -> str | None:
    """fail করলে None — ভুয়া টেমপ্লেট নয়। UI এটা হ্যান্ডেল করবে।"""
    prompt = f"""Write a concise, professional cover letter under 170 words.

CANDIDATE
  Name     : {profile.full_name}
  Email    : {profile.email or 'N/A'}
  Phone    : {profile.phone or 'N/A'}
  Skills   : {', '.join(profile.skills[:8])}
  Summary  : {profile.summary or 'N/A'}

APPLYING FOR
  {job.title} at {job.company} ({job.location})
  {(job.description or '')[:500]}

RULES
  - Open by naming the specific role and company.
  - Reference 2-3 concrete skills that match this job.
  - Never invent experience the candidate does not have.
  - Plain text. No placeholders like [Your Name]."""

    return await complete(
        task="cover_letter",
        system="You are an executive career coach writing tailored applications.",
        user=prompt,
        temperature=0.4,
        max_tokens=500,
    )


# ──────────────────────────────────────────────────────────
# ৩. পাইপলাইন — সমান্তরাল কল
# ──────────────────────────────────────────────────────────
async def process_matching_pipeline(
    profile: CVProfile,
    jobs: List[JobItem],
    top_k_cover_letters: int = 3,
) -> List[JobItem]:
    if not jobs:
        return []

    # স্তর ১ — সব জবে সস্তা হিউরিস্টিক
    for job in jobs:
        job.match_score = calculate_base_heuristic_score(profile, job)
        job.match_reason = "Initial match based on title and skills."

    jobs.sort(key=lambda j: j.match_score, reverse=True)

    # স্তর ২ — টপ ৫-এ LLM, একসাথে
    top = jobs[:12]
    evaluations = await asyncio.gather(
        *[evaluate_job_with_llm(profile, j) for j in top],
        return_exceptions=True,
    )
    for job, ev in zip(top, evaluations):
        if isinstance(ev, dict):
            job.match_score = ev["match_score"]
            job.match_reason = ev["match_reason"]

    # স্তর ৩ — ভালো ম্যাচগুলোর জন্য কভার লেটার, একসাথে
    targets = [j for j in top[:top_k_cover_letters] if j.match_score >= 60]
    if targets:
        letters = await asyncio.gather(
            *[generate_cover_letter(profile, j) for j in targets],
            return_exceptions=True,
        )
        for job, letter in zip(targets, letters):
            if isinstance(letter, str) and letter.strip():
                job.cover_letter = letter

    jobs.sort(key=lambda j: j.match_score, reverse=True)
    return jobs


# পুরনো নামের সাথে সামঞ্জস্য
match_and_score_jobs = process_matching_pipeline