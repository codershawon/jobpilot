p = "app/api/v1/applications.py"
src = open(p, encoding="utf-8").read()

old_create = '''class ApplicationCreate(BaseModel):
    job_id: str = Field(..., max_length=32)
    status: str = "APPLIED"
    notes: str = ""
    tracking_id: Optional[str] = None'''

new_create = '''class ApplicationCreate(BaseModel):
    job_id: str = Field(..., max_length=32)
    status: str = "APPLIED"
    notes: str = ""
    tracking_id: Optional[str] = None

    # জব ডাটাবেসে না থাকলে এগুলো থেকে সারি বানানো হবে
    title: Optional[str] = None
    company: Optional[str] = None
    url: Optional[str] = None
    source: Optional[str] = None
    district: Optional[str] = None
    deadline: Optional[date] = None'''

old_job = '''    if not job:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "জব পাওয়া যায়নি")'''

new_job = '''    # ডাটাবেসে না থাকলে ফ্রন্টএন্ডের পাঠানো তথ্য দিয়ে সারি বানাই
    if not job:
        if not payload.title:
            raise HTTPException(
                status.HTTP_404_NOT_FOUND,
                "জব পাওয়া যায়নি — Sync Jobs চেপে আবার চেষ্টা করুন",
            )
        job = Job(
            id=payload.job_id,
            title=payload.title[:512],
            company=(payload.company or "")[:512],
            url=payload.url or "",
            source=(payload.source or "manual")[:64],
            district=(payload.district or "")[:128],
            deadline=payload.deadline,
            sectors=["private"],
            job_function="general",
            is_active=True,
        )
        db.add(job)
        await db.flush()'''

ok1 = old_create in src
ok2 = old_job in src

if ok1:
    src = src.replace(old_create, new_create)
if ok2:
    src = src.replace(old_job, new_job)

if ok1 and ok2:
    open(p, "w", encoding="utf-8").write(src)
    print("✅ দুইটা ফিক্সই বসেছে")
else:
    print("⚠ পাওয়া যায়নি — ApplicationCreate:", ok1, "| job চেক:", ok2)