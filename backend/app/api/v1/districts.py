from fastapi import APIRouter
from app.services.district_service import get_all_districts

router = APIRouter(prefix="/districts", tags=["Districts"])

@router.get("")
async def fetch_districts():
    districts = await get_all_districts()
    return {"total": len(districts), "districts": districts}

@router.get("/external-links")
def get_external_job_links(keyword: str = "React Developer", location: str = "Bangladesh"):
    return {
        "linkedin_search": f"https://www.linkedin.com/jobs/search/?keywords={keyword}&location={location}",
        "indeed_search": f"https://bd.indeed.com/jobs?q={keyword}&l={location}",
        "glassdoor_search": f"https://www.glassdoor.com/Job/jobs.htm?sc.keyword={keyword}&locT=C&locId=1",
        "facebook_jobs_search": f"https://www.facebook.com/search/posts/?q={keyword}%20job%20{location}"
    }