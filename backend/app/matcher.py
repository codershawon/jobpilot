import json
import re
from typing import List
from app.models import CVProfile, JobItem
from app.llm_client import get_client
from app.config import settings


def calculate_base_heuristic_score(profile: CVProfile, job: JobItem) -> int:
    score = 40
    user_skills = [s.lower() for s in profile.skills]
    job_text = f"{job.title} {job.description} {' '.join(job.tags)}".lower()

    matched_skills = [s for s in user_skills if s in job_text]
    score += min(len(matched_skills) * 10, 40)

    if profile.district and profile.district.lower() in job.location.lower():
        score += 15
    elif job.is_remote and profile.open_to_remote:
        score += 10

    return min(score, 98)


async def evaluate_job_with_llm(profile: CVProfile, job: JobItem) -> dict:
    client = get_client()
    model_name = settings.active_model_name

    prompt = f"""Compare Candidate Profile with the Job Listing and provide precise match reasoning.
Candidate Skills: {', '.join(profile.skills)}
Candidate Summary: {profile.summary}
Candidate Preferred Location: {profile.district}, Bangladesh

Job Title: {job.title}
Company: {job.company}
Location: {job.location}
Description: {job.description[:700]}

Return STRICT JSON format:
{{
  "match_score": 85,
  "match_reason": "One concise sentence why this role fits the candidate's technical skills."
}}"""

    try:
        res = await client.chat.completions.create(
            model=model_name,
            temperature=0.1,
            messages=[
                {"role": "system", "content": "You are a senior tech recruiter evaluating candidate fit. Return only JSON."},
                {"role": "user", "content": prompt}
            ]
        )
        content = res.choices[0].message.content or "{}"
        clean_json = re.sub(r"^```json\s*|\s*```$", "", content.strip())
        return json.loads(clean_json)
    except Exception as e:
        print(f"[Matcher LLM Error]: {e}")
        return {
            "match_score": calculate_base_heuristic_score(profile, job),
            "match_reason": f"Strong alignment with candidate skills ({', '.join(profile.skills[:3])})."
        }


async def generate_cover_letter(profile: CVProfile, job: JobItem) -> str:
    client = get_client()
    model_name = settings.active_model_name

    prompt = f"""Write a concise, high-converting, professional application message/cover letter (under 180 words).
Candidate Name: {profile.full_name}
Email: {profile.email} | Phone: {profile.phone}
Key Skills: {', '.join(profile.skills[:6])}
Experience Highlights: {profile.summary}

Applying For: {job.title} at {job.company} ({job.location})"""

    try:
        res = await client.chat.completions.create(
            model=model_name,
            temperature=0.3,
            messages=[
                {"role": "system", "content": "You are an executive career coach crafting tailor-made job applications."},
                {"role": "user", "content": prompt}
            ]
        )
        return (res.choices[0].message.content or "").strip()
    except Exception as e:
        return f"Dear Hiring Team at {job.company},\n\nI am excited to apply for the {job.title} position..."


async def process_matching_pipeline(profile: CVProfile, jobs: List[JobItem], top_k_cover_letters: int = 3) -> List[JobItem]:
    for j in jobs:
        j.match_score = calculate_base_heuristic_score(profile, j)
        j.match_reason = f"Relevant match based on {', '.join(profile.skills[:3])}."

    jobs.sort(key=lambda x: x.match_score, reverse=True)

    for i in range(min(5, len(jobs))):
        deep_eval = await evaluate_job_with_llm(profile, jobs[i])
        jobs[i].match_score = deep_eval.get("match_score", jobs[i].match_score)
        jobs[i].match_reason = deep_eval.get("match_reason", jobs[i].match_reason)

        if i < top_k_cover_letters and jobs[i].match_score >= 60:
            jobs[i].cover_letter = await generate_cover_letter(profile, jobs[i])

    jobs.sort(key=lambda x: x.match_score, reverse=True)
    return jobs

# Alias for full compatibility
match_and_score_jobs = process_matching_pipeline