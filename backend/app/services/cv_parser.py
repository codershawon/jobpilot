"""CV file -> raw text -> structured profile."""

import io
from typing import List, Tuple

import docx
from pypdf import PdfReader

from app.models import CVParseResponse, CVProfile
from app.services.llm.cv import extract_profile


def extract_text_from_pdf(pdf_bytes: bytes) -> str:
    reader = PdfReader(io.BytesIO(pdf_bytes))
    chunks: List[str] = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            chunks.append(text)
    return "\n".join(chunks)


def extract_text_from_docx(docx_bytes: bytes) -> str:
    doc = docx.Document(io.BytesIO(docx_bytes))
    return "\n".join(p.text for p in doc.paragraphs if p.text)


def extract_raw_text(file_bytes: bytes, filename: str) -> Tuple[str, List[str]]:
    warnings: List[str] = []
    lower = filename.lower()

    if lower.endswith(".pdf"):
        raw = extract_text_from_pdf(file_bytes)
    elif lower.endswith(".docx"):
        raw = extract_text_from_docx(file_bytes)
    else:
        raise ValueError("Unsupported format. Only .pdf and .docx are supported.")

    if not raw.strip():
        warnings.append("Could not extract text from document.")

    return raw.strip(), warnings


async def parse_cv(file_bytes: bytes, filename: str) -> CVParseResponse:
    raw_text, warnings = extract_raw_text(file_bytes, filename)

    if not raw_text:
        return CVParseResponse(
            profile=CVProfile(full_name="Unknown"),
            source_filename=filename,
            warnings=["Document is empty or text could not be read."],
        )

    profile = await extract_profile(raw_text)
    profile.raw_text_char_count = len(raw_text)

    return CVParseResponse(
        profile=profile,
        source_filename=filename,
        warnings=warnings,
    )
