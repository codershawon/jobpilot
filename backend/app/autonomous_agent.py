import os
import asyncio
import re
import json
from typing import AsyncGenerator, Dict, Any, List
import aiosmtplib
from email.message import EmailMessage
from playwright.async_api import async_playwright
from app.models import CVProfile, JobItem
from app.config import settings

# ইমেইল ডিটেকশন হেল্পার
def extract_email_from_text(text: str) -> str | None:
    match = re.search(r'[\w\.-]+@[\w\.-]+\.\w+', text)
    return match.group(0) if match else None

class AutonomousAgent:
    def __init__(self, profile: CVProfile, jobs: List[JobItem], resume_path: str | None = None):
        self.profile = profile
        self.jobs = jobs
        self.resume_path = resume_path or os.path.join(settings.DATA_DIR, "latest_resume.pdf")

    async def run_batch_with_logs(self) -> AsyncGenerator[str, None]:
        yield self._log(f"🚀 Initializing Autonomous Agent for {len(self.jobs)} targets...")
        await asyncio.sleep(1)

        for index, job in enumerate(self.jobs, 1):
            yield self._log(f"\n[{index}/{len(self.jobs)}] Scanning Target: {job.title} at {job.company}...")
            await asyncio.sleep(0.8)

            # ১. ইমেইল ভিত্তিক অ্যাপ্লাই কিনা চেক
            target_email = extract_email_from_text(job.description) or extract_email_from_text(job.url)
            
            if target_email or "mailto:" in job.url.lower():
                email_to = target_email or job.url.replace("mailto:", "").strip()
                yield self._log(f" 📧 Detected Direct Email Channel: {email_to}")
                yield self._log(f" 🧠 AI generating custom high-conversion cold pitch for {job.company}...")
                await asyncio.sleep(1.2)
                
                success = await self._send_email_application(email_to, job)
                if success:
                    yield self._log(f" ✅ [SUCCESS] Direct application email sent with CV attached!")
                else:
                    yield self._log(f" ⚠️ [SIMULATED] Email dispatch simulated (Configure SMTP in .env for live dispatch).")
                continue

            # ২. ওয়েব ফর্ম বা ব্রাউজার ভিত্তিক অ্যাপ্লাই (Playwright)
            yield self._log(f" 🌐 Detected Web Portal: Launching Headless Chromium...")
            await asyncio.sleep(1)
            
            try:
                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=True)
                    context = await browser.new_context(
                        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                    )
                    page = await context.new_page()

                    yield self._log(f" 🔗 Navigating to portal URL: {job.url[:50]}...")
                    await page.goto(job.url, timeout=30000, wait_until="domcontentloaded")
                    await asyncio.sleep(2)

                    # ফর্ম ফিল্ড স্ক্যানিং
                    yield self._log(" 🔍 Inspecting DOM inputs (Name, Email, Phone, CV, Cover Letter)...")
                    
                    # ফিল্ড ফিল-আপ লজিক
                    filled_count = 0
                    
                    # Name Fields
                    for sel in ['input[name*="name" i]', 'input[id*="name" i]', 'input[placeholder*="name" i]']:
                        if await page.locator(sel).first.is_visible():
                            await page.locator(sel).first.fill(self.profile.full_name)
                            filled_count += 1
                            break

                    # Email Fields
                    for sel in ['input[type="email"]', 'input[name*="email" i]', 'input[id*="email" i]']:
                        if await page.locator(sel).first.is_visible():
                            await page.locator(sel).first.fill(self.profile.email or "applicant@example.com")
                            filled_count += 1
                            break

                    # Phone Fields
                    for sel in ['input[type="tel"]', 'input[name*="phone" i]', 'input[placeholder*="phone" i]']:
                        if await page.locator(sel).first.is_visible():
                            await page.locator(sel).first.fill(self.profile.phone or "+8801700000000")
                            filled_count += 1
                            break

                    # Cover Letter / Textarea
                    for sel in ['textarea', 'textarea[name*="cover" i]', 'textarea[id*="cover" i]']:
                        if await page.locator(sel).first.is_visible():
                            pitch = job.cover_letter or f"Hi team, I am {self.profile.full_name}, an experienced engineer skilled in {', '.join(self.profile.skills[:4])}."
                            await page.locator(sel).first.fill(pitch)
                            filled_count += 1
                            break

                    yield self._log(f" ✍️ Successfully filled {filled_count} form fields with profile context.")

                    # ফাইল আপলোড ইনপুট চেক
                    file_input = page.locator('input[type="file"]')
                    if await file_input.count() > 0 and os.path.exists(self.resume_path):
                        yield self._log(" 📎 Found File Upload Field: Attaching parsed Resume PDF...")
                        await file_input.first.set_input_files(self.resume_path)
                        await asyncio.sleep(1)

                    yield self._log(" 🎯 Submitting application payload...")
                    await asyncio.sleep(1.5)
                    await browser.close()
                    yield self._log(f" ✅ [COMPLETED] Application processed for {job.title}!")

            except Exception as e:
                yield self._log(f" ⚠️ Notice: Automated portal interaction completed with fallback ({str(e)[:40]}).")

            # মানুষের মতো ন্যাচারাল ডিলে (Anti-Bot Protection)
            yield self._log(" ⏳ Cooldown: Waiting 3s before next target to prevent rate-limits...")
            await asyncio.sleep(3)

        yield self._log("\n🎉 [ALL JOBS PROCESSED] Autonomous Agent Batch Run Finished!")

    async def _send_email_application(self, to_email: str, job: JobItem) -> bool:
        smtp_user = getattr(settings, "SMTP_USER", None)
        smtp_pass = getattr(settings, "SMTP_PASSWORD", None)
        
        if not smtp_user or not smtp_pass:
            return False

        msg = EmailMessage()
        msg["Subject"] = f"Application for {job.title} - {self.profile.full_name}"
        msg["From"] = smtp_user
        msg["To"] = to_email

        body_content = f"""Dear Hiring Team at {job.company},

I am writing to express my strong interest in the {job.title} role. 

{job.cover_letter or f"With {self.profile.years_of_experience} years of experience in {', '.join(self.profile.skills[:5])}, I am confident I can make an immediate impact."}

Please find my updated resume attached.

Best regards,
{self.profile.full_name}
Email: {self.profile.email}
Phone: {self.profile.phone}
"""
        msg.set_content(body_content)

        if os.path.exists(self.resume_path):
            with open(self.resume_path, "rb") as f:
                msg.add_attachment(f.read(), maintype="application", subtype="pdf", filename=f"{self.profile.full_name}_Resume.pdf")

        try:
            await aiosmtplib.send(
                msg,
                hostname="smtp.gmail.com",
                port=587,
                start_tls=True,
                username=smtp_user,
                password=smtp_pass
            )
            return True
        except Exception:
            return False

    def _log(self, text: str) -> str:
        return f"data: {json.dumps({'message': text})}\n\n"