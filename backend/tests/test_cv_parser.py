import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app import cv_parser  # noqa: E402
from tests.make_sample_docx import build as build_sample_docx  # noqa: E402

SAMPLE_DOCX = Path(__file__).resolve().parent.parent / "sample_cvs" / "sample_cv.docx"


def setup_module():
    build_sample_docx()


def test_extract_text_from_docx_contains_key_facts():
    text = cv_parser.extract_text_from_docx(SAMPLE_DOCX)
    assert "Farhan Ahmed" in text
    assert "FastAPI" in text
    assert "BUET" in text


def test_parse_cv_maps_llm_json_into_profile(monkeypatch):
    fake_llm_response = {
        "full_name": "Farhan Ahmed",
        "email": "farhan.ahmed@example.com",
        "phone": "+880 1XXXXXXXXX",
        "location": "Dhaka, Bangladesh",
        "summary": "Backend engineer with 4 years of experience in Python and Node.js.",
        "skills": ["Python", "FastAPI", "Django", "Node.js", "PostgreSQL", "Docker", "AWS"],
        "years_of_experience": 4,
        "work_experience": [
            {
                "title": "Backend Engineer",
                "company": "Pathao",
                "duration": "Jan 2022 - Present",
                "highlights": ["Built ride-matching microservices"],
            }
        ],
        "education": [{"degree": "B.Sc. CSE", "institution": "BUET", "year": "2020"}],
        "preferred_job_titles": ["Backend Engineer", "Software Engineer"],
        "preferred_locations": ["Dhaka"],
        "open_to_remote": True,
    }

    monkeypatch.setattr(cv_parser, "chat_json", lambda *a, **k: dict(fake_llm_response))

    result = cv_parser.parse_cv(SAMPLE_DOCX, original_filename="sample_cv.docx")

    assert result.source_filename == "sample_cv.docx"
    assert result.profile.full_name == "Farhan Ahmed"
    assert "FastAPI" in result.profile.skills
    assert result.profile.open_to_remote is True
    assert result.profile.raw_text_char_count > 0
