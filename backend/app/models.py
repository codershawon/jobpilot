from typing import List, Optional
from pydantic import BaseModel, Field


class WorkExperience(BaseModel):
    title: str = ""
    company: str = ""
    duration: str = ""
    highlights: List[str] = Field(default_factory=list)


class Education(BaseModel):
    degree: str = ""
    institution: str = ""
    year: str = ""


class CVProfile(BaseModel):
    full_name: str = "Candidate"
    email: Optional[str] = None
    phone: Optional[str] = None
    location: Optional[str] = None
    district: Optional[str] = "Bangladesh"
    summary: Optional[str] = None
    skills: List[str] = Field(default_factory=list)
    years_of_experience: float = 0.0
    work_experience: List[WorkExperience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    preferred_job_titles: List[str] = Field(default_factory=list)
    preferred_locations: List[str] = Field(default_factory=list)
    open_to_remote: bool = True
    raw_text_char_count: int = 0


class CVParseResponse(BaseModel):
    profile: CVProfile
    source_filename: str
    warnings: List[str] = Field(default_factory=list)


class JobItem(BaseModel):
    id: str
    title: str
    company: str
    location: str
    district: str = "All Bangladesh"
    is_remote: bool = False
    job_type: str = "Local"  # "Local", "Worldwide", "Gov"
    source: str              # "Bdjobs", "RemoteOK", "Arbeitnow"
    url: str
    description: str
    salary: Optional[str] = "Negotiable / Not Disclosed"
    tags: List[str] = Field(default_factory=list)
    posted_date: Optional[str] = None
    match_score: int = 0
    match_reason: Optional[str] = None
    cover_letter: Optional[str] = None
    status: str = "SAVED"    # "SAVED", "APPLIED", "ARCHIVED"


class JobSearchQuery(BaseModel):
    keywords: List[str] = Field(default_factory=lambda: ["Web Developer", "Frontend Developer", "React"])
    districts: List[str] = Field(default_factory=lambda: ["Cumilla", "Dhaka", "Chattogram"])
    include_remote: bool = True
    include_gov: bool = True
    limit_per_source: int = 10


class JobSearchResponse(BaseModel):
    total_found: int
    jobs: List[JobItem]


class JobMatchRequest(BaseModel):
    profile: CVProfile
    jobs: List[JobItem]
    generate_cover_letters_for_top: int = 3


class JobMatchResponse(BaseModel):
    matched_jobs: List[JobItem]


class FullPipelineResponse(BaseModel):
    profile: CVProfile
    total_found: int
    matched_jobs: List[JobItem]